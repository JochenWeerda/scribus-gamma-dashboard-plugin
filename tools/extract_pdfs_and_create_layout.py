#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extrahiert Text aus allen 14 PDFs und erstellt vollständiges Layout
für alle 130 Seiten mit Dummy-Bildflächen (Prompts/Beschreibungen).
"""

import sys
import re
from pathlib import Path

try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False
    print("Warnung: PyMuPDF nicht installiert. Installiere mit: pip install PyMuPDF")

try:
    from pdfminer.high_level import extract_text
    HAS_PDFMINER = True
except ImportError:
    HAS_PDFMINER = False
    print("Warnung: pdfminer.six nicht installiert. Installiere mit: pip install pdfminer.six")


def find_pdf_dir():
    """Findet den PDF-Ordner"""
    root = Path.home() / 'Documents'
    pdf_dir = next((d for d in root.rglob('PDFs DIN a4') if d.is_dir()), None)
    if pdf_dir is None:
        raise FileNotFoundError("PDFs DIN a4 Ordner nicht gefunden")
    return pdf_dir


def extract_text_from_pdf(pdf_path):
    """Extrahiert Text aus PDF (versucht mehrere Methoden)"""
    text = ""
    
    # Versuche pdfminer zuerst (besser für Layout)
    if HAS_PDFMINER:
        try:
            text = extract_text(str(pdf_path))
            if text.strip():
                return text
        except Exception as e:
            print(f"  pdfminer Fehler: {e}")
    
    # Fallback zu PyMuPDF
    if HAS_FITZ:
        try:
            doc = fitz.open(str(pdf_path))
            text = ""
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
            if text.strip():
                return text
        except Exception as e:
            print(f"  PyMuPDF Fehler: {e}")
    
    return ""


def clean_text_for_latex(text):
    """Bereinigt Text für LaTeX"""
    # Entferne Sonderzeichen, die LaTeX-Probleme verursachen
    text = text.replace('\\', '\\textbackslash{}')
    text = text.replace('{', '\\{')
    text = text.replace('}', '\\}')
    text = text.replace('$', '\\$')
    text = text.replace('&', '\\&')
    text = text.replace('%', '\\%')
    text = text.replace('#', '\\#')
    text = text.replace('^', '\\textasciicircum{}')
    text = text.replace('_', '\\_')
    text = text.replace('~', '\\textasciitilde{}')
    
    # Entferne mehrfache Leerzeichen/Zeilenumbrüche
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' +', ' ', text)
    
    return text.strip()


def parse_chapter_structure(text):
    """Erkennt Überschriften und Absätze"""
    lines = text.split('\n')
    structure = []
    current_para = []
    
    for line in lines:
        line = line.strip()
        if not line:
            if current_para:
                structure.append(('para', ' '.join(current_para)))
                current_para = []
            continue
        
        # Große Überschrift (GROSSBUCHSTABEN oder sehr lang)
        if line.isupper() and len(line) > 10:
            if current_para:
                structure.append(('para', ' '.join(current_para)))
                current_para = []
            structure.append(('heading', line))
        # Kleine Überschrift (fett oder kurz)
        elif len(line) < 80 and (line.endswith(':') or line.isupper()):
            if current_para:
                structure.append(('para', ' '.join(current_para)))
                current_para = []
            structure.append(('subheading', line))
        else:
            current_para.append(line)
    
    if current_para:
        structure.append(('para', ' '.join(current_para)))
    
    return structure


def load_asset_manifest():
    """Lädt asset manifest und erstellt Mapping Kapitel -> Assets"""
    manifest_path = Path("assets/manifest_assets.csv")
    if not manifest_path.exists():
        return {}
    
    assets_by_chapter = {}
    with open(manifest_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines[1:]:  # Skip header
            if not line.strip() or line.startswith('#'):
                continue
            parts = [p.strip() for p in line.split(',')]
            if len(parts) < 2:
                continue
            asset_id = parts[0]
            chapter_str = parts[1]
            if chapter_str.isdigit():
                ch = int(chapter_str)
                if ch not in assets_by_chapter:
                    assets_by_chapter[ch] = []
                category = parts[4] if len(parts) > 4 else 'unknown'
                title = parts[5] if len(parts) > 5 else asset_id
                description = parts[6] if len(parts) > 6 else ''
                prompt = parts[16] if len(parts) > 16 else description
                assets_by_chapter[ch].append({
                    'id': asset_id,
                    'category': category,
                    'title': title,
                    'description': description,
                    'prompt': prompt
                })
    
    return assets_by_chapter


def create_dummy_image_box(asset, page_num, slot_name):
    """Erstellt LaTeX-Code für Dummy-Bildfläche mit Beschreibung"""
    desc = asset.get('description', asset.get('title', asset['id']))
    prompt = asset.get('prompt', '')
    
    # Kürze Prompt für Anzeige
    if prompt and len(prompt) > 200:
        prompt_short = prompt[:197] + "..."
    else:
        prompt_short = prompt
    
    latex = f"""% Dummy-Bild: {asset['id']}
