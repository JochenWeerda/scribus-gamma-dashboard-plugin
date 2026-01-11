from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from .decision_store import DecisionStore
from .question_engine import build_default_questionnaire, validate_decisions
from .session import DialogSession


def _parse_choice(q, raw: str) -> Any:
    raw = (raw or "").strip()
    if q.kind == "bool":
        return raw.lower() in {"1", "true", "yes", "y", "ja"}
    if q.kind == "number":
        try:
            return int(raw) if raw.isdigit() else float(raw)
        except Exception:
            return raw
    return raw


def _cmd_validate(args: argparse.Namespace) -> int:
    store = DecisionStore(Path(args.file))
    decisions = store.load()
    ok, errors = validate_decisions(build_default_questionnaire(), decisions, require_all=True)
    if ok:
        print("OK")
        return 0
    print("INVALID")
    for e in errors[:50]:
        print("-", e)
    return 2


def _cmd_run(args: argparse.Namespace) -> int:
    store = DecisionStore(Path(args.file))
    session = DialogSession(store)

    while True:
        q = session.next_question()
        if q is None:
            break

        print(f"\n[{q.block}] {q.prompt}  (key={q.key})")
        if q.help:
            print(q.help)
        if q.choices:
            for c in q.choices:
                print(f"  - {c.value}: {c.label}")
        if q.default is not None:
            print(f"Default: {q.default}")

        if args.non_interactive:
            if q.default is None:
                raise SystemExit(f"Missing non-interactive answer for {q.key} (no default)")
            session.answer(q.key, q.default, source="cli.default")
            continue

        raw = input("> ").strip()
        if raw == "" and q.default is not None:
            value = q.default
        else:
            value = _parse_choice(q, raw)

        session.answer(q.key, value, source="cli")

    print("\nDialog complete.")
    return _cmd_validate(args)


def _cmd_export_project_init(args: argparse.Namespace) -> int:
    store = DecisionStore(Path(args.file))
    decisions = store.load()

    template_path = Path(args.template) if args.template else None
    template: Dict[str, Any] = {}
    if template_path and template_path.exists():
        template = json.loads(template_path.read_text(encoding="utf-8"))

    # Apply known fields
    if "format" in decisions:
        template["format"] = decisions["format"]
    if "variants" in decisions:
        v = decisions["variants"]
        if v == "both":
            template["variants"] = ["color", "grayscale"]
        elif isinstance(v, list):
            template["variants"] = v
        else:
            template["variants"] = [v]
    if "akt_colors" in decisions:
        template["akt_colors"] = decisions["akt_colors"]
    if "layout_density" in decisions:
        template["layout_density"] = decisions["layout_density"]
    if "sidebar_detection" in decisions:
        template["sidebar_detection"] = decisions["sidebar_detection"]
    if "infographic_handling" in decisions:
        template["infographic_handling"] = decisions["infographic_handling"]

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dialog_engine", description="Dialog Engine CLI (MVP).")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="Run the interactive dialog and persist decisions")
    run.add_argument("--file", default="temp_analysis/dialog_decisions.json", help="Decision JSON path")
    run.add_argument("--non-interactive", action="store_true", help="Use defaults only (fails if a question has no default)")
    run.set_defaults(func=_cmd_run)

    val = sub.add_parser("validate", help="Validate an existing decisions file")
    val.add_argument("--file", default="temp_analysis/dialog_decisions.json", help="Decision JSON path")
    val.set_defaults(func=_cmd_validate)

    exp = sub.add_parser("export-project-init", help="Export/merge decisions into a project_init.json")
    exp.add_argument("--file", default="temp_analysis/dialog_decisions.json", help="Decision JSON path")
    exp.add_argument("--template", default=".cursor/project_init.json.template", help="Optional template path")
    exp.add_argument("--out", default="project_init.json", help="Output path")
    exp.set_defaults(func=_cmd_export_project_init)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))
