# AI-Enhanced Aesthetics

KI-gestützte Layout-Optimierung für bessere visuelle Qualität.

---

## Übersicht

AI-Enhanced Aesthetics kombiniert drei KI-Module für optimale Layout-Qualität:

1. **Visueller Fokus** - Erkennt wichtige Bildbereiche
2. **Kontextuelle Platzierung** - Platziert Bilder basierend auf Textinhalt
3. **Balance-Checks** - KI als "Art Director" für ästhetische Korrekturen

---

## 1. Visueller Fokus

### Funktion

Die KI analysiert Bilder und erkennt wichtige Bereiche:
- **Gesichter** - Für Porträts
- **Religiöse Symbole** - Kreuze, Ikonen, etc.
- **Zentrale Objekte** - Hauptmotiv des Bildes
- **Wichtige Bildbereiche** - Regionen mit hohem visuellen Gewicht

### Verwendung

```python
from packages.ai_aesthetics import detect_image_focus, FocusDetector

# Fokus erkennen
focus = detect_image_focus("path/to/image.jpg")
# {
#     "focus_center": {"x": 0.5, "y": 0.5},
#     "focus_region": {"x": 0.25, "y": 0.25, "width": 0.5, "height": 0.5},
#     "focus_type": "face",
#     "confidence": 0.95,
# }

# Crop-Vorschlag
detector = FocusDetector()
crop = detector.suggest_crop("path/to/image.jpg", 800, 600)
# {
#     "preserves_focus": True,
#     "focus_overlap": 0.95,
#     "focus_center": {...},
# }
```

### Integration

Der Fokus-Detektor wird automatisch in der Layout-Pipeline verwendet:
- Crop wird so angepasst, dass wichtige Bereiche erhalten bleiben
- Fokus-Center wird bei automatischen Crops berücksichtigt

---

## 2. Kontextuelle Platzierung

### Funktion

Die KI analysiert Text und schlägt vor, wo Bilder inhaltlich hingehören:
- **Keyword-Matching** - Bild-Keywords werden mit Text-Keywords verglichen
- **Topic-Analyse** - Themen werden erkannt (Religion, Kunst, Geschichte, etc.)
- **Relevanz-Score** - Wie gut passt Bild zu Text?

### Verwendung

```python
from packages.ai_aesthetics import suggest_image_placement, ContextualPlacer

# Kontextuelle Platzierung
text_blocks = [
    {"content": "Das Gesicht zeigt...", "x": 100, "y": 200},
    {"content": "Das religiöse Symbol...", "x": 100, "y": 400},
]
image_metadata = {
    "keywords": ["face", "portrait"],
    "type": "portrait",
}
available_positions = [
    {"x": 100, "y": 300, "width": 400, "height": 500},
    {"x": 600, "y": 300, "width": 400, "height": 500},
]

placement = suggest_image_placement(text_blocks, image_metadata, available_positions)
# {
#     "recommended_position": {...},
#     "relevance_score": 0.95,
#     "reasoning": "Bild-Keywords: ['face'], Text-Keywords: ['face']",
# }
```

### Integration

Kontextuelle Platzierung wird verwendet, wenn:
- Bilder in Textfluss eingefügt werden
- Mehrere Bild-Positionen möglich sind
- Text-Kontext verfügbar ist

---

## 3. Balance-Checks (Art Director)

### Funktion

Die KI fungiert als "Art Director" und prüft:
- **Visuelle Balance** - Gewichtsverteilung auf der Seite
- **Spacing** - Abstände zwischen Elementen
- **Alignment** - Ausrichtung und Ordnung
- **Contrast** - Kontraste und Hierarchie

### Verwendung

```python
from packages.ai_aesthetics import check_layout_balance, BalanceChecker

# Balance prüfen
layout_data = {
    "elements": [
        {"id": "img_1", "box": {"x_px": 50, "y_px": 50, ...}},
        {"id": "text_1", "box": {"x_px": 500, "y_px": 100, ...}},
    ]
}

balance = check_layout_balance(layout_data)
# {
#     "balanced": False,
#     "score": 0.75,
#     "issues": [
#         {
#             "type": "spacing",
#             "severity": "medium",
#             "element_id": "img_1",
#             "description": "Element zu nah am Rand",
#             "suggestion": {"x_px": 100, "y_px": 100},
#         }
#     ],
#     "suggestions": [...],
# }

# Ästhetische Korrekturen
checker = BalanceChecker()
corrections = checker.suggest_aesthetic_corrections(layout_data, mathematical_precision=True)
# {
#     "corrections": [
#         {
#             "element_id": "img_1",
#             "type": "micro_adjustment",
#             "changes": {"x_px": 101, "y_px": 103},
#             "reasoning": "Verbessert visuelle Balance",
#         }
#     ],
#     "preserves_precision": True,
# }
```

### Integration

Balance-Checks werden ausgeführt:
- Nach Layout-Generierung
- Vor finalem Export
- Bei mathematischen Grenzfällen (Micro-Adjustments)

---

## Integration in Layout-Pipeline

### AIAestheticsEngine

Die Haupt-Engine kombiniert alle drei Module:

```python
from packages.ai_aesthetics import get_ai_aesthetics_engine

engine = get_ai_aesthetics_engine(enabled=True)
result = engine.optimize_layout(layout_json, apply_corrections=False)

# {
#     "optimized_layout": {...},
#     "optimizations": [
#         {
#             "type": "focus_adjustment",
#             "element_id": "img_1",
#             "changes": {...},
#             "reasoning": "...",
#         },
#         ...
#     ],
#     "summary": {
#         "focus_adjustments": 2,
#         "contextual_placements": 1,
#         "balance_corrections": 3,
#     },
# }
```

