# Visual Studio Toolset v143 nicht gefunden - Lösung

## Problem

Visual Studio 2022 Build Tools (Platform Toolset = "v143") wurden nicht gefunden.

**Fehlermeldung:**
```
Die Buildtools für Visual Studio 2022 (Plattformtoolset = "v143") wurden nicht gefunden.
```

## Ursache

Die Scribus.sln ist für Platform Toolset **v143** (Visual Studio 2022) konfiguriert, aber:
- Visual Studio 2022 ist nicht installiert, ODER
- Visual Studio 2022 Build Tools (C++ Desktop Development) sind nicht installiert

## Lösungen

### Lösung 1: Visual Studio 2022 Build Tools installieren (Empfohlen)

**Visual Studio 2022 Build Tools installieren:**

1. **Download:** https://visualstudio.microsoft.com/de/downloads/#build-tools-for-visual-studio-2022
2. **Installieren:** `vs_buildtools.exe` ausführen
3. **Workloads wählen:**
   - ✅ **"Desktop development with C++"** (enthält MSVC v143 Build Tools)
   - Optional: **"Windows 10/11 SDK"**
4. **Installation abschließen**
5. **Visual Studio neu starten**
6. **Scribus.sln erneut öffnen**

### Lösung 2: Visual Studio 2022 Community installieren (Alternative)

Falls du die vollständige IDE bevorzugst:

1. **Download:** https://visualstudio.microsoft.com/de/downloads/
2. **Visual Studio 2022 Community installieren**
3. **Workloads wählen:**
   - ✅ **"Desktop development with C++"**
4. **Installation abschließen**
5. **Scribus.sln in Visual Studio öffnen**

### Lösung 3: Toolset in Solution umstellen (Workaround)

Falls ein anderes Toolset installiert ist (z.B. v142 für VS 2019), kann die Solution umgestellt werden:

**⚠️ Warnung:** Dies kann Kompatibilitätsprobleme verursachen, da die Scribus-Libs-Kit für v143 gebaut wurde.

**Schritte:**
1. **Scribus.sln in Visual Studio öffnen**
2. **Rechtsklick auf Solution → Retarget Projects**
3. **Toolset wählen:** z.B. "v142" (Visual Studio 2019)
4. **OK**

**ODER manuell in .vcxproj-Dateien:**
- Suche nach: `<PlatformToolset>v143</PlatformToolset>`
- Ersetze mit: `<PlatformToolset>v142</PlatformToolset>` (oder verfügbares Toolset)

### Lösung 4: Toolset-Version prüfen (Diagnose)

Prüfe, welche Toolset-Versionen installiert sind:

**PowerShell:**
```powershell
# Prüfe VS 2022 Build Tools
Get-ChildItem "${env:ProgramFiles}\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC" -Directory

# ODER VS 2022 Community
Get-ChildItem "${env:ProgramFiles}\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC" -Directory
```

**Erwartete Ausgabe (v143):**
```
14.30.xxxxx  (v143 für VS 2022)
14.29.xxxxx  (v142 für VS 2019)
```

## Welche Lösung wählen?

### ✅ Empfohlen: Lösung 1 (Build Tools installieren)

**Vorteile:**
- ✅ Kompatibel mit Scribus-Libs-Kit (v143)
- ✅ Keine Source-Code-Änderungen nötig
- ✅ Minimaler Installationsaufwand (nur Build Tools)

**Nachteile:**
- ⚠️ Installation erforderlich (~3-4 GB)

### ⚠️ Alternative: Lösung 3 (Toolset umstellen)

**Vorteile:**
- ✅ Keine Installation nötig (falls VS 2019 vorhanden)

**Nachteile:**
- ❌ Mögliche Kompatibilitätsprobleme mit Scribus-Libs-Kit
- ❌ Scribus-Libs-Kit müsste für v142 neu gebaut werden

## Nächste Schritte (nach Installation)

1. **Visual Studio schließen**
2. **Visual Studio neu starten**
3. **Scribus.sln öffnen:** `C:\Development\scribus-1.7\win32\msvc2022\Scribus.sln`
4. **Configuration: Release, Platform: x64**
5. **Build → Build Solution**

## Überprüfung (nach Installation)

**Prüfe, ob v143 verfügbar ist:**

1. **Developer Command Prompt für VS 2022 öffnen**
2. **Führe aus:**
   ```cmd
   where cl
   ```
3. **Erwartete Ausgabe:** `C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.xx.xxxxx\bin\Hostx64\x64\cl.exe`

**ODER in Visual Studio:**
- **Project → Properties → General → Platform Toolset**
- Sollte **"v143"** anzeigen (oder verfügbare Version)

