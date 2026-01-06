# Build Script für Scribus-Libs-Kit
# Baut die Solution mit Release-Konfiguration und x64-Platform

Write-Host "=== Scribus-Libs-Kit Build ===" -ForegroundColor Cyan
Write-Host ""

$solutionPath = "C:\Development\scribus-1.7.x-libs-msvc\scribus-libs-msvc2022.sln"
$configuration = "Release"
$platform = "x64"

# Prüfe, ob Solution existiert
if (-not (Test-Path $solutionPath)) {
    Write-Host "FEHLER: Solution nicht gefunden: $solutionPath" -ForegroundColor Red
    exit 1
}

Write-Host "Solution: $solutionPath" -ForegroundColor White
Write-Host "Configuration: $configuration" -ForegroundColor White
Write-Host "Platform: $platform" -ForegroundColor White
Write-Host ""

# Finde MSBuild
$msbuildPaths = @(
    "C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe",
    "C:\Program Files\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin\MSBuild.exe",
    "C:\Program Files (x86)\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe",
    "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin\MSBuild.exe"
)

$msbuild = $null
foreach ($path in $msbuildPaths) {
    if (Test-Path $path) {
        $msbuild = $path
        break
    }
}

if (-not $msbuild) {
    Write-Host "FEHLER: MSBuild nicht gefunden!" -ForegroundColor Red
    Write-Host "Bitte Visual Studio Build Tools installieren oder MSBuild-Pfad anpassen." -ForegroundColor Yellow
    exit 1
}

Write-Host "MSBuild gefunden: $msbuild" -ForegroundColor Green
Write-Host ""

# Build-Befehl
Write-Host "Starte Build..." -ForegroundColor Yellow
Write-Host ""

$buildArgs = @(
    $solutionPath,
    "/p:Configuration=$configuration",
    "/p:Platform=$platform",
    "/m",  # Multi-processor build
    "/v:minimal"  # Minimale Ausgabe
)

try {
    & $msbuild $buildArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "=== Build erfolgreich! ===" -ForegroundColor Green
        Write-Host ""
        Write-Host "Nächster Schritt: CMake für Scribus konfigurieren" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "=== Build fehlgeschlagen! ===" -ForegroundColor Red
        Write-Host "Exit Code: $LASTEXITCODE" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Prüfe die Fehlermeldungen oben." -ForegroundColor Yellow
        exit $LASTEXITCODE
    }
} catch {
    Write-Host ""
    Write-Host "FEHLER beim Build: $_" -ForegroundColor Red
    exit 1
}