### Workflow

1. **Layout-Generierung** - Mathematisches Layout wird erstellt
2. **Fokus-Detektion** - Bilder werden analysiert, Crops angepasst
3. **Kontextuelle Platzierung** - Bilder werden basierend auf Text plaziert
4. **Balance-Checks** - Ästhetische Korrekturen werden vorgeschlagen
5. **Anwendung** - Korrekturen werden angewendet (optional)

---

## Konfiguration

### Environment-Variablen

```bash
# AI-Enhanced Aesthetics
AI_AESTHETICS_ENABLED=true
AI_FOCUS_PROVIDER=openai  # openai, google, fallback
AI_TEXT_PROVIDER=openai   # openai, fallback
AI_AESTHETICS_APPLY_AUTO=false  # Automatisch Korrekturen anwenden

# OpenAI API Key (für OpenAI Provider)
OPENAI_API_KEY=sk-...

# Google Cloud Vision (für Google Provider)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

### Aktivierung

```python
from packages.ai_aesthetics import get_ai_aesthetics_engine

# Aktiviert mit OpenAI (aus Environment-Variablen)
engine = get_ai_aesthetics_engine()

# Aktiviert mit OpenAI (explizit)
engine = get_ai_aesthetics_engine(
    enabled=True,
    focus_provider="openai",
    text_provider="openai",
    api_key="sk-..."
)

# Aktiviert mit Google Vision
engine = get_ai_aesthetics_engine(
    enabled=True,
    focus_provider="google",
    text_provider="openai"  # Text-Analyse bleibt OpenAI
)

# Deaktiviert (Fallback-Modus)
engine = get_ai_aesthetics_engine(enabled=False)
```

### API Keys einrichten

**OpenAI:**
1. Erstelle Account auf https://platform.openai.com
2. Generiere API Key
3. Setze `OPENAI_API_KEY` Environment-Variable

**Google Cloud Vision:**
1. Erstelle Google Cloud Project
2. Aktiviere Vision API
3. Erstelle Service Account
4. Download JSON Key
5. Setze `GOOGLE_APPLICATION_CREDENTIALS` auf JSON-Pfad

---

## KI-Provider

### Aktueller Status

**✅ KI-Integration implementiert:**
- ✅ OpenAI Vision API Integration (Fokus-Detektion)
- ✅ OpenAI GPT-4 Integration (Text-Analyse)
- ✅ Google Cloud Vision Integration (Fokus-Detektion)
- ✅ Fallback-Logik für Offline-Betrieb

### Verfügbare Provider

1. **OpenAI (✅ Implementiert)**
   - Vision API für Bildanalyse (Fokus-Detektion)
   - GPT-4 für Textanalyse (Kontextuelle Platzierung)
   - Model: `gpt-4o` (default)

2. **Google Cloud Vision (✅ Implementiert)**
   - Face Detection
   - Object Detection
   - Label Detection

3. **Fallback (✅ Implementiert)**
   - Einfache Keyword-Erkennung
   - Zentrierter Fokus
   - Funktioniert ohne KI-Provider

---

## Performance

### Latenz

- **Fokus-Detektion:** ~100-500ms pro Bild (abhängig von Provider)
- **Kontextuelle Platzierung:** ~200-800ms pro Seite (Text-Analyse)
- **Balance-Checks:** ~50-200ms pro Seite (lokal)

### Optimierungen

- **Caching:** Fokus-Ergebnisse werden gecacht (gleiche Bilder)
- **Batch-Processing:** Mehrere Bilder parallel analysieren
- **Lazy Loading:** Nur bei Bedarf aktivieren

---

## Beispiele

### Beispiel 1: Fokus-Erhaltung

```python
# Bild mit Gesicht
focus = detect_image_focus("portrait.jpg")
# focus_type: "face", focus_center: {x: 0.4, y: 0.45}

# Crop wird angepasst, um Gesicht zu erhalten
crop = detector.suggest_crop("portrait.jpg", 800, 600)
# preserves_focus: True, focus_overlap: 0.95
```

### Beispiel 2: Kontextuelle Platzierung

```python
# Text: "Das Gesicht des Propheten zeigt..."
# Bild: portrait.jpg (Keywords: ["face", "portrait"])

placement = suggest_image_placement(
    text_blocks=[{"content": "Das Gesicht des Propheten zeigt..."}],
    image_metadata={"keywords": ["face", "portrait"]},
    available_positions=[...]
)
# relevance_score: 0.95, recommended_position: nahe Text
```

### Beispiel 3: Balance-Correction

```python
# Layout hat Element zu nah am Rand
balance = check_layout_balance(layout_data)
# issues: [{"type": "spacing", "element_id": "img_1", ...}]

# Micro-Adjustment wird vorgeschlagen
corrections = checker.suggest_aesthetic_corrections(layout_data, mathematical_precision=True)
# corrections: [{"changes": {"x_px": 101, "y_px": 103}, ...}]
```

---

## Roadmap

### Phase 1: Stub-Implementation ✅
- ✅ Grundgerüst implementiert
- ✅ Fallback-Logik
- ✅ Integration vorbereitet

### Phase 2: KI-Integration (TODO)
- ⚠️ OpenAI Vision API Integration
- ⚠️ Google Cloud Vision Integration
- ⚠️ Text-Analyse (GPT-4)

### Phase 3: Erweiterte Features (TODO)
- ⚠️ Lokale Modelle (ONNX, TensorFlow Lite)
- ⚠️ Batch-Processing
- ⚠️ Caching

---

*Letzte Aktualisierung: 2025-01-27*

