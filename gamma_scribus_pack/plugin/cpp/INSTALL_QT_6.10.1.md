# Qt 6.10.1 Installation für Gamma Dashboard Plugin

## Schritt 1: Qt Installer herunterladen

1. Öffne: https://www.qt.io/download-qt-installer
2. Klicke auf "Download the Qt Online Installer"
3. Installiere den Qt Online Installer

## Schritt 2: Qt 6.10.1 installieren

1. **Qt Installer starten** (erfordert Qt Account - kostenlos registrieren)

2. **Bei Installation wählen:**
   - **Qt Version:** Qt 6.10.1
   - **Compiler:** MSVC 2019 64-bit ODER MSVC 2022 64-bit
     - Wichtig: Wähle die Version, die mit deiner Visual Studio Installation übereinstimmt!
   - **Zusätzliche Komponenten:**
     - Qt Creator (optional, aber empfohlen)
     - Qt 6.10.1 > MSVC 2019 64-bit (oder MSVC 2022 64-bit)
     - Qt 6.10.1 > Qt Network

3. **Installationspfad:** Standard ist `C:\Qt\6.10.1\msvc2019_64` (oder msvc2022_64)

## Schritt 3: Installation prüfen

Nach der Installation sollte folgender Pfad existieren:
```
C:\Qt\6.10.1\msvc2019_64\bin\qmake.exe
```
ODER
```
C:\Qt\6.10.1\msvc2022_64\bin\qmake.exe
```

## Schritt 4: Plugin neu kompilieren

Nach der Qt-Installation das Plugin neu kompilieren:

```powershell
cd 'c:\Users\Jochen\Documents\Die verborgene Uhr Gottes\Gottes geheimer Zeitcode\gamma_scribus_pack\plugin\cpp'
.\rebuild_with_qt6101.ps1
```

## Schnell-Installation (Alternativ)

Wenn du bereits Qt installiert hast und nur 6.10.1 hinzufügen möchtest:
1. Qt Maintenance Tool öffnen
2. "Add or remove components" wählen
3. Qt 6.10.1 auswählen und installieren

## Troubleshooting

### Qt 6.10.1 wird nicht in Installer angezeigt
- Installer aktualisieren
- Prüfe ob Qt Account korrekt eingeloggt ist

### Falscher Compiler gewählt
- Plugin muss mit derselben Compiler-Version kompiliert werden wie Scribus
- Prüfe: `C:\Program Files\Scribus 1.7.1(1)\Qt6Core.dll` mit Dependency Walker oder ähnlichem Tool

### Installation nimmt viel Zeit in Anspruch
- Normale Download-Größe: ~2-3 GB
- Installation: ~10-15 Minuten (abhängig von Internet-Geschwindigkeit)


