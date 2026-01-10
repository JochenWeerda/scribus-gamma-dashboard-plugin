# -*- coding: utf-8 -*-
"""
Gamma Dashboard QT-Widget - Vereinfachte Version
Native QT-GUI für Pipeline-Management
"""
import os
import json
import subprocess
import threading
from pathlib import Path
from typing import Optional

try:
    from qt_loader import load_qt, get_qapplication
    QtCore, QtGui, QtWidgets, QtNetwork, QT_BINDING = load_qt()
except ImportError as e:
    QtCore = QtGui = QtWidgets = None
    print(f"QT kann nicht geladen werden: {e}")


class PipelineRunner(QtCore.QThread if QtCore else object):
    """Pipeline-Runner Thread"""
    finished_signal = None
    
    def __init__(self, cmd, tools_dir, parent=None):
        if QtCore:
            super().__init__(parent)
        self.cmd = cmd
        self.tools_dir = tools_dir
        self.output = ""
        self.error = ""
        self.returncode = 0
        
        if QtCore and QT_BINDING:
            if QT_BINDING in ('PyQt5', 'PyQt6'):
                self.finished_signal = QtCore.pyqtSignal(bool, str, str)
            elif QT_BINDING in ('PySide2', 'PySide6'):
                self.finished_signal = QtCore.Signal(bool, str, str)
    
    def run(self):
        """Führt Pipeline aus"""
        try:
            result = subprocess.run(
                self.cmd,
                cwd=str(self.tools_dir),
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            self.returncode = result.returncode
            self.output = result.stdout
            self.error = result.stderr
            
            if self.finished_signal:
                self.finished_signal.emit(
                    result.returncode == 0,
                    result.stdout,
                    result.stderr
                )
        except Exception as e:
            self.error = str(e)
            if self.finished_signal:
                self.finished_signal.emit(False, "", str(e))


class GammaDashboardWidget(QtWidgets.QWidget if QtWidgets else object):
    """Haupt-Dashboard-Widget"""
    
    def __init__(self, plugin_dir: Path, parent=None):
        if QtWidgets:
            super().__init__(parent)
        
        self.plugin_dir = Path(plugin_dir)
        self.config_file = self.plugin_dir / "config.json"
        self.tools_dir = self.plugin_dir / "tools"
        self.config = {}
        self.pipeline_runner = None
        
        self._load_config()
        if QtWidgets:
            self._init_ui()
            self._load_config_into_ui()
    
    def _load_config(self):
        """Lädt Konfiguration"""
        default_config = {
            "project_dir": "",
            "gamma_export_dir": "",
            "venv_python": "",
            "max_clusters": 3,
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception:
                pass
        
        self.config = default_config
    
    def _save_config(self):
        """Speichert Konfiguration"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _init_ui(self):
        """Erstellt UI"""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Titel
        title_label = QtWidgets.QLabel("🎨 Gamma Dashboard")
        title_font = QtGui.QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Separator
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Konfiguration-Gruppe
        config_group = QtWidgets.QGroupBox("Konfiguration")
        config_layout = QtWidgets.QFormLayout()
        config_layout.setSpacing(8)
        
        # Projekt-Verzeichnis
        self.project_dir_edit = QtWidgets.QLineEdit()
        self.project_dir_edit.setPlaceholderText("C:\\Path\\To\\Project")
        project_browse_btn = QtWidgets.QPushButton("📁")
        project_browse_btn.setMaximumWidth(40)
        project_browse_btn.clicked.connect(lambda: self._browse_folder(self.project_dir_edit))
        project_layout = QtWidgets.QHBoxLayout()
        project_layout.addWidget(self.project_dir_edit)
        project_layout.addWidget(project_browse_btn)
        config_layout.addRow("Projekt-Verzeichnis:", project_layout)
        
        # Gamma Export
        self.gamma_export_edit = QtWidgets.QLineEdit()
        self.gamma_export_edit.setPlaceholderText("C:\\Path\\To\\Export.zip oder Ordner")
        gamma_browse_btn = QtWidgets.QPushButton("📁")
        gamma_browse_btn.setMaximumWidth(40)
        gamma_browse_btn.clicked.connect(lambda: self._browse_file_or_folder(self.gamma_export_edit))
        gamma_layout = QtWidgets.QHBoxLayout()
        gamma_layout.addWidget(self.gamma_export_edit)
        gamma_layout.addWidget(gamma_browse_btn)
        config_layout.addRow("Gamma Export:", gamma_layout)
        
        # Python venv
        self.venv_python_edit = QtWidgets.QLineEdit()
        self.venv_python_edit.setPlaceholderText("C:\\Path\\.venv\\Scripts\\python.exe")
        venv_browse_btn = QtWidgets.QPushButton("📁")
        venv_browse_btn.setMaximumWidth(40)
        venv_browse_btn.clicked.connect(lambda: self._browse_file(self.venv_python_edit, "Python Executable (*.exe)"))
        venv_layout = QtWidgets.QHBoxLayout()
        venv_layout.addWidget(self.venv_python_edit)
        venv_layout.addWidget(venv_browse_btn)
        config_layout.addRow("Python (venv):", venv_layout)
        
        # Max Clusters
        self.max_clusters_spin = QtWidgets.QSpinBox()
        self.max_clusters_spin.setMinimum(1)
        self.max_clusters_spin.setMaximum(10)
        self.max_clusters_spin.setValue(3)
        config_layout.addRow("Max. Cluster:", self.max_clusters_spin)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        self.save_config_btn = QtWidgets.QPushButton("💾 Konfiguration speichern")
        self.save_config_btn.clicked.connect(self._on_save_config)
        button_layout.addWidget(self.save_config_btn)
        
        self.run_pipeline_btn = QtWidgets.QPushButton("▶ Pipeline starten")
        self.run_pipeline_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.run_pipeline_btn.clicked.connect(self._on_run_pipeline)
        button_layout.addWidget(self.run_pipeline_btn)
        
        layout.addLayout(button_layout)
        
        # Status-Output
        output_group = QtWidgets.QGroupBox("Status")
        output_layout = QtWidgets.QVBoxLayout()
        
        self.status_label = QtWidgets.QLabel("Bereit")
        self.status_label.setWordWrap(True)
        output_layout.addWidget(self.status_label)
        
        self.output_text = QtWidgets.QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMaximumHeight(200)
        self.output_text.setFont(QtGui.QFont("Consolas", 9))
        output_layout.addWidget(self.output_text)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        layout.addStretch()
    
    def _load_config_into_ui(self):
        """Lädt Config in UI"""
        if not QtWidgets:
            return
        self.project_dir_edit.setText(self.config.get("project_dir", ""))
        self.gamma_export_edit.setText(self.config.get("gamma_export_dir", ""))
        self.venv_python_edit.setText(self.config.get("venv_python", ""))
        self.max_clusters_spin.setValue(self.config.get("max_clusters", 3))
    
    def _browse_folder(self, line_edit):
        if not QtWidgets:
            return
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Ordner auswählen",
            line_edit.text() or str(Path.home())
        )
        if folder:
            line_edit.setText(folder)
    
    def _browse_file(self, line_edit, filter=""):
        if not QtWidgets:
            return
        file, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Datei auswählen",
            line_edit.text() or str(Path.home()),
            filter
        )
        if file:
            line_edit.setText(file)
    
    def _browse_file_or_folder(self, line_edit):
        if not QtWidgets:
            return
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Gamma Export (Datei oder Ordner)",
            line_edit.text() or str(Path.home())
        )
        if folder:
            line_edit.setText(folder)
        else:
            file, _ = QtWidgets.QFileDialog.getOpenFileName(
                self,
                "Gamma Export (ZIP oder Ordner)",
                line_edit.text() or str(Path.home()),
                "ZIP-Dateien (*.zip);;Alle Dateien (*.*)"
            )
            if file:
                line_edit.setText(file)
    
    def _on_save_config(self):
        """Speichert Konfiguration"""
        if not QtWidgets:
            return
        self.config["project_dir"] = self.project_dir_edit.text()
        self.config["gamma_export_dir"] = self.gamma_export_edit.text()
        self.config["venv_python"] = self.venv_python_edit.text()
        self.config["max_clusters"] = self.max_clusters_spin.value()
        
        self._save_config()
        self.status_label.setText("✅ Konfiguration gespeichert!")
        self.status_label.setStyleSheet("color: green;")
    
    def _on_run_pipeline(self):
        """Startet Pipeline"""
        if not QtWidgets:
            return
        
        project_dir = self.project_dir_edit.text().strip()
        gamma_export = self.gamma_export_edit.text().strip()
        venv_python = self.venv_python_edit.text().strip()
        
        if not project_dir:
            QtWidgets.QMessageBox.warning(self, "Fehler", "Projekt-Verzeichnis fehlt!")
            return
        
        if not gamma_export:
            QtWidgets.QMessageBox.warning(self, "Fehler", "Gamma Export fehlt!")
            return
        
        if not os.path.exists(gamma_export):
            QtWidgets.QMessageBox.warning(self, "Fehler", f"Gamma Export existiert nicht:\n{gamma_export}")
            return
        
        if not venv_python:
            QtWidgets.QMessageBox.warning(self, "Fehler", "Python (venv) fehlt!")
            return
        
        if not os.path.isfile(venv_python):
            QtWidgets.QMessageBox.warning(self, "Fehler", f"Python-Datei existiert nicht:\n{venv_python}")
            return
        
        self._on_save_config()
        
        cmd = [
            venv_python,
            str(self.tools_dir / "pipeline.py"),
            "--gamma_export", gamma_export,
            "--project", project_dir,
            "--max_clusters", str(self.max_clusters_spin.value()),
        ]
        
        self.run_pipeline_btn.setEnabled(False)
        self.status_label.setText("🔄 Pipeline läuft...")
        self.status_label.setStyleSheet("color: blue;")
        self.output_text.clear()
        self.output_text.append("Pipeline gestartet...\n")
        self.output_text.append(f"Command: {' '.join(cmd)}\n\n")
        
        self.pipeline_runner = PipelineRunner(cmd, self.tools_dir, self)
        
        if self.pipeline_runner.finished_signal:
            self.pipeline_runner.finished_signal.connect(self._on_pipeline_finished)
        
        self.pipeline_runner.start()
    
    def _on_pipeline_finished(self, success, stdout, stderr):
        """Pipeline-Finished Callback"""
        if not QtWidgets:
            return
        
        self.run_pipeline_btn.setEnabled(True)
        
        if success:
            self.status_label.setText("✅ Pipeline erfolgreich abgeschlossen!")
            self.status_label.setStyleSheet("color: green;")
            self.output_text.append("\n✅ Erfolg!\n\n")
            self.output_text.append(stdout)
        else:
            self.status_label.setText("❌ Pipeline fehlgeschlagen!")
            self.status_label.setStyleSheet("color: red;")
            self.output_text.append("\n❌ Fehler!\n\n")
            if stderr:
                self.output_text.append("STDERR:\n" + stderr + "\n\n")
            if stdout:
                self.output_text.append("STDOUT:\n" + stdout)
        
        scrollbar = self.output_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

