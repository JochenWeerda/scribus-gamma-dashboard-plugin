#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verbessert die Text-Extraktion: bessere Formatierung, weniger Zeilenumbrüche,
bessere Erkennung von Absätzen und Überschriften.
"""

import re
from pathlib import Path


def clean_text_for_latex(text):
    """Bereinigt Text für LaTeX - verbesserte Version"""
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
    
    # Entferne einzelne Zeilenumbrüche inmitten von Sätzen
    # (behalte nur Absatzumbrüche)
    lines = text.split('\n')
    cleaned_lines = []
    current_para = []
    
    for line in lines:
        line = line.strip()
        if not line:
            # Leere Zeile = Absatzende
            if current_para:
                cleaned_lines.append(' '.join(current_para))
                current_para = []
            cleaned_lines.append('')
        elif line.endswith('.') or line.endswith('!') or line.endswith('?') or line.endswith(':'):
            # Satzende = wahrscheinlich Absatzende
            current_para.append(line)
            cleaned_lines.append(' '.join(current_para))
            current_para = []
        elif len(line) < 50 and line.isupper():
            # Kurze Großbuchstaben-Zeile = wahrscheinlich Überschrift
            if current_para:
                cleaned_lines.append(' '.join(current_para))
                current_para = []
            cleaned_lines.append('')
            cleaned_lines.append(line)
            cleaned_lines.append('')
        else:
            # Normale Zeile = Teil eines Absatzes
            current_para.append(line)
    
    if current_para:
        cleaned_lines.append(' '.join(current_para))
    
    # Entferne mehrfache Leerzeilen
    result = '\n'.join(cleaned_lines)
    result = re.sub(r'\n{3,}', '\n\n', result)
    
    return result.strip()


def improve_chapter_layout(chapter_file):
    """Verbessert eine Kapitel-Layout-Datei"""
    if not chapter_file.exists():
        return False
    
    content = chapter_file.read_text(encoding='utf-8')
    lines = content.split('\n')
    improved_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Wenn Zeile mit LaTeX-Befehl beginnt, übernehme sie unverändert
        if line.strip().startswith('\\') or line.strip().startswith('%') or line.strip() == '':
            improved_lines.append(line)
            i += 1
            continue
        
        # Sammle Text-Zeilen, die wahrscheinlich Teil eines Absatzes sind
        # (nur wenn sie kurz sind und nicht mit Satzzeichen enden)
        text_block = []
        start_i = i
        
        while i < len(lines):
            current_line = lines[i].strip()
            
            # Stoppe bei LaTeX-Befehlen oder Kommentaren
            if current_line.startswith('\\') or current_line.startswith('%'):
                break
            
            # Stoppe bei leeren Zeilen (Absatzende)
            if not current_line:
                if text_block:
                    break
                i += 1
                continue
            
            # Wenn Zeile lang ist oder mit Satzzeichen endet, ist es wahrscheinlich ein Absatzende
            if len(current_line) > 60 or current_line.endswith(('.', '!', '?', ':', ';')):
                text_block.append(current_line)
                i += 1
                # Prüfe nächste Zeile - wenn leer oder LaTeX-Befehl, ist Absatz zu Ende
                if i < len(lines):
                    next_line = lines[i].strip()
                    if not next_line or next_line.startswith('\\') or next_line.startswith('%'):
                        break
                continue
            
            # Kurze Zeile ohne Satzzeichen = wahrscheinlich Teil eines Absatzes
            if len(current_line) <= 60:
                text_block.append(current_line)
                i += 1
            else:
                break
        
        # Verbessere Text-Block (nur wenn mehrere Zeilen)
        if len(text_block) > 1:
            # Verbinde Zeilen zu einem Absatz
            text = ' '.join(text_block)
            # Bereinige Sonderzeichen
            text = text.replace('>', '„').replace('<', '«')  # Anführungszeichen
            text = text.replace('3', '–')  # Bindestrich
            improved_lines.append(text)
            improved_lines.append('')
        elif text_block:
            # Einzelne Zeile - nur Sonderzeichen bereinigen
            text = text_block[0]
            text = text.replace('>', '„').replace('<', '«')
            text = text.replace('3', '–')
            improved_lines.append(text)
            improved_lines.append('')
        else:
            # Kein Text-Block gefunden, übernehme Original
            if start_i < len(lines):
                improved_lines.append(lines[start_i])
                i = start_i + 1
    
    # Speichere verbesserte Version
    chapter_file.write_text('\n'.join(improved_lines), encoding='utf-8')
    return True


def main():
    """Hauptfunktion"""
    # Finde Projektverzeichnis (wo dieses Script liegt)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    chapters_dir = project_root / "tex" / "chapters"
    
    print("Verbessere Text-Extraktion in Layout-Dateien...")
    print(f"Projektverzeichnis: {project_root}")
    print(f"Kapitel-Verzeichnis: {chapters_dir}")
    
    if not chapters_dir.exists():
        print(f"FEHLER: Verzeichnis {chapters_dir} nicht gefunden!")
        return
    
    for ch in range(14):
        ch_str = f"{ch:02d}"
        layout_file = chapters_dir / f"chapter{ch_str}_layout.tex"
        
        if layout_file.exists():
            print(f"  Kapitel {ch_str}...")
            if improve_chapter_layout(layout_file):
                print(f"    ✓ Verbessert")
            else:
                print(f"    ✗ Fehler")
        else:
            print(f"  Kapitel {ch_str}: Datei nicht gefunden")
    
    print("\n=== Fertig ===")


if __name__ == "__main__":
    main()

