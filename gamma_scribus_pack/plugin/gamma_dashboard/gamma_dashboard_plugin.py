# -*- coding: utf-8 -*-
"""
Gamma Dashboard Plugin - Python-Teil
Wird vom C++-Plugin aufgerufen
"""
import os
import sys
from pathlib import Path

# Pfade
PLUGIN_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(PLUGIN_DIR))

# QT-Loader
try:
    from qt_loader import load_qt, get_qapplication
    QtCore, QtGui, QtWidgets, QtNetwork, QT_BINDING = load_qt()
    QT_AVAILABLE = True
except ImportError as e:
    QT_AVAILABLE = False
    QT_BINDING = None
    print(f"QT nicht verfügbar: {e}")

# Dashboard-Widget
try:
    from qt_dashboard_widget import GammaDashboardWidget
    WIDGET_AVAILABLE = True
except ImportError as e:
    WIDGET_AVAILABLE = False
    print(f"Dashboard-Widget nicht verfügbar: {e}")

try:
    import scribus
    SCRIBUS_AVAILABLE = True
except ImportError:
    SCRIBUS_AVAILABLE = False
    scribus = None


class GammaDashboardPlugin:
    """Haupt-Plugin-Klasse"""
    
    def __init__(self):
        self.dialog = None
    
    def run(self):
        """Hauptfunktion"""
        if not QT_AVAILABLE:
            self._show_error_no_qt()
            return
        
        if not WIDGET_AVAILABLE:
            self._show_error_no_widget()
            return
        
        try:
            app = get_qapplication()
            
            # Prüfe ob Dialog bereits offen
            if self.dialog is not None:
                try:
                    if self.dialog.isVisible():
                        self.dialog.raise_()
                        self.dialog.activateWindow()
                        return
                except:
                    self.dialog = None
            
            # Erstelle Dialog
            self._create_dialog(app)
            
        except Exception as e:
            self._show_error(f"Fehler beim Erstellen des Dashboards:\n\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def _create_dialog(self, app):
        """Erstellt QT-Dialog"""
        self.dialog = QtWidgets.QDialog()
        self.dialog.setWindowTitle("Gamma Dashboard v1.0.0")
        self.dialog.setMinimumSize(600, 700)
        
        layout = QtWidgets.QVBoxLayout(self.dialog)
        
        dashboard = GammaDashboardWidget(PLUGIN_DIR, self.dialog)
        layout.addWidget(dashboard)
        
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QtWidgets.QPushButton("Schließen")
        close_btn.clicked.connect(self.dialog.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        self.dialog.setModal(False)
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()
    
    def _show_error_no_qt(self):
        msg = "QT-Bindings nicht verfügbar!"
        if SCRIBUS_AVAILABLE and scribus:
            try:
                scribus.messageBox("Gamma Dashboard", msg, icon=scribus.ICON_CRITICAL)
            except:
                print(f"[ERROR] {msg}")
        else:
            print(f"[ERROR] {msg}")
    
    def _show_error_no_widget(self):
        msg = "Dashboard-Widget konnte nicht geladen werden."
        if SCRIBUS_AVAILABLE and scribus:
            try:
                scribus.messageBox("Gamma Dashboard", msg, icon=scribus.ICON_CRITICAL)
            except:
                print(f"[ERROR] {msg}")
        else:
            print(f"[ERROR] {msg}")
    
    def _show_error(self, message):
        if SCRIBUS_AVAILABLE and scribus:
            try:
                scribus.messageBox("Gamma Dashboard", message, icon=scribus.ICON_CRITICAL)
            except:
                print(f"[ERROR] {message}")
        else:
            print(f"[ERROR] {message}")


def main():
    """Entry Point"""
    plugin = GammaDashboardPlugin()
    plugin.run()


if __name__ == "__main__":
    main()

