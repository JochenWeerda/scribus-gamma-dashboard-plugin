# Schnelles Build-Script mit lokalem CMake
param(
    [string]$CmakePath = "C:\Development\cmake-4.2.1",
    [string]$ScribusSourcePath = "F:\Scribus for Windows\scribus-1.7.x-svn",
    [string]$QtPath = ""
)

$ErrorActionPreference = "Stop"

Write-Host "=== Gamma Dashboard Plugin - Quick Build ===" -ForegroundColor Cyan

# 1. Finde CMake
Write-Host "`n1. Prüfe CMake..." -ForegroundColor Yellow
$cmakeExe = ""

# Prüfe zuerst im PATH
$cmakeInPath = Get-Command cmake -ErrorAction SilentlyContinue
if ($cmakeInPath) {
    $cmakeExe = $cmakeInPath.Source
    Write-Host "  CMake im PATH: $cmakeExe" -ForegroundColor Green
} else {
    # Versuche angegebenen Pfad
    if (Test-Path $CmakePath) {
        # Prüfe Standard-Struktur
        $testPaths = @(
            (Join-Path $CmakePath "bin\cmake.exe"),
            (Join-Path $CmakePath "cmake-4.2.1\bin\cmake.exe"),
            (Join-Path $CmakePath "cmake\bin\cmake.exe")
        )
        
        $foundPath = $null
        foreach ($testPath in $testPaths) {
            if (Test-Path $testPath) {
                $foundPath = $testPath
                break
            }
        }
        
        if ($foundPath) {
            $cmakeExe = $foundPath
            Write-Host "  CMake gefunden: $cmakeExe" -ForegroundColor Green
        } else {
            # Suche rekursiv nach cmake.exe (aber ignoriere Test-Dateien)
            Write-Host "  Suche rekursiv in $CmakePath..." -ForegroundColor Gray
            $found = Get-ChildItem $CmakePath -Filter "cmake.exe" -Recurse -ErrorAction SilentlyContinue | 
                     Where-Object { $_.FullName -notlike "*\Tests\*" -and $_.FullName -notlike "*\Testing\*" } | 
                     Select-Object -First 1
            if ($found) {
                $cmakeExe = $found.FullName
                Write-Host "  CMake gefunden: $cmakeExe" -ForegroundColor Green
            }
        }
    } else {
        Write-Host "  WARNUNG: CMake-Pfad existiert nicht: $CmakePath" -ForegroundColor Yellow
    }
}

if (-not $cmakeExe) {
    Write-Host "  FEHLER: CMake nicht gefunden!" -ForegroundColor Red
    Write-Host "`nLösungsvorschläge:" -ForegroundColor Yellow
    Write-Host "  1. Extrahiere CMake ZIP:" -ForegroundColor White
    Write-Host "     Expand-Archive -Path 'C:\Users\Jochen\Downloads\cmake-4.2.1.zip' -DestinationPath 'C:\Development' -Force" -ForegroundColor Cyan
    Write-Host "`n  2. Oder installiere CMake von: https://cmake.org/download/" -ForegroundColor White
    Write-Host "`n  3. Oder gib einen anderen CMake-Pfad an:" -ForegroundColor White
    Write-Host "     .\quick_build.ps1 -CmakePath 'C:\Path\To\CMake'" -ForegroundColor Cyan
    exit 1
}

# Teste CMake
$cmakeVersion = & $cmakeExe --version 2>&1 | Select-Object -First 1
Write-Host "  Version: $cmakeVersion" -ForegroundColor Gray

# 2. Finde Scribus-Header
Write-Host "`n2. Finde Scribus-Header..." -ForegroundColor Yellow
$scribusInclude = ""

if ($ScribusSourcePath) {
    # Prüfe ob Laufwerk existiert
    $drive = [System.IO.Path]::GetPathRoot($ScribusSourcePath)
    if (-not (Test-Path $drive)) {
        Write-Host "  WARNUNG: Laufwerk $drive existiert nicht!" -ForegroundColor Yellow
        Write-Host "  Suche nach alternativen Scribus-Pfaden..." -ForegroundColor Gray
    } else {
    $testPaths = @(
        (Join-Path $ScribusSourcePath "Scribus\scribus\plugins"),
        (Join-Path $ScribusSourcePath "scribus\plugins"),
        (Join-Path $ScribusSourcePath "scribus"),
        (Join-Path $ScribusSourcePath "plugins")
    )
        
        foreach ($testPath in $testPaths) {
            if (Test-Path (Join-Path $testPath "scplugin.h")) {
                $scribusInclude = $testPath
                break
            }
        }
    }
}

