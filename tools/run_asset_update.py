#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Führt Asset-Manifest-Aktualisierung aus.
"""

import sys
from pathlib import Path

# Füge tools-Verzeichnis zum Python-Pfad hinzu
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(script_dir))

# Importiere update_asset_manifest
from update_asset_manifest import update_manifest_status

def main():
    """Hauptfunktion"""
    import os
    os.chdir(project_root)
    
    print("Aktualisiere Asset-Manifest...")
    print(f"Projektverzeichnis: {project_root}")
    print()
    
    if update_manifest_status():
        print("\n=== Fertig ===")
        return True
    else:
        print("\n=== Fehler ===")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

