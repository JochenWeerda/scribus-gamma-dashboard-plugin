#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Erstellt vollständiges PagePlan für alle 130 Seiten (65 Doppelseiten).
Definiert Template-Zuordnung pro Seite und generiert LaTeX-Code.
"""

from pathlib import Path

# Seitenzahlen pro Kapitel (aus Manifest)
CHAPTER_PAGES = {
    0: 10,
    1: 13,
    2: 10,
    3: 10,
    4: 10,
    5: 10,
    6: 10,
    7: 10,
    8: 10,
    9: 10,
    10: 10,
    11: 13,
    12: 10,
    13: 9,
}

# Berechne Start-Seiten pro Kapitel
def calculate_page_starts():
    """Berechnet Start-Seiten pro Kapitel"""
    starts = {}
    current = 1
    for ch in range(14):
        starts[ch] = current
        current += CHAPTER_PAGES[ch]
    return starts

# Template-Zuordnung pro Seite
def create_pageplan():
    """Erstellt PagePlan-Mapping für alle Seiten"""
    starts = calculate_page_starts()
    total_pages = sum(CHAPTER_PAGES.values())
    
    plan = {}
    
    for ch in range(14):
        start = starts[ch]
        pages = CHAPTER_PAGES[ch]
        
        # Erste Seite: Opener (bleed)
        plan[start] = "bleed"
        if pages > 1:
            plan[start + 1] = "bleed"  # Zweite Seite des Openers
        
        # Rest: story oder guide (abwechselnd)
        for p in range(start + 2, start + pages):
            # Jede 4. Seite als "guide" (mit Slots)
            if (p - start) % 4 == 0:
                plan[p] = "guide"
            else:
                plan[p] = "story"
    
    return plan, total_pages

# Generiere LaTeX-Code für PagePlan
def generate_pageplan_latex(plan, total_pages):
    """Generiert LaTeX-Code für PagePlan"""
    lines = []
    lines.append("% ============================================================================")
    lines.append("% PagePlan: Template-Zuordnung für alle Seiten")
    lines.append(f"% Gesamt: {total_pages} Seiten ({total_pages//2} Doppelseiten)")
    lines.append("% ============================================================================")
    lines.append("")
    lines.append("% Setze Template pro Seite in Lua")
    lines.append("\\directlua{")
    lines.append("  local plan = rawget(_G, 'ZC_PLAN') or {}")
    lines.append("  plan.pages = {}")
    lines.append("")
    
    # Sortiere Seiten
    sorted_pages = sorted(plan.items())
    
    for page, template in sorted_pages:
        lines.append(f"  plan.pages[{page}] = '{template}'")
    
    lines.append("  _G.ZC_PLAN = plan")
    lines.append("}")
    lines.append("")
    
    return "\n".join(lines)

# Generiere Übersicht als Markdown
def generate_pageplan_overview(plan, total_pages, starts):
    """Generiert Markdown-Übersicht"""
    lines = []
    lines.append("# PagePlan Übersicht")
    lines.append("")
    lines.append(f"**Gesamt:** {total_pages} Seiten ({total_pages//2} Doppelseiten)")
    lines.append("")
    lines.append("| Seite | Kapitel | Template | Beschreibung |")
    lines.append("|-------|---------|----------|--------------|")
    
    for ch in range(14):
        start = starts[ch]
        pages = CHAPTER_PAGES[ch]
        
        for p in range(start, start + pages):
            template = plan.get(p, "story")
            if p == start:
                desc = "Opener (bleed)"
            elif p == start + 1:
                desc = "Opener Seite 2 (bleed)"
            elif template == "guide":
                desc = "Guide (mit Slots: Headline/Deck/Teaser/Pullquote/Factbox/Caption)"
            else:
                desc = "Story (Standard-Layout)"
            
            lines.append(f"| {p:3d} | {ch:2d} | {template:6s} | {desc} |")
    
    return "\n".join(lines)

def main():
    """Hauptfunktion"""
    plan, total_pages = create_pageplan()
    starts = calculate_page_starts()
    
    print(f"PagePlan erstellt: {total_pages} Seiten")
    print(f"Templates: bleed={sum(1 for t in plan.values() if t == 'bleed')}, "
          f"guide={sum(1 for t in plan.values() if t == 'guide')}, "
          f"story={sum(1 for t in plan.values() if t == 'story')}")
    
    # Generiere LaTeX
    latex_code = generate_pageplan_latex(plan, total_pages)
    output_file = Path("tex/pageplan_full.tex")
    output_file.write_text(latex_code, encoding='utf-8')
    print(f"LaTeX gespeichert: {output_file}")
    
    # Generiere Markdown-Übersicht
    md_code = generate_pageplan_overview(plan, total_pages, starts)
    output_file = Path("docs/PAGEPLAN_OVERVIEW.md")
    output_file.write_text(md_code, encoding='utf-8')
    print(f"Markdown gespeichert: {output_file}")

if __name__ == "__main__":
    main()

