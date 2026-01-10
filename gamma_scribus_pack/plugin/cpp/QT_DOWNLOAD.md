# Qt5 Open Source - Kostenloser Download

## Ja, es gibt eine kostenlose Version!

Qt ist unter zwei Lizenzen verfügbar:
1. **Open Source (LGPL/GPL)** - **KOSTENLOS** ✓
2. Commercial - Bezahlversion

Für das Gamma Dashboard Plugin benötigst du **nur die kostenlose Open Source Version**!

## Download der kostenlosen Qt Open Source Version

### Option 1: Direkter Download (Empfohlen)

1. Gehe zu: https://www.qt.io/download-open-source
2. Oder direkt: https://www.qt.io/download-open-source-software
3. Wähle: **Open Source** (nicht Commercial/Evaluation!)

### Option 2: Qt Online Installer (Kostenlos)

1. Download: https://www.qt.io/download-qt-installer
2. Installiere den Qt Online Installer
3. Beim Start wähle:
   - **"Open Source"** oder **"LGPL"** (nicht Commercial!)
   - Erstelle ein kostenloses Qt Account (optional, aber empfohlen)
4. Wähle während der Installation:
   - **Qt 5.15.2** (oder neuer)
   - **MSVC 2019 64-bit** oder **MSVC 2022 64-bit**
   - Standard-Pfad: `C:\Qt\5.15.2\msvc2019_64`

### Option 3: Archiv-Download (Direkt, ohne Installer)

1. Gehe zu: https://download.qt.io/archive/qt/5.15/5.15.2/
2. Lade herunter:
   - `qt-opensource-windows-x64-5.15.2.exe` (Online Installer)
   - Oder einzelne Komponenten aus `single/`

## Wichtig für Open Source

- Die Open Source Version ist **komplett kostenlos**
- Du musst NICHT das "Free Evaluation" Formular ausfüllen (das ist für Commercial)
- Die Open Source Version hat alle Features, die du brauchst
- Sie ist unter LGPL/GPL lizenziert (kostenlos für Open Source Projekte)

## Installation

Nach dem Download:
1. Führe den Installer aus
2. Wähle **"Open Source"** bei der Lizenz
3. Installiere Qt 5.15.2 mit MSVC 2019/2022 64-bit
4. Standard-Installationspfad: `C:\Qt\5.15.2\msvc2019_64`

## Nach der Installation

Teste Qt:
```powershell
& "C:\Qt\5.15.2\msvc2019_64\bin\qmake.exe" --version
```

Dann kompiliere das Plugin:
```powershell
cd "C:\Users\Jochen\Documents\Die verborgene Uhr Gottes\Gottes geheimer Zeitcode\gamma_scribus_pack\plugin\cpp"
.\quick_build.ps1 -CmakePath "C:\Development" -ScribusSourcePath "C:\Development\scribus-1.7" -QtPath "C:\Qt\5.15.2\msvc2019_64"
```

## Unterschied zwischen Open Source und Commercial

- **Open Source**: Kostenlos, LGPL/GPL Lizenz
- **Commercial**: Bezahlt, für proprietäre Software ohne Quellcode-Offenlegung
- **Evaluation**: 10-tägige Testversion der Commercial Version

Für dein Plugin reicht die **Open Source Version** vollkommen aus!

