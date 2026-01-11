# KI-Integration: Implementierung

**Status:** ✅ Vollständig implementiert

---

## Übersicht

Die KI-Integration für AI-Enhanced Aesthetics ist vollständig implementiert:

1. **OpenAI Vision API** - Für Bildanalyse (Fokus-Detektion)
2. **OpenAI GPT-4** - Für Text-Analyse (Kontextuelle Platzierung)
3. **Google Cloud Vision** - Alternative für Bildanalyse

---

## Installation

### Dependencies

```bash
# OpenAI
pip install openai>=1.0.0

# Google Cloud Vision (optional)
pip install google-cloud-vision>=3.0.0
```

### API Keys

**OpenAI:**
```bash
export OPENAI_API_KEY=sk-...
```

**Google Cloud Vision:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

---

## Verwendung

### Focus Detector (Bildanalyse)

```python
from packages.ai_aesthetics import FocusDetector

# OpenAI
detector = FocusDetector(model_provider="openai", api_key="sk-...")
focus = detector.detect_focus("image.jpg")
# {
#     "focus_center": {"x": 0.5, "y": 0.5},
#     "focus_type": "face",
#     "confidence": 0.9,
#     ...
# }

# Google Vision
detector = FocusDetector(model_provider="google")
focus = detector.detect_focus("image.jpg")
```

### Contextual Placer (Text-Analyse)

```python
from packages.ai_aesthetics import ContextualPlacer

# OpenAI GPT-4
placer = ContextualPlacer(model_provider="openai", api_key="sk-...")
context = placer.analyze_text_context("Das Gesicht des Propheten zeigt...")
# {
#     "keywords": ["face", "portrait", "prophet"],
#     "entities": [...],
#     "sentiment": "neutral",
#     "topics": ["religion", "art"],
#     ...
# }
```

### Integration Engine

```python
from packages.ai_aesthetics import get_ai_aesthetics_engine

# Automatisch aus Environment-Variablen
engine = get_ai_aesthetics_engine()

# Explizit
engine = get_ai_aesthetics_engine(
    enabled=True,
    focus_provider="openai",
    text_provider="openai",
    api_key="sk-..."
)

result = engine.optimize_layout(layout_json, apply_corrections=False)
```

---

## Provider-Details

### OpenAI Provider

**Features:**
- Vision API für Bildanalyse
- GPT-4 für Text-Analyse
- Strukturierte JSON-Responses (Text)
- Fallback bei Fehlern

**Model:**
- Default: `gpt-4o` (Vision + Text)

**Kosten:**
- Vision: ~$0.01 pro Bild
- GPT-4: ~$0.01-0.03 pro 1K Tokens

### Google Vision Provider

**Features:**
- Face Detection
- Object Detection
- Label Detection
- Hohe Genauigkeit für Gesichter

**Kosten:**
- Face Detection: $1.50 pro 1.000 Bilder
- Object Detection: $1.50 pro 1.000 Bilder
- Label Detection: $1.50 pro 1.000 Bilder

---

## Error Handling

Alle Provider haben integriertes Error Handling:

1. **API-Fehler:** Fallback auf einfache Logik
2. **Missing API Key:** Fallback-Modus
3. **Network-Fehler:** Retry-Logik (kann erweitert werden)
4. **Timeout:** Fallback nach Timeout

```python
# Funktioniert auch ohne API Keys (Fallback)
detector = FocusDetector(model_provider="fallback")
focus = detector.detect_focus("image.jpg")  # Zentrierter Fokus
```

---

## Performance

### Latenz

| Provider | Operation | Latenz |
|----------|-----------|--------|
| OpenAI Vision | Bildanalyse | ~500-2000ms |
| OpenAI GPT-4 | Text-Analyse | ~500-1500ms |
| Google Vision | Face Detection | ~300-1000ms |
| Fallback | Einfache Logik | ~1-10ms |

### Optimierungen

- **Caching:** Kann für wiederholte Analysen hinzugefügt werden
- **Batch-Processing:** Mehrere Bilder parallel (kann erweitert werden)
- **Async:** Provider unterstützen async (kann erweitert werden)

---

## Konfiguration

### Environment-Variablen

```bash
# Aktivierung
AI_AESTHETICS_ENABLED=true

# Provider-Auswahl
AI_FOCUS_PROVIDER=openai  # openai, google, fallback
AI_TEXT_PROVIDER=openai   # openai, fallback

# API Keys
OPENAI_API_KEY=sk-...
GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
```

### Code-Konfiguration

```python
from packages.ai_aesthetics import get_ai_aesthetics_engine

engine = get_ai_aesthetics_engine(
    enabled=True,
    focus_provider="openai",  # oder "google", "fallback"
    text_provider="openai",   # oder "fallback"
    api_key="sk-..."          # optional
)
```

---

## Beispiel-Workflow

```python
from packages.ai_aesthetics import get_ai_aesthetics_engine

# 1. Engine initialisieren
engine = get_ai_aesthetics_engine(
    enabled=True,
    focus_provider="openai",
    text_provider="openai"
)

# 2. Layout optimieren
result = engine.optimize_layout(layout_json, apply_corrections=False)

# 3. Optimierungen prüfen
print(f"Focus Adjustments: {result['summary']['focus_adjustments']}")
print(f"Contextual Placements: {result['summary']['contextual_placements']}")
print(f"Balance Corrections: {result['summary']['balance_corrections']}")

# 4. Korrekturen anwenden (optional)
if result['optimizations']:
    optimized = engine.optimize_layout(layout_json, apply_corrections=True)
```

---

## Troubleshooting

### OpenAI API Key nicht gefunden

```
ValueError: OpenAI API Key nicht gefunden
```

**Lösung:**
```bash
export OPENAI_API_KEY=sk-...
```

### Google Vision Credentials fehlen

```
RuntimeError: google-cloud-vision package nicht verfügbar
```

**Lösung:**
```bash
pip install google-cloud-vision
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
```

### Provider-Fehler

Alle Provider haben Fallback-Logik. Bei Fehlern wird automatisch der Fallback-Modus verwendet.

---

## Nächste Schritte

### Mögliche Erweiterungen

1. **Strukturierte JSON-Responses für Vision**
   - Bounding Boxes von OpenAI Vision
   - Genauere Fokus-Regionen

2. **Caching**
   - Hash-basiertes Caching für wiederholte Analysen
   - Redis/Memory Cache

3. **Batch-Processing**
   - Mehrere Bilder parallel analysieren
   - Async/Await für bessere Performance

4. **Lokale Modelle**
   - ONNX-Runtime für Offline-Betrieb
   - TensorFlow Lite für Edge-Devices

---

*Letzte Aktualisierung: 2025-01-27*

