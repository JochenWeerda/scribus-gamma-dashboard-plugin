import argparse
import sys
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.figma_integration.client import FigmaClient
from packages.figma_integration.converter import FrameToLayoutConverter


def _safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("_") or "frame"


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Figma frames to layout JSON files.")
    parser.add_argument("--file-key", required=True, help="Figma file key")
    parser.add_argument("--out", default="media_pool/figma_import", help="Output directory")
    parser.add_argument("--dpi", type=int, default=300, help="DPI for conversion")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of frames")
    args = parser.parse_args()

    client = FigmaClient()
    converter = FrameToLayoutConverter()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    frames = client.list_frames(args.file_key)
    if args.limit and args.limit > 0:
        frames = frames[: args.limit]

    outputs = []
    for frame in frames:
        frame_id = frame.get("id")
        frame_name = frame.get("name") or frame_id
        if not frame_id:
            continue
        frame_json = client.get_frame(args.file_key, frame_id)
        layout_json = converter.convert(frame_json, dpi=args.dpi, page_number=1)

        out_name = f"{_safe_name(frame_name)}_{frame_id}.layout.json"
        out_path = out_dir / out_name
        out_path.write_text(json.dumps(layout_json, ensure_ascii=False, indent=2), encoding="utf-8")
        outputs.append(str(out_path))

    print(json.dumps({"file_key": args.file_key, "count": len(outputs), "outputs": outputs}, indent=2))


if __name__ == "__main__":
    main()
