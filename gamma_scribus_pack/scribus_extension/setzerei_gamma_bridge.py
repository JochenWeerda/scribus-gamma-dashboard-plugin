# -*- coding: utf-8 -*-
import os
import sys
import subprocess

try:
    import scribus
except Exception:
    scribus = None

def _msg(t, s):
    if scribus:
        try:
            scribus.messageBox(t, s)
            return
        except Exception:
            pass
    print(f"[{t}] {s}")

def run():
    if scribus and not scribus.haveDoc():
        _msg("Setzerei Gamma Bridge", "Bitte zuerst das Scribus-Template (.sla) öffnen.")
        return

    gamma_export = os.environ.get("ZC_GAMMA_EXPORT_DIR", "").strip()
    project_dir = os.environ.get("ZC_PROJECT_DIR", "").strip()
    venv_py = os.environ.get("ZC_VENV_PY", "").strip()

    if not gamma_export or not os.path.exists(gamma_export):
        _msg("Setzerei Gamma Bridge", "ENV ZC_GAMMA_EXPORT_DIR fehlt oder ungültig.\n"
                                    "Setze es auf Gamma-Export ZIP oder Ordner.")
        return
    if not project_dir:
        _msg("Setzerei Gamma Bridge", "ENV ZC_PROJECT_DIR fehlt. Setze Projektordner.")
        return
    if not venv_py or not os.path.isfile(venv_py):
        _msg("Setzerei Gamma Bridge", "ENV ZC_VENV_PY fehlt/ungültig.\n"
                                    "Setze auf venv python.exe (mit opencv+pillow).")
        return

    tool_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tools"))
    pipeline_py = os.path.join(tool_dir, "pipeline.py")

    cmd = [venv_py, pipeline_py, "--gamma_export", gamma_export, "--project", project_dir, "--max_clusters", "3"]
    _msg("Setzerei Gamma Bridge", "Starte Pipeline:\n" + " ".join(cmd))
    try:
        subprocess.check_call(cmd, cwd=tool_dir)
    except Exception as e:
        _msg("Setzerei Gamma Bridge", f"Pipeline Fehler: {e}")
        return

    _msg("Setzerei Gamma Bridge", "Pipeline OK.\n\nJetzt:\n"
                                 "1) Stelle sicher, dass dein pptx_json ggf. gepatcht ist (json_patch_pptx.py).\n"
                                 "2) Starte anschließend dein setzerei_engine.py wie gewohnt (Script-Menü).")

if __name__ == "__main__":
    run()
