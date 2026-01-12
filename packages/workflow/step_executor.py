from __future__ import annotations

import inspect
import logging
import traceback
from dataclasses import dataclass, field
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .progress_tracker import ProgressTracker
from .resume_manager import ResumeManager, hash_inputs


@dataclass
class StepExecutor:
    tracker: ProgressTracker = field(default_factory=ProgressTracker)

    def render(
        self,
        *,
        layout_paths: List[Path],
        out_dir: Path,
        project_init: Optional[Path] = None,
        render_pdf: bool = True,
        render_png: bool = True,
        report_name: str = "render_report.json",
    ) -> Dict[str, Any]:
        """
        Render step (MVP): Layout JSON -> SLA + placeholder PDF/PNG.

        This makes the render/export step explicit in the workflow graph.
        Production Scribus export can later replace the placeholder generator.
        """

        from packages.sla_compiler import compile_layout_to_sla

        init: Dict[str, Any] = {}
        if project_init and Path(project_init).exists():
            try:
                init = json.loads(Path(project_init).read_text(encoding="utf-8"))
            except Exception:
                init = {}

        out_dir.mkdir(parents=True, exist_ok=True)
        sla_dir = out_dir / "sla"
        pdf_dir = out_dir / "pdf"
        png_dir = out_dir / "png"
        sla_dir.mkdir(parents=True, exist_ok=True)
        if render_pdf:
            pdf_dir.mkdir(parents=True, exist_ok=True)
        if render_png:
            png_dir.mkdir(parents=True, exist_ok=True)

        report: Dict[str, Any] = {"outputs": [], "errors": []}
        self.tracker.emit("render.start", inputs=len(layout_paths), out_dir=str(out_dir))

        for lp in layout_paths:
            try:
                layout = json.loads(Path(lp).read_text(encoding="utf-8"))
            except Exception as exc:
                report["errors"].append({"path": str(lp), "error": f"failed to read json: {exc}"})
                continue

            base_name = Path(lp).stem
            # If this is our "chapter_XX_name.layout.json" format, keep that stable.
            safe_name = re.sub(r"[^A-Za-z0-9_.\\-]+", "_", base_name).strip("_") or "layout"

            try:
                sla_bytes = compile_layout_to_sla(layout)
                sla_path = sla_dir / f"{safe_name}.sla"
                sla_path.write_bytes(sla_bytes)
            except Exception as exc:
                report["errors"].append({"path": str(lp), "error": f"failed to compile sla: {exc}"})
                continue

            pdf_path = None
            if render_pdf:
                pdf_path = pdf_dir / f"{safe_name}.pdf"
                try:
                    pdf_path.write_bytes(_minimal_pdf_bytes(f"Placeholder PDF for {safe_name}"))
                except Exception as exc:
                    report["errors"].append({"path": str(lp), "error": f"failed to write pdf: {exc}"})
                    pdf_path = None

            png_path = None
            if render_png:
                png_path = png_dir / f"{safe_name}_p0001.png"
                try:
                    png_path.write_bytes(_minimal_png_1x1())
                except Exception as exc:
                    report["errors"].append({"path": str(lp), "error": f"failed to write png: {exc}"})
                    png_path = None

            report["outputs"].append(
                {
                    "input": str(lp),
                    "sla": str(sla_path),
                    "pdf": str(pdf_path) if pdf_path else None,
                    "png": str(png_path) if png_path else None,
                    "path": str(sla_path),
                    "render_mode": "placeholder",
                }
            )

        report_path = out_dir / report_name
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        report["report_path"] = str(report_path)

        self.tracker.emit("render.done", outputs=len(report["outputs"]), errors=len(report["errors"]), report=str(report_path))
        return report

    def convert_manifest(self, *, manifest_path: Path, pptx_root: Path, out_dir: Path, project_init: Optional[Path] = None):
        from packages.pptx_parser.manifest_converter import convert_manifest_to_layout_jsons
        from packages.pptx_parser.style_presets import apply_style_preset
        from packages.pptx_parser.json_converter import PptxExtractConvertConfig

        cfg = apply_style_preset(PptxExtractConvertConfig(), "magazin")
        self.tracker.emit("convert.start", manifest=str(manifest_path))
        result = convert_manifest_to_layout_jsons(
            manifest_path=manifest_path,
            pptx_root_dir=pptx_root,
            out_dir=out_dir,
            config=cfg,
            project_init_path=str(project_init) if project_init else None,
            use_sidecar=False,
        )
        self.tracker.emit("convert.done", outputs=len(result.outputs), valid=result.valid_count, invalid=len(result.invalid))
        return result

    def generate_variants(
        self,
        *,
        layout_paths: List[Path],
        out_dir: Path,
        project_init: Optional[Path] = None,
        attach_gamma_crops: bool = False,
        gamma_report: Optional[Dict[str, Any]] = None,
        gamma_attach_kinds: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate publishing variants based on `project_init.json` decisions.

        Rules (MVP):
        - `variants`: ["color","grayscale"] or single value; "both" treated as both
        - `format`: "A4" | "8x11.5" | "both"
        - If "color" present: apply bleed_mm (default 3.0) when `bleed_mm` in project_init or default
        - If "grayscale" present: grayscale conversion (colors only)
        """

        from packages.variant_generator import apply_bleed, convert_layout_colors_to_grayscale, convert_layout_format, validate_kdp_layout
        from packages.layout_schema import validate_layout

        init: Dict[str, Any] = {}
        if project_init and Path(project_init).exists():
            init = json.loads(Path(project_init).read_text(encoding="utf-8"))

        variants = init.get("variants", ["color"])
        if variants == "both":
            variants = ["color", "grayscale"]
        if isinstance(variants, str):
            variants = [variants]

        fmt = init.get("format", "A4")
        formats: List[str] = []
        if fmt == "both":
            formats = ["A4", "8x11.5"]
        elif isinstance(fmt, str):
            formats = [fmt]
        else:
            formats = ["A4"]

        bleed_mm = float(init.get("bleed_mm", 3.0))
        out_dir.mkdir(parents=True, exist_ok=True)

        report: Dict[str, Any] = {"outputs": [], "errors": []}
        self.tracker.emit("variants.start", inputs=len(layout_paths), variants=variants, formats=formats)

        gamma_attach_kinds = gamma_attach_kinds or ["image_box"]

        for base_path in layout_paths:
            try:
                base = json.loads(Path(base_path).read_text(encoding="utf-8"))
            except Exception as exc:
                report["errors"].append({"path": str(base_path), "error": str(exc)})
                continue

            for target_format in formats:
                try:
                    formatted = convert_layout_format(base, target_format=target_format) if target_format else base
                except Exception as exc:
                    report["errors"].append({"path": str(base_path), "format": target_format, "error": str(exc)})
                    continue

                for v in variants:
                    try:
                        out_layout = formatted
                        suffix_parts = []
                        if target_format:
                            suffix_parts.append(target_format.replace(".", "_").replace(",", "_"))
                        suffix_parts.append(v)

                        if v == "color":
                            out_layout = apply_bleed(out_layout, bleed_mm=bleed_mm)
                        elif v == "grayscale":
                            out_layout = convert_layout_colors_to_grayscale(out_layout)
                        else:
                            # Unknown: pass-through
                            pass

                        if attach_gamma_crops and gamma_report:
                            pptx_name = None
                            try:
                                pptx_name = (out_layout.get("source") or {}).get("name") or (base.get("source") or {}).get("name")
                            except Exception:
                                pptx_name = None
                            out_layout = self.attach_gamma_crops_to_layout(
                                layout_json=out_layout,
                                gamma_report=gamma_report,
                                pptx_name=pptx_name,
                                kinds=gamma_attach_kinds,
                            )

                        ok, schema_errors = validate_layout(out_layout)
                        kdp_ok, kdp_errors = validate_kdp_layout(out_layout, safety_margin_px=0.0)

                        out_name = base_path.stem + "." + ".".join(suffix_parts) + ".layout.json"
                        out_path = out_dir / out_name
                        out_path.write_text(json.dumps(out_layout, ensure_ascii=False, indent=2), encoding="utf-8")

                        report["outputs"].append(
                            {
                                "in": str(base_path),
                                "out": str(out_path),
                                "format": target_format,
                                "variant": v,
                                "schema_valid": ok,
                                "schema_errors": schema_errors[:10],
                                "kdp_valid": kdp_ok,
                                "kdp_errors": kdp_errors[:10],
                            }
                        )
                    except Exception as exc:
                        report["errors"].append({"path": str(base_path), "format": target_format, "variant": v, "error": str(exc)})

        self.tracker.emit("variants.done", outputs=len(report["outputs"]), errors=len(report["errors"]))
        return report

    def quality_check(
        self,
        *,
        layout_paths: List[Path],
        out_dir: Path,
        checks: Optional[List[str]] = None,
        project_init: Optional[Path] = None,
        report_name: str = "quality_report.json",
    ) -> Dict[str, Any]:
        """
        Run basic quality checks on a set of layout JSON files.

        Checks (MVP):
        - preflight: schema + semantic validation
        - amazon: KDP constraint validation
        """

        from packages.quality_check import (
            check_amazon_constraints,
            evaluate_quality_gate,
            run_heuristic_checks,
            run_preflight,
            summarize_quality_gate,
            HeuristicConfig,
        )

        checks = checks or ["preflight", "amazon"]
        out_dir.mkdir(parents=True, exist_ok=True)

        init: Dict[str, Any] = {}
        if project_init and Path(project_init).exists():
            try:
                init = json.loads(Path(project_init).read_text(encoding="utf-8"))
            except Exception:
                init = {}

        report: Dict[str, Any] = {"outputs": [], "errors": [], "checks": list(checks)}
        self.tracker.emit("quality.start", inputs=len(layout_paths), checks=checks)

        for p in layout_paths:
            try:
                layout = json.loads(Path(p).read_text(encoding="utf-8"))
            except Exception as exc:
                report["errors"].append({"path": str(p), "error": f"failed to read json: {exc}"})
                continue

            entry: Dict[str, Any] = {"path": str(p)}
            try:
                if "preflight" in checks:
                    ok, errs = run_preflight(layout)
                    entry["preflight_valid"] = bool(ok)
                    entry["preflight_errors"] = list(errs[:50])
                if "amazon" in checks:
                    ok, errs = check_amazon_constraints(layout)
                    entry["amazon_valid"] = bool(ok)
                    entry["amazon_errors"] = list(errs[:50])

                # Quality gate (fail/warn policy), always computed.
                gate_results = evaluate_quality_gate(layout, project_init=init)
                entry["quality_gate"] = summarize_quality_gate(gate_results)

                # Heuristic checks (warn-only), opt-in via checks list.
                if "heuristics" in checks:
                    hcfg_raw = ((init.get("quality") or {}).get("heuristics") or {})
                    hcfg = HeuristicConfig(
                        avg_char_width_em=float(hcfg_raw.get("avg_char_width_em", 0.6)),
                        line_height_em=float(hcfg_raw.get("line_height_em", 1.2)),
                        overflow_warn_ratio=float(hcfg_raw.get("overflow_warn_ratio", 1.0)),
                        overflow_info_ratio=float(hcfg_raw.get("overflow_info_ratio", 0.9)),
                        objects_per_page_warn=int(hcfg_raw.get("objects_per_page_warn", 80)),
                    )
                    entry["heuristics"] = run_heuristic_checks(layout, config=hcfg)
            except Exception as exc:
                report["errors"].append({"path": str(p), "error": str(exc)})
                continue

            report["outputs"].append(entry)

        report_path = out_dir / report_name
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        report["report_path"] = str(report_path)

        self.tracker.emit("quality.done", outputs=len(report["outputs"]), errors=len(report["errors"]), report=str(report_path))
        return report

    def gamma_sync(
        self,
        *,
        extracted_manifest_path: Path,
        extracted_root: Path,
        gamma_png_dir: Path,
        out_dir: Path,
        crop_kinds: Optional[List[str]] = None,
        crop_pad_px: int = 10,
        crop_refine: bool = True,
        crop_refine_margin_px: int = 40,
        crop_bg_threshold: int = 245,
    ) -> Dict[str, Any]:
        """
        Phase 3 (gamma_sync): create real crop PNG artifacts from Gamma exports.

        Input assumptions:
        - `extracted_manifest_path` is `media_pool/pptx/manifest.json` produced by `tools/extract_pptx_assets.py`
        - `gamma_png_dir` contains ZIPs named like `<pptx_stem>.zip` (Gamma exports)
        - each ZIP contains slide PNGs named like `10_Title.png` (prefix includes slide index)
        """

        from packages.pptx_parser.image_cropper import (
            CropConfig,
            crop_from_image,
            find_gamma_png_in_zip,
            load_png_from_zip,
        )

        manifest = json.loads(extracted_manifest_path.read_text(encoding="utf-8"))
        files = manifest.get("files") or []
        out_dir.mkdir(parents=True, exist_ok=True)

        cfg = CropConfig(
            pad_px=int(crop_pad_px),
            refine=bool(crop_refine),
            refine_margin_px=int(crop_refine_margin_px),
            bg_threshold=int(crop_bg_threshold),
        )

        crop_kinds = crop_kinds or ["infobox", "image_box"]
        report: Dict[str, Any] = {"outputs": [], "errors": []}
        self.tracker.emit("gamma_sync.start", files=len(files), out_dir=str(out_dir))

        for entry in files:
            name = entry.get("name") or ""
            rel_json = entry.get("json")
            if not name or not rel_json:
                continue

            # `manifest.json` may contain Windows-style backslashes even when running in Linux containers.
            extracted_rel = str(rel_json).replace("\\", "/")
            extracted_path = extracted_root / Path(extracted_rel)
            if not extracted_path.exists():
                # Fallback: search by basename (handles odd ZIP extraction/path variants)
                try:
                    base_name = Path(extracted_rel).name
                    hits = list(extracted_root.rglob(base_name))
                    if not hits:
                        # Some ZIP tools on Windows can store backslashes in filenames; on Linux those become literal chars.
                        # In that case the filename may end with the expected basename but include extra prefix.
                        for p in extracted_root.rglob("*.json"):
                            try:
                                if Path(p).name.endswith(base_name):
                                    hits.append(p)
                                    break
                            except Exception:
                                continue
                    if hits:
                        extracted_path = Path(hits[0])
                except Exception:
                    pass
            try:
                extracted = json.loads(extracted_path.read_text(encoding="utf-8"))
            except Exception as exc:
                report["errors"].append({"pptx": name, "error": f"failed to read extracted json: {exc}"})
                continue

            zip_path = gamma_png_dir / f"{name}.zip"
            if not zip_path.exists():
                report["errors"].append({"pptx": name, "error": f"gamma zip not found: {zip_path}"})
                continue

            for slide in extracted.get("slides") or []:
                slide_index = int(slide.get("slide") or 0)
                if slide_index <= 0:
                    continue

                member = find_gamma_png_in_zip(zip_path, slide_index=slide_index)
                if not member:
                    report["errors"].append({"pptx": name, "slide": slide_index, "error": "no png in zip"})
                    continue

                try:
                    image = load_png_from_zip(zip_path, member)
                except Exception as exc:
                    report["errors"].append({"pptx": name, "slide": slide_index, "error": f"failed to load png: {exc}"})
                    continue

                if "infobox" in crop_kinds:
                    infoboxes = slide.get("infoboxes") or []
                    for i, ib in enumerate(infoboxes):
                        rel_bbox = ib.get("rel_bbox")
                        if not isinstance(rel_bbox, list) or len(rel_bbox) != 4:
                            continue
                        out_path = out_dir / name / f"slide_{slide_index:03d}" / f"infobox_{i:02d}.png"
                        try:
                            bbox_px = crop_from_image(image, rel_bbox, out_path, config=cfg)
                            report["outputs"].append(
                                {
                                    "pptx": name,
                                    "slide": slide_index,
                                    "box_index": i,
                                    "kind": "infobox",
                                    "member": member,
                                    "out": str(out_path),
                                    "bbox_px": bbox_px,
                                    "rel_bbox": rel_bbox,
                                }
                            )
                        except Exception as exc:
                            report["errors"].append(
                                {"pptx": name, "slide": slide_index, "kind": "infobox", "error": str(exc)}
                            )

                if "image_box" in crop_kinds:
                    image_boxes = slide.get("image_boxes") or []
                    for i, ibox in enumerate(image_boxes):
                        rel_bbox = ibox.get("rel_bbox")
                        if not isinstance(rel_bbox, list) or len(rel_bbox) != 4:
                            continue
                        out_path = out_dir / name / f"slide_{slide_index:03d}" / f"image_{i:02d}.png"
                        try:
                            bbox_px = crop_from_image(image, rel_bbox, out_path, config=cfg)
                            report["outputs"].append(
                                {
                                    "pptx": name,
                                    "slide": slide_index,
                                    "box_index": i,
                                    "kind": "image_box",
                                    "member": member,
                                    "out": str(out_path),
                                    "bbox_px": bbox_px,
                                    "rel_bbox": rel_bbox,
                                }
                            )
                        except Exception as exc:
                            report["errors"].append(
                                {"pptx": name, "slide": slide_index, "kind": "image_box", "error": str(exc)}
                            )

        self.tracker.emit("gamma_sync.done", outputs=len(report["outputs"]), errors=len(report["errors"]))
        return report

    def attach_gamma_crops_to_layout(
        self,
        *,
        layout_json: Dict[str, Any],
        gamma_report: Dict[str, Any],
        pptx_name: Optional[str] = None,
        kinds: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Attach gamma crop PNGs to layout image objects by matching sourceSlide/sourceIndex.
        Expects `gamma_sync` report entries with fields: pptx, slide, kind, box_index, out.
        """

        kinds = kinds or ["image_box"]
        index: Dict[tuple, str] = {}
        for o in gamma_report.get("outputs") or []:
            try:
                if (o.get("kind") not in kinds) or not o.get("out"):
                    continue
                if pptx_name and o.get("pptx") != pptx_name:
                    continue
                key = (int(o.get("slide") or 0), int(o.get("box_index") or 0), str(o.get("kind")))
                index[key] = str(o.get("out"))
            except Exception:
                continue

        for page in layout_json.get("pages", []) or []:
            for obj in page.get("objects", []) or []:
                if obj.get("type") != "image":
                    continue
                if str(obj.get("sourceKind") or "") not in kinds:
                    continue
                try:
                    slide = int(obj.get("sourceSlide") or 0)
                    idx = int(obj.get("sourceIndex") or 0)
                    kind = str(obj.get("sourceKind") or "")
                except Exception:
                    continue
                path = index.get((slide, idx, kind))
                if path:
                    obj["imageUrl"] = path
                    obj["gammaCrop"] = True

        layout_json.setdefault("variant", {})
        layout_json["variant"]["gamma_crops_attached"] = True
        return layout_json


class IdempotentStepExecutor:
    """
    Verantwortlich für die idempotente Ausführung eines einzelnen Workflow-Schritts.
    Prüft vorab, ob der Schritt bereits mit identischen Inputs erledigt wurde.

    Unterstützt sync und async `action` Callables.
    """

    def __init__(self, resume_manager: ResumeManager, *, tracker: Optional[ProgressTracker] = None):
        self.resume_manager = resume_manager
        self.tracker = tracker or ProgressTracker()
        self.logger = logging.getLogger("StepExecutor")

    async def execute_step(self, state: Dict[str, Any], step_cfg: Dict[str, Any]):
        step_id = step_cfg["id"]
        action = step_cfg["action"]
        inputs = step_cfg.get("inputs", {})

        current_input_hash = hash_inputs(inputs)
        existing_step = self.resume_manager.get_step(state, step_id)

        if existing_step.get("status") == "completed":
            if existing_step.get("input_hash") == current_input_hash:
                self.logger.info(f"Step '{step_id}' bereits abgeschlossen (Hash-Match). Überspringe.")
                self.tracker.emit("step.skipped", step_id=step_id)
                return existing_step.get("outputs")
            self.logger.info(f"Step '{step_id}' Inputs geändert. Führe neu aus.")

        self.logger.info(f"Starte Step: {step_id}")
        self.tracker.emit("step.started", step_id=step_id)
        self.resume_manager.mark_step_running(state, step_id, input_hash=current_input_hash)
        self.resume_manager.save(state)

        try:
            result = action(inputs)
            if inspect.isawaitable(result):
                result = await result

            self.resume_manager.mark_step_completed(
                state,
                step_id,
                outputs=result,
                summary={"success": True},
            )
            self.resume_manager.save(state)
            self.tracker.emit("step.completed", step_id=step_id)
            return result
        except Exception as e:
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            self.logger.error(f"Fehler in Step '{step_id}': {error_msg}")
            self.resume_manager.mark_step_failed(state, step_id, error=error_msg)
            self.resume_manager.save(state)
            self.tracker.emit("step.failed", step_id=step_id, error=str(e))
            raise


def _minimal_png_1x1() -> bytes:
    # 1x1 transparent PNG
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
        b"\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def _minimal_pdf_bytes(message: str) -> bytes:
    """
    Minimal single-page PDF without external deps (good enough for pipeline wiring/tests).
    """

    msg = (message or "PDF").replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")[:200]

    # Build objects
    parts: List[bytes] = []
    parts.append(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

    offsets = []

    def add_obj(obj_no: int, body: bytes) -> None:
        offsets.append(sum(len(p) for p in parts))
        parts.append(f"{obj_no} 0 obj\n".encode("ascii") + body + b"\nendobj\n")

    add_obj(1, b"<< /Type /Catalog /Pages 2 0 R >>")
    add_obj(2, b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    add_obj(3, b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>")

    stream = f"BT /F1 18 Tf 72 770 Td ({msg}) Tj ET\n".encode("utf-8")
    add_obj(4, b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"endstream")
    add_obj(5, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    # Xref
    xref_start = sum(len(p) for p in parts)
    parts.append(b"xref\n0 6\n0000000000 65535 f \n")
    for off in offsets:
        parts.append(f"{off:010d} 00000 n \n".encode("ascii"))
    parts.append(b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n")
    parts.append(f"{xref_start}\n".encode("ascii"))
    parts.append(b"%%EOF\n")
    return b"".join(parts)
