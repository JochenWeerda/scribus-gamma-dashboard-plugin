from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from .progress_tracker import ProgressTracker
from .resume_manager import ResumeManager, hash_file, hash_inputs
from .step_executor import StepExecutor
from .error_handler import run_with_retries, RetryPolicy


@dataclass(frozen=True)
class WorkflowConfig:
    manifest_path: Path
    pptx_root: Path = Path("media_pool/pptx")
    layout_out: Path = Path("media_pool/layout_json")
    variants_out: Path = Path("media_pool/layout_json_variants")
    project_init: Optional[Path] = None
    resume_path: Path = Path("temp_analysis/workflow_state.json")
    generate_variants: bool = True
    gamma_png_dir: Optional[Path] = None
    gamma_crops_out: Path = Path("media_pool/gamma_crops")
    gamma_sync: bool = False
    gamma_crop_kinds: Tuple[str, ...] = ("infobox", "image_box")
    gamma_attach_to_variants: bool = False
    gamma_attach_kinds: Tuple[str, ...] = ("image_box",)
    quality_check: bool = False
    quality_on_variants: bool = True
    quality_out: Path = Path("media_pool/quality")
    quality_checks: Tuple[str, ...] = ("preflight", "amazon")
    render: bool = False
    render_on_variants: bool = True
    render_out: Path = Path("media_pool/render")
    render_pdf: bool = True
    render_png: bool = True
    agents_enabled: bool = False
    agent_steps: Tuple[str, ...] = ("SemanticEnricher", "LayoutDesigner", "QualityCritic")
    agent_seed: Optional[int] = None
    agent_version: str = "v1"
    agent_simulate: bool = False
    force: bool = False
    retry_max: int = 1


