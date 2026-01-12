import asyncio
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.rag_service import AutoIndexer, EmbeddingModels, RAGDatabase


def _chunk_text(text: str, max_chars: int = 2000, overlap: int = 200) -> List[str]:
    chunks = []
    if not text:
        return chunks
    start = 0
    length = len(text)
    while start < length:
        end = min(length, start + max_chars)
        chunks.append(text[start:end])
        if end >= length:
            break
        start = max(0, end - overlap)
    return chunks


async def _index_prompts(root: Path) -> int:
    db = RAGDatabase()
    embeddings = EmbeddingModels()
    auto_indexer = AutoIndexer(db, embeddings)

    texts = []
    for path in sorted(root.rglob("*.md")):
        content = path.read_text(encoding="utf-8", errors="ignore")
        pieces = _chunk_text(content)
        for idx, chunk in enumerate(pieces):
            texts.append(
                {
                    "text": chunk,
                    "source": f"{path}#chunk{idx:03d}",
                    "metadata": {
                        "source_type": "prompt",
                        "path": str(path),
                        "chunk_index": idx,
                        "chunk_total": len(pieces),
                        "title": path.stem,
                    },
                }
            )

    if not texts:
        print("No prompt markdown files found.")
        return 0

    result = await auto_indexer.index_media_scan(texts=texts, images=None)
    return len(result.get("text_ids") or [])


def main() -> None:
    root = Path("archive/prompts")
    if not root.exists():
        print("archive/prompts not found. Nothing to index.")
        return

    indexed = asyncio.run(_index_prompts(root))
    print(f"Indexed {indexed} prompt chunks into RAG.")


if __name__ == "__main__":
    main()
