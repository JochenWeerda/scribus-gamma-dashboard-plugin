#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF zu LaTeX Konverter
Extrahiert Text, Struktur und Bilder aus PDFs und konvertiert sie in LaTeX
"""

import sys
import os
import re
from pathlib import Path

try:
    import PyPDF2
    from pdfminer.high_level import extract_text
    from pdfminer.layout import LTTextContainer, LTFigure, LTImage
except ImportError:
    print("Fehlende Abhängigkeiten. Installiere mit:")
    print("  pip install PyPDF2 pdfminer.six")
    sys.exit(1)

class PDFToLaTeXConverter:
    def __init__(self, pdf_path, output_dir, chapter_num):
        self.pdf_path = Path(pdf_path)
        self.output_dir = Path(output_dir)
        self.chapter_num = chapter_num
        self.ch_str = f"{chapter_num:02d}"
        
    def extract_text_from_pdf(self):
        """Extrahiert Text aus PDF"""
        try:
            text = extract_text(str(self.pdf_path))
            return text
        except Exception as e:
            print(f"Fehler beim Extrahieren von Text: {e}")
            return ""
    
    def analyze_structure(self, text):
        """Analysiert die Struktur des Textes"""
        lines = text.split('\n')
        structure = {
            'title': '',
            'sections': [],
            'current_section': None,
            'paragraphs': []
        }
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Erkenne Überschriften (GROSSBUCHSTABEN oder fett)
            if line.isupper() and len(line) > 5:
                if structure['current_section']:
                    structure['sections'].append(structure['current_section'])
                structure['current_section'] = {
                    'title': line,
                    'paragraphs': []
                }
            elif structure['current_section']:
                structure['current_section']['paragraphs'].append(line)
            else:
                structure['paragraphs'].append(line)
        
        if structure['current_section']:
            structure['sections'].append(structure['current_section'])
        
        return structure
    
    def convert_to_latex(self, structure):
        """Konvertiert Struktur zu LaTeX"""
        latex = []
        latex.append(f"% ============================================================================")
        latex.append(f"% Kapitel {self.ch_str}: {structure.get('title', 'Titel')}")
        latex.append(f"% Auto-generiert aus PDF")
        latex.append(f"% ============================================================================")
        latex.append(f"\\chapter{{{structure.get('title', 'Titel')}}}")
        latex.append("")
        
        # Hero-Bild (falls vorhanden)
        hero_path = f"ch{self.ch_str}_hero_creation.png"
        if (Path("assets/images/heroes/hires") / hero_path).exists():
            latex.append(f"% Chapter Opener Hero")
            latex.append(f"\\heroimg[hires]{{{hero_path}}}")
            latex.append("")
        
        # Einleitung
        if structure['paragraphs']:
            latex.append(f"% Einleitung")
            for para in structure['paragraphs'][:3]:  # Erste 3 Absätze
                latex.append(self.clean_text(para))
                latex.append("")
        
        # Sektionen
        for i, section in enumerate(structure['sections'], 1):
            latex.append(f"\\section{{{self.clean_text(section['title'])}}}")
            latex.append("")
            
            for para in section['paragraphs']:
                cleaned = self.clean_text(para)
                if cleaned:
                    latex.append(cleaned)
                    latex.append("")
            
            # Füge Figuren ein (basierend auf verfügbaren Assets)
            fig_num = i - 1
            fig_path = f"ch{self.ch_str}_vecfig_{fig_num:03d}.png"
            if (Path(f"assets/figures/ch{self.ch_str}/color_navy") / fig_path).exists():
                latex.append(f"% Vektorfigur")
                latex.append(f"\\vecfig{{{self.ch_str}}}{{{fig_path}}}")
                latex.append("")
        
        return "\n".join(latex)
    
    def clean_text(self, text):
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
        
        # Entferne mehrfache Leerzeichen
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def convert(self):
        """Hauptkonvertierungs-Funktion"""
        print(f"Konvertiere PDF: {self.pdf_path}")
        
        # Extrahiere Text
        text = self.extract_text_from_pdf()
        if not text:
            print("Kein Text gefunden!")
            return False
        
        # Analysiere Struktur
        structure = self.analyze_structure(text)
        
        # Konvertiere zu LaTeX
        latex_code = self.convert_to_latex(structure)
        
        # Speichere Ergebnis
        output_file = self.output_dir / f"chapter{self.ch_str}_auto.tex"
        output_file.write_text(latex_code, encoding='utf-8')
        
        print(f"LaTeX-Datei erstellt: {output_file}")
        return True

def main():
    if len(sys.argv) < 4:
        print("Verwendung: pdf_to_latex.py <pdf_path> <output_dir> <chapter_num>")
        print("Beispiel: pdf_to_latex.py chapter00.pdf tex/chapters 0")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    output_dir = sys.argv[2]
    chapter_num = int(sys.argv[3])
    
    converter = PDFToLaTeXConverter(pdf_path, output_dir, chapter_num)
    converter.convert()

if __name__ == "__main__":
    main()

