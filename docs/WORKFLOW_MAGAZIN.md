## Workflow: Magazin-Produktion ohne InDesign (lua-pagemaker + gamma.app + napkin.ai)

### Ziel
- **Print**: Magazin-Layout mit Wow-Effekt über **LuaLaTeX + lua-pagemaker** (4-Spalten-Grid, Bleed, Gutter).
- **Digital**: bleibt stabil (später optional optimieren).
- **Assets**: Bilder via **gamma.app**, Infografik-Skizzen via **napkin.ai** (danach drucktauglich finalisieren).

### Rollen (Agenten / Verantwortlichkeiten)
- **Chefredaktion/Struktur**
  - Output: Flatplan (130 Seiten), Kapitel-Rhythmus, „Wow“-Doppelseiten-Plan.
- **Art Direction / Style Guide**
  - Output: Typo-Skala, Farben, Box-Styles, Icon-Stil, „Uhr“-Leitelement.
- **Layout Engineer (lua-pagemaker)**
  - Output: Templates + PagePlan-Slots + Constraint „max 1 Box-Zone pro Spalte“.
- **Asset Producer (gamma.app)**
  - Output: Hero-Shots / Key Visuals (hires), konsistente Stil-Variante.
- **Infografik Producer (napkin.ai → final)**
  - Output: Skizze (napkin) → finaler Vektor/HiRes-Export.
- **Preflight**
  - Output: Druck-Check (Bleed, Fonts, DPI, Schwarz, Safe-Area).

### Produktionspipeline (pro Kapitel)
1) **Kapitelbriefing**
   - Kernthese, 3–5 Subheads, 1 Pullquote, 1 Factbox, 1–2 Captions
2) **Asset-Liste**
   - Eintrag in `assets/manifest_assets.csv` (ID, Zweck, Format, Status)
3) **Generierung**
   - gamma: Hero/Illustrationen
   - napkin: Infografik-Skizze
4) **Finalisierung**
   - Infografik: drucktauglich (Lesbarkeit, Kontrast, keine Artefakte)
5) **Einbau**
   - LaTeX: `\includegraphics[width=\linewidth]{...}` (Print)
   - Slots über `tex/pageplan.tex` setzen
6) **Preview**
   - `.\start_preview.ps1` (Cursor PNG Preview)


