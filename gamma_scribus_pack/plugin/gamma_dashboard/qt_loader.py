# -*- coding: utf-8 -*-
"""
QT-Binding Loader - Unterstützt PyQt5/6 und PySide2/6
"""
import sys

QT_BINDING = None
QtCore = None
QtGui = None
QtWidgets = None
QtNetwork = None


def load_qt():
    """
    Lädt QT-Bindings automatisch (PySide6, PyQt6, PySide2, PyQt5)
    Gibt (QtCore, QtGui, QtWidgets, QtNetwork, binding_name) zurück
    """
    global QT_BINDING, QtCore, QtGui, QtWidgets, QtNetwork
    
    if QT_BINDING:
        return QtCore, QtGui, QtWidgets, QtNetwork, QT_BINDING
    
    errors = []
    
    # Versuche verschiedene QT-Bindings
    for name in ('PySide6', 'PyQt6', 'PySide2', 'PyQt5'):
        try:
            if name == 'PySide6':
                from PySide6 import QtCore, QtGui, QtWidgets, QtNetwork
                QT_BINDING = 'PySide6'
            elif name == 'PyQt6':
                from PyQt6 import QtCore, QtGui, QtWidgets, QtNetwork
                QT_BINDING = 'PyQt6'
            elif name == 'PySide2':
                from PySide2 import QtCore, QtGui, QtWidgets, QtNetwork
                QT_BINDING = 'PySide2'
            elif name == 'PyQt5':
                from PyQt5 import QtCore, QtGui, QtWidgets, QtNetwork
                QT_BINDING = 'PyQt5'
            
            # Test-Import erfolgreich
            return QtCore, QtGui, QtWidgets, QtNetwork, QT_BINDING
            
        except ImportError as exc:
            errors.append(f'{name}: {exc}')
            continue
        except Exception as exc:
            errors.append(f'{name}: {exc}')
            continue
    
    # Kein QT-Binding gefunden
    error_msg = 'Keine QT-Bindings verfügbar.\n\nVersucht:\n'
    error_msg += '\n'.join(f'  • {e}' for e in errors)
    error_msg += '\n\nInstalliere PyQt5:\n'
    error_msg += '  python -m pip install PyQt5'
    raise ImportError(error_msg)


def get_qapplication():
    """Holt oder erstellt QApplication"""
    QtCore, QtGui, QtWidgets, _, _ = load_qt()
    
    app = QtWidgets.QApplication.instance()
    if app is None:
        # Versuche Scribus' Qt-Instanz zu finden
        # In Scribus sollte bereits eine Instanz existieren
        app = QtWidgets.QApplication(sys.argv)
    
    return app

