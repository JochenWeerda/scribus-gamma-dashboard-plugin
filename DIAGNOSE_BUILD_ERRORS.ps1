# Diagnose der Build-Fehler im Scribus-Libs-Kit
Write-Host "=== Diagnose: Scribus-Libs-Kit Build-Fehler ===" -ForegroundColor Cyan
Write-Host ""

# 1. Prüfe Visual Studio Version
Write-Host "1. Visual Studio Version:" -ForegroundColor Yellow
$vsPath = Get-ChildItem "C:\Program Files\Microsoft Visual Studio\2022\" -Directory -ErrorAction SilentlyContinue | Select-Object -First 1
if ($vsPath) {
    Write-Host "   Gefunden: $($vsPath.Name)" -ForegroundColor Green
} else {
    Write-Host "   Visual Studio 2022 nicht gefunden!" -ForegroundColor Red
}
Write-Host ""

# 2. Prüfe ICU-Bibliotheken
Write-Host "2. ICU-Bibliotheken (x64):" -ForegroundColor Yellow
$icuLibs = Get-ChildItem "C:\Development\scribus-1.7.x-libs-msvc\icu-76.1\lib" -Recurse -Filter "*.lib" | Where-Object { $_.FullName -like "*x64*" }
if ($icuLibs) {
    Write-Host "   Gefunden: $($icuLibs.Count) Bibliotheken" -ForegroundColor Green
    $icuLibs | ForEach-Object {
        Write-Host "   - $($_.Name) in $($_.DirectoryName)" -ForegroundColor Gray
    }
} else {
    Write-Host "   KEINE ICU-Bibliotheken gefunden!" -ForegroundColor Red
}
Write-Host ""

# 3. Prüfe libxml2
Write-Host "3. libxml2-Bibliotheken:" -ForegroundColor Yellow
$xmlLibs = Get-ChildItem "C:\Development\scribus-1.7.x-libs-msvc" -Recurse -Filter "*xml*.lib"
if ($xmlLibs) {
    Write-Host "   Gefunden:" -ForegroundColor Green
    $xmlLibs | ForEach-Object {
        Write-Host "   - $($_.Name) in $($_.DirectoryName)" -ForegroundColor Gray
        if ($_.Name -like "*_d.lib") {
            Write-Host "     → Debug-Version" -ForegroundColor Cyan
        } else {
            Write-Host "     → Release-Version (kein _d Suffix)" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "   KEINE libxml2-Bibliotheken gefunden!" -ForegroundColor Red
}
Write-Host ""

# 4. Prüfe, welche Toolset-Version verwendet wird
Write-Host "4. Toolset-Versionen in Libs-Kit:" -ForegroundColor Yellow
$toolsetDirs = Get-ChildItem "C:\Development\scribus-1.7.x-libs-msvc" -Recurse -Directory | Where-Object { $_.Name -match "v14[0-9]|x64|Win32" } | Select-Object -Unique Name
if ($toolsetDirs) {
    Write-Host "   Gefundene Toolset-Verzeichnisse:" -ForegroundColor Green
    $toolsetDirs | ForEach-Object {
        Write-Host "   - $($_.Name)" -ForegroundColor Gray
    }
} else {
    Write-Host "   Keine Toolset-Verzeichnisse gefunden" -ForegroundColor Yellow
}
Write-Host ""

# 5. Prüfe Visual Studio Solution-Konfiguration
Write-Host "5. Visual Studio Solution:" -ForegroundColor Yellow
$slnPath = "C:\Development\scribus-1.7.x-libs-msvc\scribus-libs-msvc2022.sln"
if (Test-Path $slnPath) {
    Write-Host "   Solution gefunden: $slnPath" -ForegroundColor Green
    
    # Prüfe, welche Konfigurationen es gibt
    $slnContent = Get-Content $slnPath -Raw
    if ($slnContent -match 'Debug|Release') {
        Write-Host "   Konfigurationen:" -ForegroundColor Cyan
        if ($slnContent -match 'Debug') {
            Write-Host "   - Debug (kann Debug-Bibliotheken benötigen)" -ForegroundColor Yellow
        }
        if ($slnContent -match 'Release') {
            Write-Host "   - Release" -ForegroundColor Green
        }
    }
} else {
    Write-Host "   Solution nicht gefunden: $slnPath" -ForegroundColor Red
}
Write-Host ""

# 6. Zusammenfassung und Lösungsvorschläge
Write-Host "=== PROBLEM-ANALYSE ===" -ForegroundColor Red
Write-Host ""
Write-Host "Hauptprobleme:" -ForegroundColor Yellow
Write-Host "1. libxml2_d.lib fehlt (Debug-Version)" -ForegroundColor Red
Write-Host "   → Lösung: Nur Release-Build verwenden ODER Debug-Bibliotheken bauen" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. ICU-Bibliotheken in Unterverzeichnissen (x64-v142, x64-v143)" -ForegroundColor Yellow
Write-Host "   → Lösung: Bibliothekspfade in Visual Studio korrekt setzen" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Möglicherweise falsche Toolset-Version (v142 vs v143)" -ForegroundColor Yellow
Write-Host "   → Lösung: Visual Studio Toolset-Version prüfen und anpassen" -ForegroundColor Cyan
Write-Host ""

Write-Host "=== EMPFOHLENE LÖSUNG ===" -ForegroundColor Green
Write-Host ""
Write-Host "Option 1: Nur Release-Build (EINFACHSTE LÖSUNG)" -ForegroundColor Cyan
Write-Host "  → Visual Studio: Build → Configuration Manager" -ForegroundColor White
Write-Host "  → Active solution configuration: Release" -ForegroundColor White
Write-Host "  → Dann: Build → Build Solution" -ForegroundColor White
Write-Host ""
Write-Host "Option 2: Bibliothekspfade korrigieren" -ForegroundColor Cyan
Write-Host "  → Visual Studio: Project → Properties → Linker → General" -ForegroundColor White
Write-Host "  → Additional Library Directories hinzufügen:" -ForegroundColor White
Write-Host "    - C:\Development\scribus-1.7.x-libs-msvc\icu-76.1\lib\x64-v143" -ForegroundColor Gray
Write-Host "    - C:\Development\scribus-1.7.x-libs-msvc\libxml2-2.15.1\lib\x64-v143" -ForegroundColor Gray
Write-Host ""

