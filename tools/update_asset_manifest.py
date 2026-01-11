#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aktualisiert das Asset-Manifest basierend auf tatsächlich vorhandenen Dateien.
"""

import csv
from pathlib import Path
import re


def find_asset_files(asset_path):
    """Prüft, ob Asset-Datei existiert"""
    if not asset_path or not asset_path.strip():
        return False, None
    
    base_path = Path(asset_path.strip())
    
    # Prüfe verschiedene mögliche Pfade
    paths_to_check = [
        base_path,  # Original-Pfad
        Path("tex") / base_path,  # Relativ zu tex/
        Path(".") / base_path,  # Relativ zum Root
    ]
    
    # Wenn Pfad mit assets/ beginnt, prüfe auch direkt
    if str(base_path).startswith("assets/"):
        paths_to_check.insert(0, base_path)
    
    for path in paths_to_check:
        if path.exists() and path.is_file():
            return True, str(path.resolve())
    
    return False, None


def update_manifest_status():
    """Aktualisiert Status-Spalte im Manifest"""
    manifest_path = Path("assets/manifest_assets.csv")
    
    if not manifest_path.exists():
        print(f"FEHLER: {manifest_path} nicht gefunden!")
        return False
    
    # Lade Manifest
    rows = []
    with open(manifest_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)
    
    # Prüfe jeden Asset
    updated_count = 0
    for row in rows:
        asset_id = row.get('asset_id', '').strip()
        if not asset_id or asset_id.startswith('#'):
            continue
        
        output_path = row.get('output_path_print', '').strip()
        if not output_path:
            continue
        
        # Prüfe, ob Datei existiert
        exists, found_path = find_asset_files(output_path)
        
        if exists:
            old_status = row.get('status', '').strip()
            if old_status != 'created':
                row['status'] = 'created'
                row['notes'] = f"Gefunden: {found_path}"
                updated_count += 1
                print(f"  ✓ {asset_id}: {found_path}")
    
    # Speichere aktualisiertes Manifest
    if updated_count > 0:
        with open(manifest_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"\n✓ {updated_count} Assets als 'created' markiert")
    else:
        print("\n✓ Keine Änderungen nötig")
    
    return True


def main():
    """Hauptfunktion"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    print("Aktualisiere Asset-Manifest...")
    print(f"Projektverzeichnis: {project_root}")
    
    # Wechsle zum Projektverzeichnis
    import os
    os.chdir(project_root)
    
    if update_manifest_status():
        print("\n=== Fertig ===")
    else:
        print("\n=== Fehler ===")


if __name__ == "__main__":
    main()

