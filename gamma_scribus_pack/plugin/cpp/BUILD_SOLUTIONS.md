# Build-Lösungen für Gamma Dashboard Plugin

## Problem
Das Plugin benötigt zur Link-Zeit das Meta-Object von `ScPlugin`, das nur in gebauten Scribus-Libraries verfügbar ist.

## Lösung 1: Plugin in Scribus-Build integrieren (EMPFOHLEN)

### Schritt 1: Plugin in Scribus-Source-Tree kopieren
```powershell
# Kopiere Plugin-Verzeichnis nach Scribus
Copy-Item -Recurse "gamma_scribus_pack/plugin/cpp" `
  "C:\Development\scribus-1.7\scribus\plugins\gamma_dashboard"
```

### Schritt 2: CMakeLists.txt in Scribus erweitern
Füge in `C:\Development\scribus-1.7\scribus\plugins\CMakeLists.txt` hinzu:
```cmake
add_subdirectory(gamma_dashboard)
```

### Schritt 3: Plugin-CMakeLists.txt anpassen
Ändere `gamma_dashboard/CMakeLists.txt` zu:
```cmake
set(GAMMA_DASHBOARD_PLUGIN_SOURCES
    gamma_dashboard_plugin.cpp
    gamma_dashboard_dock.cpp
)

set(GAMMA_DASHBOARD_PLUGIN_HEADERS
    gamma_dashboard_plugin.h
    gamma_dashboard_dock.h
)

add_library(gamma_dashboard MODULE 
    ${GAMMA_DASHBOARD_PLUGIN_SOURCES}
    ${GAMMA_DASHBOARD_PLUGIN_HEADERS}
)

target_link_libraries(gamma_dashboard ${EXE_NAME})

if(WANT_PCH)
    target_precompile_headers(gamma_dashboard PRIVATE "../plugins_pch.h")
endif()

install(TARGETS gamma_dashboard
  LIBRARY
  DESTINATION ${PLUGINDIR}
  PERMISSIONS ${PLUGIN_PERMISSIONS}
)
```

### Schritt 4: Scribus bauen
```powershell
cd C:\Development\scribus-1.7
mkdir build
cd build
cmake .. -DCMAKE_PREFIX_PATH="C:\Qt\6.5.3\msvc2019_64"
cmake --build . --config Release
```

## Lösung 2: Minimaler Workaround (für schnelles Testen)

Erstelle eine minimale Stub-Library, die nur das Meta-Object bereitstellt. Das ist kompliziert und nicht empfohlen.

## Lösung 3: Runtime-Test trotz Linker-Fehler

Falls die DLL trotz Linker-Fehler erstellt wurde, kann sie möglicherweise zur Laufzeit in Scribus geladen werden, wenn alle Symbole zur Laufzeit verfügbar sind. Das ist jedoch riskant.

## EMPFOHLENER WEG

**Lösung 1** ist der sauberste Ansatz und entspricht der Standard-Praxis für Scribus-Plugins. Alle anderen Plugins werden auch so gebaut.

