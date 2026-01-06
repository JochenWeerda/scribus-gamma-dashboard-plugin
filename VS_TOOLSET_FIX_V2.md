# Visual Studio Toolset v143 - Toolset ist installiert, wird aber nicht erkannt

## Status

✅ **Visual Studio 2022 Build Tools sind installiert!**
- Installation: `C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools`
- MSVC Toolset: Version 14.44.35207 (neuere Version als v143)

❌ **Problem:** Visual Studio erkennt das Toolset nicht beim Öffnen der Solution

## Ursache

Das Toolset ist installiert, aber Visual Studio erkennt es möglicherweise nicht, wenn:
- Die Solution über den Datei-Explorer geöffnet wird (nicht über Visual Studio)
- Visual Studio wurde nicht als Administrator gestartet
- Die Build Tools-Installation ist unvollständig

## Lösungen

### Lösung 1: Visual Studio IDE verwenden (Empfohlen)

**Schritte:**

1. **Visual Studio 2022 Build Tools starten:**
   - Windows Start-Menü → "Visual Studio 2022" (oder Developer Command Prompt)
   - ODER: `"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\devenv.exe"`

2. **In Visual Studio:**
   - **File → Open → Project/Solution...**
   - Navigiere zu: `C:\Development\scribus-1.7\win32\msvc2022\Scribus.sln`
   - **Öffnen**

3. **Wenn Toolset-Fehler erscheint:**
   - **Project → Retarget Projects** (wenn angeboten)
   - Wähle: **"v143"** oder **"Latest"**

4. **Build → Build Solution**

### Lösung 2: Developer Command Prompt verwenden

**Schritte:**

1. **Developer Command Prompt für VS 2022 öffnen:**
   - Windows Start-Menü → "Developer Command Prompt for VS 2022"
   - ODER: `"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat"`

2. **In Command Prompt:**
   ```cmd
   cd C:\Development\scribus-1.7\win32\msvc2022
   msbuild Scribus.sln /p:Configuration=Release /p:Platform=x64 /t:Build
   ```

3. **Wenn Toolset-Fehler:**
   - MSBuild sollte automatisch das neueste Toolset verwenden
   - Oder explizit angeben: `/p:PlatformToolset=v143`

### Lösung 3: Toolset in Solution auf "Latest" umstellen

**Schritte:**

1. **Scribus.sln in Visual Studio öffnen**
2. **Rechtsklick auf Solution → Properties**
3. **Configuration Properties → General**
4. **Platform Toolset:** Ändere von `v143` zu **"Latest"** (oder lasse leer)
5. **OK → Build**

### Lösung 4: Build Tools-Installation prüfen (Falls Problem weiterhin besteht)

**Prüfe, ob C++ Build Tools installiert sind:**

1. **Visual Studio Installer öffnen:**
   - Windows Start-Menü → "Visual Studio Installer"
   - ODER: `"C:\Program Files (x86)\Microsoft Visual Studio\Installer\setup.exe"`

2. **Modify (Ändern) klicken**
3. **Prüfe Workloads:**
   - ✅ **"Desktop development with C++"** muss aktiviert sein
   - ✅ **"MSVC v143 - VS 2022 C++ x64/x86 build tools"** muss aktiviert sein
   - ✅ **"Windows 10/11 SDK"** sollte aktiviert sein

4. **Falls fehlend:**
   - Aktiviere die Workloads
   - **Modify** klicken
   - Warten auf Installation

5. **Visual Studio neu starten**

## Empfohlener Workflow

1. ✅ **Visual Studio Installer prüfen** (Lösung 4)
2. ✅ **Visual Studio IDE öffnen** (Lösung 1)
3. ✅ **Scribus.sln öffnen**
4. ✅ **Wenn Toolset-Fehler → Retarget Projects**
5. ✅ **Build → Build Solution**

## Überprüfung

**Prüfe, ob Toolset verfügbar ist:**

**PowerShell:**
```powershell
# Prüfe MSVC Tools
Get-ChildItem "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC" -Directory

# Erwartete Ausgabe:
# 14.44.35207  (oder ähnliche Version)
```

**Developer Command Prompt:**
```cmd
where cl
# Erwartete Ausgabe:
# C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.xx.xxxxx\bin\Hostx64\x64\cl.exe
```

## Hinweis: Toolset-Versionen

- **v143** = Visual Studio 2022 (MSVC 14.30.x)
- **Version 14.44.35207** = Neuere Version, kompatibel mit v143-Projekten
- Visual Studio sollte automatisch die kompatible Version verwenden

