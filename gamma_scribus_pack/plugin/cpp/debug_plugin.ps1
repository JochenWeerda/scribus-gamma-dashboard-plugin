# Debug-Script für Plugin-Laden
param(
    [switch]$WaitForLog
)

Write-Host "=== Gamma Dashboard Plugin Debug ===" -ForegroundColor Cyan
Write-Host ""

# 1. Prüfe DLL
Write-Host "1. DLL-Prüfung:" -ForegroundColor Yellow
$dllPath = "$env:APPDATA\Scribus\plugins\gamma_dashboard.dll"
if (Test-Path $dllPath) {
    $dll = Get-Item $dllPath
    Write-Host "   ✅ Gefunden: $dllPath" -ForegroundColor Green
    Write-Host "      Größe: $([math]::Round($dll.Length/1KB, 2)) KB"
    Write-Host "      Erstellt: $($dll.LastWriteTime)"
    
    # Prüfe Export-Funktionen
    $dumpbinPath = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64\dumpbin.exe"
    if (Test-Path $dumpbinPath) {
        Write-Host ""
        Write-Host "   Export-Funktionen:" -ForegroundColor Cyan
        $exports = & $dumpbinPath /EXPORTS $dllPath 2>&1 | Select-String -Pattern "gamma_dashboard"
        foreach ($exp in $exports) {
            Write-Host "      ✅ $exp" -ForegroundColor Green
        }
    }
} else {
    Write-Host "   ❌ DLL nicht gefunden: $dllPath" -ForegroundColor Red
}

Write-Host ""

# 2. Prüfe plugin.json
Write-Host "2. Metadata-Prüfung:" -ForegroundColor Yellow
$jsonPath = "$env:APPDATA\Scribus\plugins\gamma_dashboard.json"
if (Test-Path $jsonPath) {
    Write-Host "   ✅ Gefunden: $jsonPath" -ForegroundColor Green
    Get-Content $jsonPath | ForEach-Object { Write-Host "      $_" }
} else {
    Write-Host "   ⚠️  Nicht gefunden (optional)" -ForegroundColor Yellow
}

Write-Host ""

# 3. Prüfe Log-Datei
Write-Host "3. Log-Datei:" -ForegroundColor Yellow
$logFile = "$env:TEMP\scribus_debug.log"
if (Test-Path $logFile) {
    Write-Host "   ✅ Gefunden: $logFile" -ForegroundColor Green
    $logContent = Get-Content $logFile -Raw
    
    # Suche nach Plugin-relevanten Meldungen
    $matches = $logContent | Select-String -Pattern "gamma|plugin.*error|error.*plugin|API version|Unable to get ScPlugin" -AllMatches
    if ($matches) {
        Write-Host "   ⚠️  Plugin-relevante Meldungen gefunden:" -ForegroundColor Yellow
        $matches.Matches | ForEach-Object { 
            $ctx = $_.Context
            Write-Host "      $ctx" -ForegroundColor Red
        }
    } else {
        Write-Host "   ℹ️  Keine Plugin-Fehler gefunden" -ForegroundColor Cyan
    }
    
    # Zeige letzte 20 Zeilen
    Write-Host ""
    Write-Host "   Letzte 20 Zeilen:" -ForegroundColor Cyan
    Get-Content $logFile -Tail 20 | ForEach-Object { Write-Host "      $_" }
} else {
    Write-Host "   ⚠️  Nicht gefunden: $logFile" -ForegroundColor Yellow
    Write-Host "      Starte Scribus mit: .\scribus.exe 2>&1 | Tee-Object -FilePath `$env:TEMP\scribus_debug.log" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=== Nächste Schritte ===" -ForegroundColor Cyan
Write-Host "1. Scribus vollständig schließen" -ForegroundColor White
Write-Host "2. Scribus neu starten" -ForegroundColor White
Write-Host "3. Pruefe: Extras > Plugins -> 'Gamma Dashboard'" -ForegroundColor White
Write-Host "4. Falls nicht sichtbar: Prüfe Log-Datei auf Fehler" -ForegroundColor White
Write-Host ""

