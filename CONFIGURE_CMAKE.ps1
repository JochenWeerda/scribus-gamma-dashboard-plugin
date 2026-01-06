# CMake-Konfiguration für Scribus (nach Libs-Kit Build)

Write-Host "=== CMake für Scribus konfigurieren ===" -ForegroundColor Cyan
Write-Host ""

$scribusSource = "C:\Development\scribus-1.7\scribus"
$scribusBuild = "C:\Development\scribus-1.7\build"
$libsKitDir = "C:\Development\scribus-1.7.x-libs-msvc"

# Prüfe Pfade
if (-not (Test-Path $scribusSource)) {
    Write-Host "FEHLER: Scribus-Source nicht gefunden: $scribusSource" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $libsKitDir)) {
    Write-Host "FEHLER: Libs-Kit nicht gefunden: $libsKitDir" -ForegroundColor Red
    exit 1
}

Write-Host "Scribus Source: $scribusSource" -ForegroundColor White
Write-Host "Scribus Build: $scribusBuild" -ForegroundColor White
Write-Host "Libs-Kit: $libsKitDir" -ForegroundColor White
Write-Host ""

# Erstelle Build-Verzeichnis
if (-not (Test-Path $scribusBuild)) {
    Write-Host "Erstelle Build-Verzeichnis..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $scribusBuild -Force | Out-Null
}

# Finde CMake
$cmakePaths = @(
    "C:\Development\bin\cmake.exe",
    "C:\Program Files\CMake\bin\cmake.exe",
    "C:\Program Files (x86)\CMake\bin\cmake.exe"
)

$cmake = $null
foreach ($path in $cmakePaths) {
    if (Test-Path $path) {
        $cmake = $path
        break
    }
}

if (-not $cmake) {
    Write-Host "FEHLER: CMake nicht gefunden!" -ForegroundColor Red
    Write-Host "Bitte CMake installieren oder Pfad anpassen." -ForegroundColor Yellow
    exit 1
}

Write-Host "CMake gefunden: $cmake" -ForegroundColor Green
Write-Host ""

# CMake-Konfiguration
Write-Host "Konfiguriere CMake..." -ForegroundColor Yellow
Write-Host ""

# Versuche verschiedene Generatoren
$generators = @(
    "Visual Studio 17 2022",
    "Visual Studio 16 2022", 
    "Visual Studio 15 2022"
)

$cmakeArgs = @(
    "..",
    "-A", "x64",
    "-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreadedDLL",
    "-DLIBPODOFO_SHARED=1",
    "-DSCRIBUS_LIBS_DIR=$libsKitDir"
)

# Finde passenden Generator
$generatorFound = $false
foreach ($gen in $generators) {
    Write-Host "Versuche Generator: $gen" -ForegroundColor Gray
    $testArgs = @("-G", $gen) + $cmakeArgs
    $testResult = & $cmake $testArgs 2>&1
    if ($LASTEXITCODE -eq 0 -or ($testResult -notmatch "could not find any instance")) {
        $cmakeArgs = @("-G", $gen) + $cmakeArgs
        $generatorFound = $true
        Write-Host "Generator gefunden: $gen" -ForegroundColor Green
        break
    }
}

if (-not $generatorFound) {
    Write-Host "WARNUNG: Kein Visual Studio Generator gefunden, verwende Standard-Generator" -ForegroundColor Yellow
    # Entferne Generator-Argument, CMake wählt automatisch
    $cmakeArgs = $cmakeArgs | Where-Object { $_ -ne "-A" -and $_ -ne "x64" }
}

# Zusätzliche Pfade für Bibliotheken (falls CMake sie nicht automatisch findet)
# Die Property-Sheet-Datei sollte eigentlich helfen, aber manchmal braucht CMake explizite Pfade

Write-Host "CMake-Argumente:" -ForegroundColor Cyan
$cmakeArgs | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
Write-Host ""

try {
    Push-Location $scribusBuild
    
    # Setze Visual Studio Umgebungsvariablen
    $vsPath = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools"
    $vcvars = "$vsPath\VC\Auxiliary\Build\vcvars64.bat"
    
    if (Test-Path $vcvars) {
        Write-Host "Setze Visual Studio Umgebungsvariablen..." -ForegroundColor Gray
        # vcvars64.bat setzt Umgebungsvariablen, müssen in derselben Shell-Session bleiben
        # Daher: Führe CMake in derselben Session aus, nachdem vcvars geladen wurde
        $env:Path = "$vsPath\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64;$env:Path"
        $env:VCINSTALLDIR = "$vsPath\VC\"
    }
    
    & $cmake $cmakeArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "=== CMake-Konfiguration erfolgreich! ===" -ForegroundColor Green
        Write-Host ""
        Write-Host "Nächster Schritt: Scribus bauen" -ForegroundColor Cyan
        Write-Host "  cmake --build . --config Release" -ForegroundColor White
    } else {
        Write-Host ""
        Write-Host "=== CMake-Konfiguration fehlgeschlagen! ===" -ForegroundColor Red
        Write-Host "Exit Code: $LASTEXITCODE" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Prüfe die Fehlermeldungen oben." -ForegroundColor Yellow
        exit $LASTEXITCODE
    }
} catch {
    Write-Host ""
    Write-Host "FEHLER bei CMake-Konfiguration: $_" -ForegroundColor Red
    exit 1
} finally {
    Pop-Location
}

