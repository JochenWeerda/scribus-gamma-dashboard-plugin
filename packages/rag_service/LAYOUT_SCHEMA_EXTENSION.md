# Layout JSON Schema Erweiterung für RAG

## Erweiterte Felder

Das Layout JSON Schema wurde erweitert, um Text-Bild-Zuordnungen und gescannte Inhalte zu unterstützen.

## Object-Erweiterungen

### Text-Objekte

```json
{
  "id": "text_001",
  "type": "text",
  "content": "Headline über KI",
  "bbox": {"x": 124, "y": 1502, "w": 2232, "h": 140},
  "layer": "Text",
  "zOrder": 0,
  "relatedImageIds": ["image_001", "image_002"]  // NEU: Zuordnung zu Bildern
}
```

### Bild-Objekte

```json
{
  "id": "image_001",
  "type": "image",
  "bbox": {"x": 124, "y": 2000, "w": 800, "h": 600},
  "layer": "Images",
  "zOrder": 1,
  "mediaId": "minio://images/ki-illustration.png",
  "relatedTextIds": ["text_001"],  // NEU: Zuordnung zu Texten
  "metadata": {  // NEU: Metadaten für RAG
    "altText": "KI-Neuronales Netzwerk",
    "description": "Visualisierung von künstlicher Intelligenz",
    "extractedText": "Neuronales Netzwerk mit 3 Layern..."  // Optional: OCR-Text
  }
}
```

## scannedContent-Sektion

Neue Sektion auf Page-Level für gescannte Inhalte:

```json
{
  "pages": [{
    "pageNumber": 1,
    "objects": [...],
    "scannedContent": {  // NEU: Gescannte Inhalte
      "texts": [
        {
          "id": "scanned_text_001",
          "source": "media_pool/articles/ki-article.pdf",
          "content": "Künstliche Intelligenz revolutioniert...",
          "pageNumber": 1,
          "relatedImageIds": ["image_001"]  // Zuordnung zu Bildern
        }
      ],
      "images": [
        {
          "id": "scanned_image_001",
          "source": "media_pool/images/ki-diagram.png",
          "path": "minio://images/ki-diagram.png",
          "relatedTextIds": ["scanned_text_001", "text_001"],  // Zuordnung zu Texten
          "metadata": {
            "altText": "KI-Architektur-Diagramm",
            "extractedText": "Neuronales Netzwerk mit 3 Layern..."  // Optional: OCR
          }
        }
      ]
    }
  }]
}
```

## Vollständiges Beispiel

```json
{
  "version": "1.0.0",
  "document": {
    "width": 2480,
    "height": 3508,
    "dpi": 300
  },
  "pages": [{
    "pageNumber": 1,
    "objects": [
      {
        "id": "text_001",
        "type": "text",
        "content": "Headline über KI",
        "bbox": {"x": 124, "y": 1502, "w": 2232, "h": 140},
        "layer": "Text",
        "zOrder": 0,
        "relatedImageIds": ["image_001"]
      },
      {
        "id": "image_001",
        "type": "image",
        "bbox": {"x": 124, "y": 2000, "w": 800, "h": 600},
        "layer": "Images",
        "zOrder": 1,
        "mediaId": "minio://images/ki-illustration.png",
        "relatedTextIds": ["text_001"],
        "metadata": {
          "altText": "KI-Neuronales Netzwerk",
          "description": "Visualisierung von künstlicher Intelligenz"
        }
      }
    ],
    "scannedContent": {
      "texts": [
        {
          "id": "scanned_text_001",
          "source": "media_pool/articles/ki-article.pdf",
          "content": "Künstliche Intelligenz revolutioniert...",
          "pageNumber": 1,
          "relatedImageIds": ["image_001"]
        }
      ],
      "images": [
        {
          "id": "scanned_image_001",
          "source": "media_pool/images/ki-diagram.png",
          "path": "minio://images/ki-diagram.png",
          "relatedTextIds": ["scanned_text_001", "text_001"],
          "metadata": {
            "altText": "KI-Architektur-Diagramm",
            "extractedText": "Neuronales Netzwerk mit 3 Layern..."
          }
        }
      ]
    }
  }]
}
```

## Migration

Bestehende Layout JSON Dateien sind weiterhin kompatibel. Die neuen Felder sind optional:

- `relatedImageIds` / `relatedTextIds`: Optional, Array von IDs
- `metadata`: Optional, Objekt mit `altText`, `description`, `extractedText`
- `scannedContent`: Optional, Objekt mit `texts` und `images` Arrays

## Verwendung im RAG-Service

Der RAG-Service nutzt diese Erweiterungen für:

1. **Text-Bild-Zuordnungen**: `relatedImageIds` / `relatedTextIds` werden für Pair-Indexing verwendet
2. **Bild-Metadaten**: `metadata.altText` und `metadata.description` werden für CLIP-Embeddings verwendet
3. **Gescannte Inhalte**: `scannedContent` wird separat indexiert für erweiterte Suche

