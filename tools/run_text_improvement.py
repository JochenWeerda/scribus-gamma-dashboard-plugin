#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Führt Text-Verbesserung für alle Kapitel aus.
"""

import sys
from pathlib import Path

# Füge tools-Verzeichnis zum Python-Pfad hinzu
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(script_dir))

# Importiere improve_text_extraction
from improve_text_extraction import improve_chapter_layout

def main():
    """Hauptfunktion"""
    chapters_dir = project_root / "tex" / "chapters"
    
    print("Verbessere Text-Extraktion in allen Layout-Dateien...")
    print(f"Projektverzeichnis: {project_root}")
    print(f"Kapitel-Verzeichnis: {chapters_dir}")
    print()
    
    if not chapters_dir.exists():
        print(f"FEHLER: Verzeichnis {chapters_dir} nicht gefunden!")
        return False
    
    success_count = 0
    error_count = 0
    
    for ch in range(14):
        ch_str = f"{ch:02d}"
        layout_file = chapters_dir / f"chapter{ch_str}_layout.tex"
        
        if layout_file.exists():
            print(f"Kapitel {ch_str}...", end=" ")
            try:
                if improve_chapter_layout(layout_file):
                    print("✓")
                    success_count += 1
                else:
                    print("✗ Fehler")
                    error_count += 1
            except Exception as e:
                print(f"✗ Exception: {e}")
                error_count += 1
        else:
            print(f"Kapitel {ch_str}: Datei nicht gefunden")
            error_count += 1
    
    print()
    print("=" * 50)
    print(f"Erfolgreich: {success_count}")
    print(f"Fehler: {error_count}")
    print("=" * 50)
    
    return error_count == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

