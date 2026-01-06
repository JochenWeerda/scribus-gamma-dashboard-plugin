# CMake-Konfiguration für Scribus

## Status

✅ **Scribus-Libs-Kit erfolgreich gebaut!** (Alle 25 Projekte, Release, x64)

## CMake konfigurieren

CMake findet Visual Studio manchmal nicht automatisch. Verwende eine der folgenden Methoden:

### Methode 1: Developer Command Prompt (Empfohlen)

1. **Öffne "Developer Command Prompt for VS 2022"**
   - Start-Menü → "Developer Command Prompt for VS 2022"

2. **Wechsle ins Build-Verzeichnis:**
   ```cmd
   cd C:\Development\scribus-1.7\build
   ```

3. **Lösche alten CMake-Cache (falls vorhanden):**
   ```cmd
   del CMakeCache.txt
   rmdir /s /q CMakeFiles
   ```

4. **Konfiguriere CMake:**
   ```cmd
   cmake .. -G "Visual Studio 17 2022" -A x64 ^
     -DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreadedDLL ^
     -DLIBPODOFO_SHARED=1 ^
     -DSCRIBUS_LIBS_DIR=C:\Development\scribus-1.7.x-libs-msvc
   ```

5. **Prüfe, ob Konfiguration erfolgreich war:**
   - Sollte mit "-- Configuring done" enden
   - Sollte mit "-- Generating done" enden

### Methode 2: Visual Studio (GUI)

1. **Öffne Visual Studio**
2. **File → Open → CMake...**
3. **Navigiere zu:** `C:\Development\scribus-1.7\scribus\CMakeLists.txt`
4. Visual Studio konfiguriert CMake automatisch

### Nach erfolgreicher Konfiguration

```cmd
# Scribus bauen
cmake --build . --config Release

# Oder nur das Plugin bauen
cmake --build . --config Release --target gamma_dashboard
```

## Wichtige CMake-Variablen

- `SCRIBUS_LIBS_DIR`: Pfad zum Libs-Kit (sollte automatisch gefunden werden)
- `LIBPODOFO_SHARED=1`: PoDoFo als Shared Library (für Windows)
- `CMAKE_MSVC_RUNTIME_LIBRARY=MultiThreadedDLL`: Verwendet /MD Runtime

