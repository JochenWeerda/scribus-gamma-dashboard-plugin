from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


@dataclass(frozen=True)
class PptxProjectMetadata:
    chapter: Optional[int] = None
    act: Optional[int] = None
    act_title: Optional[str] = None


def load_project_init(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8"))


def _chapter_for_pptx_name(project_init: Dict[str, Any], pptx_name: str) -> Optional[int]:
    for entry in project_init.get("chapter_map", []) or []:
        if (entry.get("pptx") or "") == pptx_name:
            try:
                return int(entry.get("chapter"))
            except Exception:
                return None
    return None


def _act_for_chapter(project_init: Dict[str, Any], chapter: int) -> Tuple[Optional[int], Optional[str]]:
    for act_entry in project_init.get("acts", []) or []:
        try:
            act_no = int(act_entry.get("act"))
        except Exception:
            continue

        chapters = act_entry.get("chapters")
        if isinstance(chapters, (list, tuple)) and len(chapters) == 2:
            try:
                start = int(chapters[0])
                end = int(chapters[1])
                if start <= chapter <= end:
                    return act_no, act_entry.get("title")
            except Exception:
                pass
        elif isinstance(chapters, (list, tuple)):
            try:
                chapter_list = {int(x) for x in chapters}
                if chapter in chapter_list:
                    return act_no, act_entry.get("title")
            except Exception:
                pass
    return None, None


def resolve_project_metadata(project_init: Dict[str, Any], *, pptx_name: str) -> PptxProjectMetadata:
    chapter = _chapter_for_pptx_name(project_init, pptx_name)
    if chapter is None:
        return PptxProjectMetadata()
    act, act_title = _act_for_chapter(project_init, chapter)
    return PptxProjectMetadata(chapter=chapter, act=act, act_title=act_title)

