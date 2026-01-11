# RAG Service - Multimodale Layout-Suche

RAG-System (Retrieval-Augmented Generation) für intelligente Suche nach ähnlichen Layouts, Texten und Bildern.

## Features

- **Layout-Indexing**: Automatisches Indexing von Layout JSON (Figma, Scribus, LLM)
- **Medien-Indexing**: Indexing von gescannten Texten und Bildern (PDF, DOCX, PPTX)
- **Multimodale Suche**: Text-Bild-Matching mit CLIP-Similarity
- **LLM-Kontext-Erweiterung**: Erweitert Prompts mit ähnlichen Layouts und relevanten Inhalten
- **Scribus Digital Twin**: Validiert XML-Konstrukte gegen bekannte Patterns

## Installation

```bash
pip install -r requirements.txt
```

## Verwendung

### Initialisierung

```python
from packages.rag_service import RAGDatabase, EmbeddingModels, AutoIndexer

# Initialisiere RAG-Service
db = RAGDatabase(persist_directory="./chroma_db")
embeddings = EmbeddingModels()
auto_indexer = AutoIndexer(db, embeddings)
```

### Layout-Indexing

```python
# Nach Figma-Import
layout_id = await auto_indexer.index_figma_import(layout_json)

# Nach Scribus-Export
layout_id = await auto_indexer.index_scribus_export(layout_json)

# Nach LLM-Generierung
layout_id = await auto_indexer.index_llm_generation(layout_json)
```

### Medien-Indexing

```python
# Gescannte Texte und Bilder
result = await auto_indexer.index_media_scan(
    texts=[
        {"text": "...", "source": "file.pdf", "metadata": {...}}
    ],
    images=[
        {"path": "...", "metadata": {...}}
    ]
)
```

### Retrieval

```python
from packages.rag_service import LayoutRetriever, TextImageMatcher

retriever = LayoutRetriever(db, embeddings)
matcher = TextImageMatcher(db, embeddings)

# Ähnliche Layouts finden
similar = retriever.find_similar_layouts("magazine layout", top_k=5)

# Bilder für Text finden
images = matcher.find_images_for_text("KI-Artikel", top_k=5)

# Texte für Bild finden
texts = matcher.find_texts_for_image("path/to/image.png", top_k=5)
```

### LLM-Kontext

```python
from packages.rag_service import LLMContextBuilder

context_builder = LLMContextBuilder(db, embeddings, retriever, matcher)

context = context_builder.build_context_for_prompt(
    "Erstelle ein Magazin-Layout über KI",
    top_k_layouts=3,
    top_k_texts=5,
    top_k_images=3
)

enhanced_prompt = context["context"]
```

### Scribus Digital Twin

```python
from packages.rag_service import ScribusValidator
import xml.etree.ElementTree as ET

validator = ScribusValidator(db, embeddings)

# Validiere XML-Konstrukt
xml_element = ET.Element("ITEM", ITEMTEXT="Test")
is_valid, warnings, suggested_fix = validator.validate_xml_construct(xml_element)

# Lerne neues Pattern
validator.learn_xml_pattern(
    xml_element,
    behavior="success",
    test_result={"success": True}
)
```

## API Endpoints

Siehe `api_endpoints.py` für FastAPI-Integration.

Endpoints:
- `POST /api/rag/layouts/similar` - Ähnliche Layouts finden
- `POST /api/rag/images/for-text` - Bilder für Text finden
- `POST /api/rag/texts/for-image` - Texte für Bild finden
- `POST /api/rag/suggest-pairs` - Text-Bild-Zuordnungen vorschlagen
- `POST /api/rag/llm-context` - LLM-Kontext erstellen
- `POST /api/rag/index/layout` - Layout indexieren
- `POST /api/rag/index/media` - Medien indexieren
- `GET /api/rag/health` - Health Check

## Environment Variables

- `CHROMA_DB_PATH`: Pfad für ChromaDB (default: `./chroma_db`)
- `EMBEDDING_MODEL`: wird aktuell ignoriert (Text-Embedding ist hart auf `paraphrase-multilingual-mpnet-base-v2` gesetzt)
- `CLIP_MODEL`: CLIP-Model (default: `clip-ViT-B-32`)

