# Quality Gate Checkliste (MVP)

Diese Checkliste definiert die Minimum-Kriterien fuer den automatisierten Quality Gate.
Sie ist Grundlage fuer `packages/quality_check` und die DoD.

## Pflicht (Fail)
- Layout JSON Schema ist gueltig (`layout_schema`)
- Amazon/KDP-Format passt (Trim + Bleed)
- Keine fehlenden Bild-Referenzen (`imageUrl`/`mediaId` leer)
- Fonts/Styles sind vorhanden und nicht leer
- Seitenformat ist konsistent ueber alle Pages

## Warnungen (Warn)
- Text-Overflow Risiko (heuristisch)
- Zu viele Objekte pro Seite (Performance)
- Infobox/Quote ohne Titel oder Quelle
- Bild-Aufloesung unter Ziel-DPI

## Informativ (Info)
- Hoher Bildanteil vs. Textanteil
- Sehr lange Headlines
- Ungewoehnliche Layer-Reihenfolge

## Quellen
- `packages/quality_check/policy.py`
- `packages/quality_check/hybrid_checks.py`