# Suche alternative Pfade wenn nicht gefunden
if (-not $scribusInclude) {
    Write-Host "  Suche nach Scribus-Header in Standard-Pfaden..." -ForegroundColor Gray
    $alternativePaths = @(
        "C:\Development\scribus-1.7",
        "C:\Scribus",
        "$env:USERPROFILE\Downloads\scribus-1.7",
        "$env:USERPROFILE\Documents\scribus-1.7"
    )
    
    foreach ($altPath in $alternativePaths) {
        if (Test-Path $altPath) {
            $testPaths = @(
                (Join-Path $altPath "Scribus\scribus\plugins"),
                (Join-Path $altPath "scribus\plugins"),
                (Join-Path $altPath "scribus"),
                (Join-Path $altPath "plugins")
            )
            foreach ($testPath in $testPaths) {
                if (Test-Path (Join-Path $testPath "scplugin.h")) {
                    $scribusInclude = $testPath
                    Write-Host "  Scribus-Header in alternativem Pfad gefunden: $scribusInclude" -ForegroundColor Yellow
                    break
                }
            }
            if ($scribusInclude) { break }
        }
    }
    
    # Als letzte Option: Suche rekursiv nach scplugin.h
    if (-not $scribusInclude) {
        Write-Host "  Suche rekursiv nach scplugin.h..." -ForegroundColor Gray
        foreach ($altPath in $alternativePaths) {
            if (Test-Path $altPath) {
                $found = Get-ChildItem $altPath -Filter "scplugin.h" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
                if ($found) {
                    $scribusInclude = Split-Path $found.FullName -Parent
                    Write-Host "  Scribus-Header rekursiv gefunden: $scribusInclude" -ForegroundColor Yellow
                    break
                }
            }
        }
    }
}

if (-not $scribusInclude) {
    Write-Host "  FEHLER: Scribus-Header nicht gefunden!" -ForegroundColor Red
    Write-Host "  Bitte gib den Scribus-Quellcode-Pfad an:" -ForegroundColor Yellow
    Write-Host "  .\quick_build.ps1 -ScribusSourcePath 'F:\Scribus for Windows\scribus-1.7.x-svn'" -ForegroundColor White
    exit 1
}

Write-Host "  Scribus-Header: $scribusInclude" -ForegroundColor Green

# 3. Finde Qt (optional für jetzt)
Write-Host "`n3. Finde Qt5..." -ForegroundColor Yellow
$qtPath = ""

if ($QtPath) {
    if (Test-Path (Join-Path $QtPath "bin\qmake.exe")) {
        $qtPath = $QtPath
    }
}

if (-not $qtPath) {
    $possibleQtPaths = @(
        "C:\Qt\6.5.3\msvc2019_64",
        "C:\Qt\6.5.3\msvc2022_64",
        "C:\Qt\5.15.2\msvc2019_64",
        "C:\Qt\5.15.2\msvc2022_64",
        "C:\Qt\6.5.0\msvc2019_64",
        "C:\Qt\5.15\msvc2019_64"
    )
    
    foreach ($path in $possibleQtPaths) {
        if (Test-Path (Join-Path $path "bin\qmake.exe")) {
            $qtPath = $path
            break
        }
    }
}

if (-not $qtPath) {
    Write-Host "  WARNUNG: Qt5 nicht gefunden!" -ForegroundColor Yellow
    Write-Host "  Das Plugin benötigt Qt5 für die Kompilierung." -ForegroundColor Yellow
    Write-Host "  Bitte installiere Qt5 oder gib den Pfad an:" -ForegroundColor Yellow
    Write-Host "  .\quick_build.ps1 -QtPath 'C:\Qt\5.15.2\msvc2019_64'" -ForegroundColor White
    Write-Host "`nWeiter ohne Qt (wird wahrscheinlich fehlschlagen)..." -ForegroundColor Yellow
} else {
    Write-Host "  Qt5 gefunden: $qtPath" -ForegroundColor Green
}

