#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ersetzt Dummy-Bildflächen automatisch durch echte Bilder, sobald sie vorhanden sind.
Liest asset manifest und prüft, ob Bilder existieren.
"""

import re
from pathlib import Path
import csv


def load_asset_manifest():
    """Lädt asset manifest"""
    manifest_path = Path("assets/manifest_assets.csv")
    if not manifest_path.exists():
        return {}
    
    assets = {}
    with open(manifest_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            asset_id = row.get('asset_id', '').strip()
            if not asset_id or asset_id.startswith('#'):
                continue
            
            output_path = row.get('output_path_print', '').strip()
            if output_path:
                assets[asset_id] = {
                    'path': output_path,
                    'title': row.get('title', ''),
                    'description': row.get('description', ''),
                    'category': row.get('category', '')
                }
    
    return assets


def find_image_file(asset_path):
    """Prüft, ob Bild-Datei existiert"""
    # Versuche verschiedene Varianten
    base_path = Path(asset_path)
    
    # Original-Pfad
    if base_path.exists():
        return base_path
    
    # Relative zu tex/
    rel_path = Path("tex") / base_path
    if rel_path.exists():
        return rel_path
    
    # Relative zu Projekt-Root
    root_path = Path(".") / base_path
    if root_path.exists():
        return root_path
    
    return None


def replace_dummy_in_chapter(chapter_file, assets):
    """Ersetzt Dummy-Bilder in einer Kapitel-Datei"""
    if not chapter_file.exists():
        return False
    
    content = chapter_file.read_text(encoding='utf-8')
    modified = False
    
    # Finde alle Dummy-Boxen
    # Pattern: \ZCPlanSetPageSlot{...}{...}{% Dummy-Bild: ASSET_ID
    pattern = r'\\ZCPlanSetPageSlot\{(\d+)\}\{(\w+)\}\{%\s*Dummy-Bild:\s*(\w+)(.*?)\\end\{tcolorbox\}\}'
    
    def replace_match(match):
        nonlocal modified
        page = match.group(1)
        slot = match.group(2)
        asset_id = match.group(3)
        dummy_content = match.group(4)
        
        if asset_id in assets:
            asset = assets[asset_id]
            image_path = find_image_file(asset['path'])
            
            if image_path:
                # Ersetze durch echtes Bild
                modified = True
                if asset['category'] == 'hero':
                    return f"\\ZCPlanSetPageSlot{{{page}}}{{{slot}}}{{\\heroimg{{{image_path.name}}}}}"
                elif asset['category'] in ['infographic', 'map', 'diagram']:
                    return f"\\ZCPlanSetPageSlot{{{page}}}{{{slot}}}{{\\includegraphics[width=\\linewidth,keepaspectratio]{{{image_path}}}}}"
                else:
                    return f"\\ZCPlanSetPageSlot{{{page}}}{{{slot}}}{{\\includegraphics[width=\\linewidth,keepaspectratio]{{{image_path}}}}}"
        
        # Kein Ersatz möglich, behalte Dummy
        return match.group(0)
    
    new_content = re.sub(pattern, replace_match, content, flags=re.DOTALL)
    
    if modified:
        chapter_file.write_text(new_content, encoding='utf-8')
        return True
    
    return False


def main():
    """Hauptfunktion"""
    print("Ersetze Dummy-Bilder durch echte Bilder...")
    
    assets = load_asset_manifest()
    print(f"Geladen: {len(assets)} Assets")
    
    chapters_dir = Path("tex/chapters")
    replaced_count = 0
    
    for ch in range(14):
        ch_str = f"{ch:02d}"
        layout_file = chapters_dir / f"chapter{ch_str}_layout.tex"
        
        if layout_file.exists():
            print(f"  Kapitel {ch_str}...")
            if replace_dummy_in_chapter(layout_file, assets):
                print(f"    ✓ Bilder ersetzt")
                replaced_count += 1
            else:
                print(f"    - Keine Ersetzungen")
    
    print(f"\n=== Fertig ===")
    print(f"Ersetzt in {replaced_count} Kapiteln")


if __name__ == "__main__":
    main()