\\begin{{tcolorbox}}[
    colback=printGray!10,
    colframe=printGray!30,
    boxrule=0.5pt,
    arc=2pt,
    left=4pt,
    right=4pt,
    top=4pt,
    bottom=4pt,
    width=\\linewidth
]
\\small\\sffamily
\\textbf{{{asset['title']}}}\\\\
\\medskip
\\textit{{{desc}}}\\\\
\\medskip
\\footnotesize
\\color{{printGray}}
[\\texttt{{{asset['id']}}}]\\\\
\\vspace{{0.5em}}
\\begin{{minipage}}{{\\linewidth}}
\\tiny
{prompt_short}
\\end{{minipage}}
\\end{{tcolorbox}}"""
    
    return latex


def generate_chapter_latex(chapter_num, title, structure, assets, page_start):
    """Generiert LaTeX-Code für ein Kapitel mit Layout"""
    ch_str = f"{chapter_num:02d}"
    
    # Akt-Zuordnung
    if chapter_num <= 2:
        act = "I"
        act_name = "Ursprung/Licht"
    elif chapter_num <= 7:
        act = "II"
        act_name = "Drama/Stein/Gold"
    else:
        act = "III"
        act_name = "Finale/Licht + Tech"
    
    latex = []
    latex.append(f"% =============================================================")
    latex.append(f"% Kapitel {ch_str} – {title}")
    latex.append(f"% Akt {act}: {act_name}")
    latex.append(f"% =============================================================")
    latex.append("")
    
    # Print-Mode: Full-Bleed Opener + Sidebar
    latex.append("\\ifprintmode")
    latex.append(f"% Full-Bleed Opener (Seiten {page_start}-{page_start+1})")
    
    # Hero-Bild für Opener
    hero_assets = [a for a in assets if a['category'] == 'hero']
    if hero_assets:
        hero = hero_assets[0]
        latex.append(f"\\ZCPlanSetPageSlot{{{page_start}}}{{hero}}{{{create_dummy_image_box(hero, page_start, 'hero')}}}")
    
    # Sidebar-Content
    latex.append(f"\\ZCSidebarSetForChapter{{{chapter_num}}}{{%")
    latex.append(f"  \\textbf{{Kapitel {chapter_num}: {title}}}\\\\")
    latex.append(f"  \\small")
    latex.append(f"  \\textbf{{Akt {act}:}} {act_name}\\\\")
    latex.append(f"  \\medskip")
    latex.append(f"  \\textbf{{Assets:}} {len(assets)} Bilder/Infografiken\\\\")
    latex.append("}%")
    latex.append("\\fi")
    latex.append("")
    
    # Chapter-Command
    latex.append(f"\\chapter{{{title}}}")
    latex.append("")
    
    # Text-Struktur mit Bild-Platzhaltern
    current_page = page_start + 2  # Nach Opener
    asset_index = 0
    
    for i, (elem_type, content) in enumerate(structure):
        if elem_type == 'heading':
            latex.append(f"\\section*{{{content}}}")
            latex.append("")
        elif elem_type == 'subheading':
            latex.append(f"\\subsection*{{{content}}}")
            latex.append("")
        elif elem_type == 'para':
            # Text einfügen
            cleaned = clean_text_for_latex(content)
            latex.append(cleaned)
            latex.append("")
            
            # Alle 2-3 Absätze ein Bild einfügen (wenn verfügbar)
            if (i % 3 == 2 or i == len(structure) - 1) and asset_index < len(assets):
                asset = assets[asset_index]
                asset_index += 1
                
                # Bestimme Slot basierend auf Asset-Kategorie
                if asset['category'] == 'hero':
                    slot = 'hero'
                elif asset['category'] == 'infographic':
                    slot = 'factbox'
                elif asset['category'] == 'map':
                    slot = 'factbox'
                elif asset['category'] == 'detail':
                    slot = 'caption'
                else:
                    slot = 'factbox'
                
                latex.append("\\ifprintmode")
                latex.append(f"% Bild-Platzhalter auf Seite ~{current_page}")
                latex.append(f"\\ZCPlanSetPageSlot{{{current_page}}}{{{slot}}}{{{create_dummy_image_box(asset, current_page, slot)}}}")
                latex.append("\\else")
                # Digital: normales Bild
                latex.append(f"% TODO: Bild einfügen: {asset['id']}")
                latex.append(f"\\begin{{KeyBox}}")
                latex.append(f"\\textbf{{{asset['title']}}}\\\\")
                latex.append(f"\\textit{{{asset.get('description', '')}}}")
                latex.append(f"\\end{{KeyBox}}")
                latex.append("\\fi")
                latex.append("")
                
                current_page += 1
    
    return "\n".join(latex), current_page


def main():
    """Hauptfunktion"""
    pdf_dir = find_pdf_dir()
    output_dir = Path("tex/chapters")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Lade Asset-Manifest
    assets_by_chapter = load_asset_manifest()
    print(f"Geladen: {len(assets_by_chapter)} Kapitel mit Assets")
    
    # Kapitel-Titel
    titles = {
        0: "Gottes erste Uhr: die Schöpfung",
        1: "Wenn der Schleier fällt",
        2: "Daniels Gebet, shuv und die 70 Jahrwochen",
        3: "Antiochus, Makkabäer und der Greuel",
        4: "Entzeit: Rede der Greuel, Jerusalem und wir",
        5: "Mensch der Gesetzlosigkeit, das Tier und der Endzeit-Greuel",
        6: "Die verborgene Uhr Gottes: Das Drama der Zeit",
        7: "Die verborgene Uhr Gottes: Daniel, Jerusalem und das Drama der Zeit",
        8: "Offenbarung 21-22: Das neue Jerusalem und die vollendete Zeit",
        9: "Tempel meines Herzens",
        10: "Alles zusammenführen: Israel, Gemeinde, du",
        11: "Wenn der Schleier fällt",
        12: "Wenn die Uhr schlägt",
        13: "Die letzte Beschleunigung"
    }
    
    # Seitenzahlen (Start pro Kapitel)
    page_starts = {
        0: 1,   # Opener
        1: 11,  # 10 Seiten vorher
        2: 24,  # 13 Seiten vorher
        3: 34,  # 10 Seiten vorher
        4: 44,
        5: 54,
        6: 64,
        7: 74,
        8: 84,
        9: 94,
        10: 104,
        11: 114,
        12: 127,  # 13 Seiten vorher
        13: 137   # 10 Seiten vorher
    }
    
    total_pages = 0
    
    # Verarbeite alle Kapitel
    for ch in range(14):
        ch_str = f"{ch:02d}"
        
        # Finde PDF-Datei (versuche verschiedene Patterns)
        pdf_files = list(pdf_dir.glob(f"{ch}-*.pdf"))
        if not pdf_files:
            # Versuche auch mit Punkt (z.B. "4.Entzeit...")
            pdf_files = list(pdf_dir.glob(f"{ch}.*.pdf"))
        if not pdf_files:
            print(f"Warnung: Keine PDF für Kapitel {ch} gefunden")
            continue
        
        pdf_path = pdf_files[0]
        print(f"\nKapitel {ch_str}: {pdf_path.name}")
        
        # Extrahiere Text
        text = extract_text_from_pdf(pdf_path)
        if not text:
            print(f"  Fehler: Kein Text extrahiert")
            continue
        
        print(f"  Text extrahiert: {len(text)} Zeichen")
        
        # Parse Struktur
        structure = parse_chapter_structure(text)
        print(f"  Struktur: {len(structure)} Elemente")
        
        # Assets für dieses Kapitel
        assets = assets_by_chapter.get(ch, [])
        print(f"  Assets: {len(assets)}")
        
        # Generiere LaTeX
        title = titles.get(ch, f"Kapitel {ch_str}")
        page_start = page_starts.get(ch, ch * 10 + 1)
        
        latex_code, last_page = generate_chapter_latex(ch, title, structure, assets, page_start)
        
        # Speichere
        output_file = output_dir / f"chapter{ch_str}_layout.tex"
        output_file.write_text(latex_code, encoding='utf-8')
        print(f"  Gespeichert: {output_file}")
        print(f"  Seiten: {page_start} - {last_page}")
        
        total_pages = max(total_pages, last_page)
    
    print(f"\n=== Fertig ===")
    print(f"Gesamt: ~{total_pages} Seiten")
    print(f"Output: {output_dir}")
    print(f"\nNächste Schritte:")
    print(f"1. Prüfe die generierten chapter*_layout.tex Dateien")
    print(f"2. Passe PagePlan in tex/pageplan.tex an")
    print(f"3. Kompiliere mit compile_pdfs.ps1")


if __name__ == "__main__":
    main()