# 4. Erstelle Build-Verzeichnis
Write-Host "`n4. Erstelle Build-Verzeichnis..." -ForegroundColor Yellow
$buildDir = Join-Path $PSScriptRoot "build"
if (Test-Path $buildDir) {
    Write-Host "  Lösche altes Build-Verzeichnis..." -ForegroundColor Gray
    Remove-Item $buildDir -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $buildDir | Out-Null
Write-Host "  Build-Verzeichnis: $buildDir" -ForegroundColor Green

# 5. CMake konfigurieren
Write-Host "`n5. Konfiguriere CMake..." -ForegroundColor Yellow
$cmakeArgs = @(
    "-S", $PSScriptRoot,
    "-B", $buildDir,
    "-DSCRIBUS_INCLUDE_DIR=$scribusInclude"
)

if ($qtPath) {
    $cmakeArgs += "-DCMAKE_PREFIX_PATH=$qtPath"
}

# Finde Scribus-Installation für Install-Pfad
$scribusInstallPaths = @(
    "C:\Program Files\Scribus 1.7.1",
    "C:\Program Files (x86)\Scribus 1.7.1",
    "C:\Program Files\Scribus",
    "C:\Scribus"
)

$scribusInstall = ""
foreach ($path in $scribusInstallPaths) {
    $drive = [System.IO.Path]::GetPathRoot($path)
    if ((Test-Path $drive) -and (Test-Path $path)) {
        $pluginPath = Join-Path $path "lib\scribus\plugins"
        if (Test-Path $pluginPath) {
            $scribusInstall = $path
            break
        }
    }
}

if ($scribusInstall) {
    $cmakeArgs += "-DCMAKE_INSTALL_PREFIX=$scribusInstall"
    Write-Host "  Install-Pfad: $scribusInstall" -ForegroundColor Gray
}

$cmakeArgs += "-DCMAKE_BUILD_TYPE=Release"

Write-Host "  Führe CMake aus..." -ForegroundColor Gray
& $cmakeExe @cmakeArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "  FEHLER: CMake-Konfiguration fehlgeschlagen!" -ForegroundColor Red
    Write-Host "  Prüfe die Fehlermeldungen oben." -ForegroundColor Yellow
    exit 1
}
Write-Host "  CMake konfiguriert" -ForegroundColor Green

# 6. Build
Write-Host "`n6. Kompiliere Plugin..." -ForegroundColor Yellow
& $cmakeExe --build $buildDir --config Release
if ($LASTEXITCODE -ne 0) {
    Write-Host "  FEHLER: Kompilierung fehlgeschlagen!" -ForegroundColor Red
    exit 1
}
Write-Host "  Plugin kompiliert" -ForegroundColor Green

# 7. Finde DLL
Write-Host "`n7. Suche erstellte DLL..." -ForegroundColor Yellow
$dllPath = Get-ChildItem $buildDir -Filter "gamma_dashboard*.dll" -Recurse | Select-Object -First 1
if ($dllPath) {
    Write-Host "  DLL gefunden: $($dllPath.FullName)" -ForegroundColor Green
    Write-Host "`n=== Build erfolgreich! ===" -ForegroundColor Green
    
    if ($scribusInstall) {
        $pluginDir = Join-Path $scribusInstall "lib\scribus\plugins"
        Write-Host "`nNächste Schritte:" -ForegroundColor Cyan
        Write-Host "  1. Kopiere die DLL nach: $pluginDir" -ForegroundColor White
        Write-Host "  2. Starte Scribus neu" -ForegroundColor White
        Write-Host "  3. Plugin sollte unter 'Extras → Gamma Dashboard' erscheinen" -ForegroundColor White
    }
} else {
    Write-Host "  WARNUNG: DLL nicht gefunden!" -ForegroundColor Yellow
    Write-Host "  Prüfe das Build-Verzeichnis: $buildDir" -ForegroundColor Yellow
}