class WorkflowOrchestrator:
    """
    MVP workflow runner:
    - convert extracted PPTX JSON -> layout_json files
    Future: create jobs, variants, quality checks, UI integration.
    """

    def __init__(self, config: WorkflowConfig, *, tracker: Optional[ProgressTracker] = None):
        self.config = config
        self.tracker = tracker or ProgressTracker(publish_to_bus=True)
        self.resume = ResumeManager(self.config.resume_path)
        self.exec = StepExecutor(tracker=self.tracker)

    def _step_should_skip(self, state: dict, step_id: str, input_hash: str) -> bool:
        if self.config.force:
            return False
        step = self.resume.get_step(state, step_id)
        if step.get("status") != "completed":
            return False
        if step.get("input_hash") != input_hash:
            return False
        outputs = step.get("outputs")
        if not outputs:
            return True
        # If outputs are file paths, ensure they still exist.
        try:
            return all(Path(p).exists() for p in outputs)
        except Exception:
            return True

    def _run_step(self, *, state: dict, step_id: str, input_hash: str, fn, on_success):
        if self._step_should_skip(state, step_id, input_hash):
            self.tracker.emit("step.skipped", step_id=step_id)
            return

        self.resume.mark_step_running(state, step_id, input_hash=input_hash)
        self.resume.save(state)
        self.tracker.emit("step.started", step_id=step_id)

        try:
            result = run_with_retries(fn, policy=RetryPolicy(max_retries=int(self.config.retry_max)))
            on_success(result)
            self.resume.mark_step_completed(state, step_id, outputs=on_success.outputs if hasattr(on_success, "outputs") else None, summary=on_success.summary if hasattr(on_success, "summary") else None)  # type: ignore[attr-defined]
            self.resume.save(state)
            self.tracker.emit("step.completed", step_id=step_id)
        except Exception as exc:
            self.resume.mark_step_failed(state, step_id, error=str(exc))
            self.resume.save(state)
            self.tracker.emit("step.failed", step_id=step_id, error=str(exc))
            raise

    def run(self) -> None:
        state = self.resume.load()
        self.tracker.emit("workflow.start", state=state)

        # Step 1: convert_manifest
        manifest_hash = hash_file(self.config.manifest_path)
        project_init_hash = hash_file(self.config.project_init) if (self.config.project_init and Path(self.config.project_init).exists()) else None
        convert_input_hash = hash_inputs(
            {
                "step": "convert_manifest",
                "manifest": str(self.config.manifest_path),
                "manifest_hash": manifest_hash,
                "pptx_root": str(self.config.pptx_root),
                "layout_out": str(self.config.layout_out),
                "project_init_hash": project_init_hash,
            }
        )

        convert_result_holder = {}

        def _do_convert():
            return self.exec.convert_manifest(
                manifest_path=self.config.manifest_path,
                pptx_root=self.config.pptx_root,
                out_dir=self.config.layout_out,
                project_init=self.config.project_init,
            )

        def _convert_success(res):
            convert_result_holder["res"] = res
            outputs = [str(p) for p in res.outputs]
            _convert_success.outputs = outputs  # type: ignore[attr-defined]
            _convert_success.summary = {"valid": res.valid_count, "invalid": len(res.invalid)}  # type: ignore[attr-defined]
            # keep compatibility top-level state fields (legacy readers)
            state["converted"] = {"outputs": outputs, "valid": res.valid_count}

        self._run_step(state=state, step_id="convert_manifest", input_hash=convert_input_hash, fn=_do_convert, on_success=_convert_success)
        self.resume.save(state)

        gamma_result_holder = {}
        gamma_input_hash: Optional[str] = None

        if self.config.gamma_attach_to_variants and (not self.config.gamma_sync or not self.config.gamma_png_dir):
            raise ValueError("gamma_attach_to_variants requires gamma_sync=True and gamma_png_dir to be set")

        if self.config.gamma_sync and self.config.gamma_png_dir:
            # Step 2: gamma_sync (crop artifacts)
            extracted_manifest_path = self.config.manifest_path
            extracted_root = self.config.pptx_root
            gamma_dir = Path(self.config.gamma_png_dir)

            gamma_input_hash = hash_inputs(
                {
                    "step": "gamma_sync",
                    "manifest_hash": manifest_hash,
                    "gamma_dir": str(gamma_dir),
                    "crops_out": str(self.config.gamma_crops_out),
                    "crop_kinds": list(self.config.gamma_crop_kinds),
                    "pad_px": 10,
                    "refine": True,
                    "refine_margin_px": 40,
                    "bg_threshold": 245,
                }
            )

            def _do_gamma():
                return self.exec.gamma_sync(
                    extracted_manifest_path=extracted_manifest_path,
                    extracted_root=extracted_root,
                    gamma_png_dir=gamma_dir,
                    out_dir=self.config.gamma_crops_out,
                    crop_kinds=list(self.config.gamma_crop_kinds),
                    crop_pad_px=10,
                    crop_refine=True,
                    crop_refine_margin_px=40,
                    crop_bg_threshold=245,
                )

            def _gamma_success(gres):
                gamma_result_holder["res"] = gres
                _gamma_success.outputs = [o.get("out") for o in (gres.get("outputs") or []) if o.get("out")]  # type: ignore[attr-defined]
                _gamma_success.summary = {"outputs": len(gres.get("outputs") or []), "errors": len(gres.get("errors") or [])}  # type: ignore[attr-defined]
                state["gamma_sync"] = gres

            self._run_step(state=state, step_id="gamma_sync", input_hash=gamma_input_hash, fn=_do_gamma, on_success=_gamma_success)
            self.resume.save(state)

        if self.config.generate_variants:
            # Step 3: generate_variants
            res = convert_result_holder.get("res")
            if res is None:
                # If we skipped convert step, recover outputs from state
                prev = self.resume.get_step(state, "convert_manifest")
                outputs = prev.get("outputs") or state.get("converted", {}).get("outputs") or []
                layout_paths = [Path(p) for p in outputs]
            else:
                layout_paths = list(res.outputs)

            # hash all layout inputs deterministically
            layout_hashes = []
            for p in layout_paths:
                try:
                    layout_hashes.append({"path": str(p), "hash": hash_file(Path(p))})
                except Exception:
                    layout_hashes.append({"path": str(p), "hash": None})

            variants_input_hash = hash_inputs(
                {
                    "step": "generate_variants",
                    "layouts": layout_hashes,
                    "variants_out": str(self.config.variants_out),
                    "project_init_hash": project_init_hash,
                    "gamma_attach_to_variants": bool(self.config.gamma_attach_to_variants),
                    "gamma_attach_kinds": list(self.config.gamma_attach_kinds),
                    "gamma_sync_input_hash": gamma_input_hash,
                }
            )

            def _do_variants():
                gamma_report = None
                if self.config.gamma_attach_to_variants:
                    gamma_report = gamma_result_holder.get("res") or state.get("gamma_sync")
                    if not isinstance(gamma_report, dict):
                        raise RuntimeError("gamma_attach_to_variants enabled but no gamma_sync report available")
                return self.exec.generate_variants(
                    layout_paths=layout_paths,
                    out_dir=self.config.variants_out,
                    project_init=self.config.project_init,
                    attach_gamma_crops=bool(self.config.gamma_attach_to_variants),
                    gamma_report=gamma_report,
                    gamma_attach_kinds=list(self.config.gamma_attach_kinds),
                )

            def _variants_success(vres):
                _variants_success.outputs = [o.get("out") for o in (vres.get("outputs") or []) if o.get("out")]  # type: ignore[attr-defined]
                _variants_success.summary = {"outputs": len(vres.get("outputs") or []), "errors": len(vres.get("errors") or [])}  # type: ignore[attr-defined]
                state["variants"] = vres

            self._run_step(state=state, step_id="generate_variants", input_hash=variants_input_hash, fn=_do_variants, on_success=_variants_success)
            self.resume.save(state)

        if self.config.agents_enabled:
            # Step 3.5: agents (heuristic black boxes)
            res = convert_result_holder.get("res")
            if res is None:
                prev = self.resume.get_step(state, "convert_manifest")
                outputs = prev.get("outputs") or state.get("converted", {}).get("outputs") or []
                layout_paths = [Path(p) for p in outputs]
            else:
                layout_paths = list(res.outputs)

            layout_hashes = []
            for p in layout_paths:
                try:
                    layout_hashes.append({"path": str(p), "hash": hash_file(Path(p))})
                except Exception:
                    layout_hashes.append({"path": str(p), "hash": None})

            agents_input_hash = hash_inputs(
                {
                    "step": "agents",
                    "layouts": layout_hashes,
                    "agent_steps": list(self.config.agent_steps),
                    "agent_seed": self.config.agent_seed,
                    "agent_version": self.config.agent_version,
                    "simulate": bool(self.config.agent_simulate),
                    "project_init_hash": project_init_hash,
                }
            )

            def _do_agents():
                return self.exec.run_agents(
                    layout_paths=layout_paths,
                    project_init=self.config.project_init,
                    agent_ids=list(self.config.agent_steps),
                    seed=self.config.agent_seed,
                    version=self.config.agent_version,
                    simulate=self.config.agent_simulate,
                )

            def _agents_success(ares):
                _agents_success.outputs = [o.get("path") for o in (ares.get("outputs") or []) if o.get("path")]  # type: ignore[attr-defined]
                _agents_success.summary = {"outputs": len(ares.get("outputs") or []), "errors": len(ares.get("errors") or [])}  # type: ignore[attr-defined]
                state["agents"] = ares

            self._run_step(state=state, step_id="agents", input_hash=agents_input_hash, fn=_do_agents, on_success=_agents_success)
            self.resume.save(state)

        if self.config.quality_check:
            # Step 4: quality_check
            quality_paths: list[Path] = []

            if self.config.generate_variants and self.config.quality_on_variants:
                vres = state.get("variants") or {}
                outs = vres.get("outputs") or []
                for o in outs:
                    try:
                        op = o.get("out")
                        if op:
                            quality_paths.append(Path(op))
                    except Exception:
                        continue
            else:
                res = convert_result_holder.get("res")
                if res is None:
                    prev = self.resume.get_step(state, "convert_manifest")
                    outputs = prev.get("outputs") or state.get("converted", {}).get("outputs") or []
                    quality_paths = [Path(p) for p in outputs]
                else:
                    quality_paths = list(res.outputs)

            q_hashes = []
            for p in quality_paths:
                try:
                    q_hashes.append({"path": str(p), "hash": hash_file(Path(p))})
                except Exception:
                    q_hashes.append({"path": str(p), "hash": None})

            quality_input_hash = hash_inputs(
                {
                    "step": "quality_check",
                    "paths": q_hashes,
                    "quality_out": str(self.config.quality_out),
                    "quality_checks": list(self.config.quality_checks),
                    "quality_on_variants": bool(self.config.quality_on_variants),
                }
            )

            def _do_quality():
                return self.exec.quality_check(
                    layout_paths=quality_paths,
                    out_dir=self.config.quality_out,
                    checks=list(self.config.quality_checks),
                    project_init=self.config.project_init,
                )

            def _quality_success(qres):
                _quality_success.outputs = [qres.get("report_path")] if qres.get("report_path") else []  # type: ignore[attr-defined]
                _quality_success.summary = {"outputs": len(qres.get("outputs") or []), "errors": len(qres.get("errors") or [])}  # type: ignore[attr-defined]
                state["quality"] = qres

            self._run_step(state=state, step_id="quality_check", input_hash=quality_input_hash, fn=_do_quality, on_success=_quality_success)
            self.resume.save(state)

        if self.config.render:
            # Step 5: render (SLA + PDF/PNG)
            render_paths: list[Path] = []
            if self.config.generate_variants and self.config.render_on_variants:
                vres = state.get("variants") or {}
                outs = vres.get("outputs") or []
                for o in outs:
                    try:
                        op = o.get("out")
                        if op:
                            render_paths.append(Path(op))
                    except Exception:
                        continue
            else:
                res = convert_result_holder.get("res")
                if res is None:
                    prev = self.resume.get_step(state, "convert_manifest")
                    outputs = prev.get("outputs") or state.get("converted", {}).get("outputs") or []
                    render_paths = [Path(p) for p in outputs]
                else:
                    render_paths = list(res.outputs)

            r_hashes = []
            for p in render_paths:
                try:
                    r_hashes.append({"path": str(p), "hash": hash_file(Path(p))})
                except Exception:
                    r_hashes.append({"path": str(p), "hash": None})

            render_input_hash = hash_inputs(
                {
                    "step": "render",
                    "layouts": r_hashes,
                    "render_out": str(self.config.render_out),
                    "render_pdf": bool(self.config.render_pdf),
                    "render_png": bool(self.config.render_png),
                    "project_init_hash": project_init_hash,
                }
            )

            def _do_render():
                return self.exec.render(
                    layout_paths=render_paths,
                    out_dir=self.config.render_out,
                    project_init=self.config.project_init,
                    render_pdf=bool(self.config.render_pdf),
                    render_png=bool(self.config.render_png),
                )

            def _render_success(rres):
                _render_success.outputs = [o.get("path") for o in (rres.get("outputs") or []) if o.get("path")]  # type: ignore[attr-defined]
                _render_success.summary = {"outputs": len(rres.get("outputs") or []), "errors": len(rres.get("errors") or [])}  # type: ignore[attr-defined]
                state["render"] = rres

            self._run_step(state=state, step_id="render", input_hash=render_input_hash, fn=_do_render, on_success=_render_success)
            self.resume.save(state)

        self.tracker.emit("workflow.done", state=state)
