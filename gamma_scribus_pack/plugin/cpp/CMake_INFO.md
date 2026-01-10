# CMake Installation - WICHTIG

## Problem
Die heruntergeladene ZIP-Datei (`cmake-4.2.1.zip`) enthält den **Quellcode** von CMake, nicht die kompilierte Version!

## Lösung

### Option 1: CMake Installer (Empfohlen)
Lade den vorkompilierten CMake-Installer herunter:

1. Gehe zu: https://cmake.org/download/
2. Wähle: **Windows x64 Installer** (nicht Source!)
3. Installiere nach: `C:\Program Files\CMake`
4. CMake wird automatisch zum PATH hinzugefügt

### Option 2: CMake Portable Binary
Lade die portable Version herunter:

1. Gehe zu: https://github.com/Kitware/CMake/releases/tag/v4.2.1
2. Lade herunter: `cmake-4.2.1-windows-x86_64.zip` (nicht Source!)
3. Extrahiere nach: `C:\Development\cmake-4.2.1`
4. CMake sollte dann hier sein: `C:\Development\cmake-4.2.1\bin\cmake.exe`

### Option 3: Chocolatey (schnellste Methode)
Falls Chocolatey installiert ist:

```powershell
choco install cmake -y
```

## Nach der Installation

Teste CMake:
```powershell
cmake --version
```

Oder gib den Pfad im Build-Script an:
```powershell
.\quick_build.ps1 -CmakePath "C:\Program Files\CMake"
```

## Aktueller Status
- ❌ Quellcode-ZIP extrahiert (muss kompiliert werden - zu komplex)
- ✅ Benötigt: Vorkompilierte CMake-Version

