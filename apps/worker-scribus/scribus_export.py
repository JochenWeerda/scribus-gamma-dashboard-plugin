"""Scribus Export Script - Wird von Scribus Python API aufgerufen."""

import sys
import os
import json


def export_sla(sla_path: str, output_dir: str, job_id: str):
    """
    Exportiert SLA-Datei zu PNG (72 DPI) und PDF (300 DPI).
    Wird von Scribus Python API aufgerufen.
    
    Args:
        sla_path: Pfad zur SLA-Datei
        output_dir: Ausgabe-Verzeichnis
        job_id: Job-ID für Dateinamen
    """
    try:
        import scribus
        
        # Dokument laden
        if not scribus.haveDoc():
            scribus.openDoc(sla_path)
        
        page_count = scribus.pageCount()
        
        # PNG-Export (72 DPI) pro Seite
        png_paths = []
        for page_num in range(1, page_count + 1):
            scribus.gotoPage(page_num)
            png_path = os.path.join(output_dir, f"preview_{job_id}_p{page_num:04d}.png")
            scribus.exportPageAsPNG(png_path, page_num, dpi=72)
            png_paths.append(png_path)
        
        # PDF-Export (300 DPI, CMYK)
        pdf_path = os.path.join(output_dir, f"output_{job_id}.pdf")
        scribus.saveDocAsPDF(
            pdf_path,
            pages=[i for i in range(1, page_count + 1)],
            dpi=300,
            colorspace=1,  # CMYK
            quality=2,  # High quality
        )
        
        result = {
            "success": True,
            "pdf_path": pdf_path,
            "png_paths": png_paths,
            "page_count": page_count,
        }
        
        # Ergebnis als JSON ausgeben
        print(json.dumps(result))
        return result
    
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
        }
        print(json.dumps(error_result))
        raise


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(json.dumps({"success": False, "error": "Usage: export_sla.py <sla_path> <output_dir> <job_id>"}))
        sys.exit(1)
    
    sla_path = sys.argv[1]
    output_dir = sys.argv[2]
    job_id = sys.argv[3]
    
    export_sla(sla_path, output_dir, job_id)

