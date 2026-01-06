# Build-Fehler: Qt6Core5Compat.lib und qregexp.h

## Status

✅ **Build läuft** - MSBuild findet das Toolset und kompiliert
❌ **Build fehlgeschlagen** - Zwei kritische Fehler:

1. **Linker-Fehler:** `Qt6Core5Compat.lib` kann nicht geöffnet werden
2. **Compiler-Fehler:** `qregexp.h` kann nicht geöffnet werden

## Problem 1: Qt6Core5Compat.lib fehlt

**Fehlermeldung:**
```
LINK : fatal error LNK1181: Eingabedatei "Qt6Core5Compat.lib" kann nicht geöffnet werden.
```

**Ursache:**
- Qt6Core5Compat ist ein optionales Qt6-Modul für Qt5-Kompatibilität
- Es ist möglicherweise nicht installiert
- ODER der Pfad wird nicht gefunden

**Lösung:**

### Option A: Qt6Core5Compat installieren

1. **Qt Maintenance Tool öffnen:**
   - Windows Start-Menü → "Qt Maintenance Tool"
   - ODER: `C:\Development\Qt\MaintenanceTool.exe`

2. **Add or remove components:**
   - Expand: **Qt 6.10.1 → MSVC 2022 64-bit**
   - Suche: **Qt 5 Compatibility Module**
   - ✅ **Aktiviere:** `Qt 5 Compatibility Module`
   - **Next → Update**

3. **Nach Installation:**
   - Build erneut starten

### Option B: Prüfe, ob Qt6Core5Compat installiert ist

**PowerShell:**
```powershell
Get-ChildItem "C:\Development\Qt\6.10.1\msvc2022_64\lib\Qt6Core5Compat*.lib"
```

**Erwartete Ausgabe:**
- `Qt6Core5Compat.lib` (Release)
- `Qt6Core5Compatd.lib` (Debug)

## Problem 2: qregexp.h fehlt

**Fehlermeldung:**
```
error C1083: Datei (Include) kann nicht geöffnet werden: "qregexp.h": No such file or directory
```

**Ursache:**
- `QRegExp` wurde in Qt6 aus Qt Core entfernt
- Es ist jetzt Teil von `Qt5Compat` (Qt6Core5Compat)
- Der Code verwendet noch den alten Qt5-Header `qregexp.h`

**Lösung:**

Der Header muss geändert werden:

**Vorher (Qt5):**
```cpp
#include <qregexp.h>
QRegExp regexp;
```

**Nachher (Qt6 mit Qt5Compat):**
```cpp
#include <QtCore5Compat/QRegExp>
QRegExp regexp;
```

**ODER (Qt6 native, empfohlen):**
```cpp
#include <QRegularExpression>
QRegularExpression regexp;
```

### Datei anpassen

**Datei:** `C:\Development\scribus-1.7\win32\msvc2022\scribus-rtf\scribus-rtf-pch.h`

**Zeile 69 ändern von:**
```cpp
#include <qregexp.h>
```

**Zu:**
```cpp
#include <QtCore5Compat/QRegExp>
```

**⚠️ Hinweis:** Dies ist eine Source-Code-Änderung. Nach der Änderung muss der Build erneut gestartet werden.

## Empfohlener Workflow

1. ✅ **Qt6Core5Compat installieren** (Option A)
2. ✅ **qregexp.h-Header anpassen** (Problem 2)
3. ✅ **Build erneut starten**

## Alternative: Qt5Compat deaktivieren (falls nicht gewünscht)

Falls Qt5Compat nicht installiert werden soll, muss der Code komplett auf Qt6 migriert werden:
- `QRegExp` → `QRegularExpression`
- Alle Qt5-Kompatibilitäts-APIs entfernen

**⚠️ Warnung:** Dies erfordert umfangreiche Code-Änderungen.

## Überprüfung nach Fix

**Prüfe Qt6Core5Compat:**
```powershell
Test-Path "C:\Development\Qt\6.10.1\msvc2022_64\lib\Qt6Core5Compat.lib"
# Sollte True zurückgeben
```

**Prüfe Header:**
```powershell
Test-Path "C:\Development\Qt\6.10.1\msvc2022_64\include\QtCore5Compat\QRegExp"
# Sollte True zurückgeben
```

