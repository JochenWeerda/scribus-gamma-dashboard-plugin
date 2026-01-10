# Build script for MCP AI Dashboard plugin
param(
    [string]$ScribusSourcePath = "",
    [string]$QtPath = "",
    [string]$BuildType = "Release"
)

$ErrorActionPreference = "Stop"

Write-Host "=== MCP AI Dashboard Plugin Build ==="

# 1) Find CMake
$cmakeExe = ""
$cmakeCmd = Get-Command cmake -ErrorAction SilentlyContinue
if ($cmakeCmd) {
    $cmakeExe = $cmakeCmd.Source
}
if (-not $cmakeExe) {
    $candidates = @(
        "C:/Development/cmake-4.2.1/bin/cmake.exe",
        "C:/Program Files/CMake/bin/cmake.exe",
        "C:/Program Files (x86)/CMake/bin/cmake.exe"
    )
    foreach ($p in $candidates) {
        if (Test-Path $p) { $cmakeExe = $p; break }
    }
}
if (-not $cmakeExe) {
    Write-Host "[ERR] CMake not found."
    exit 1
}

# 2) Find Scribus headers
$scribusInclude = ""
if ($ScribusSourcePath) {
    $testPath = Join-Path $ScribusSourcePath "scribus/plugins"
    if (Test-Path (Join-Path $testPath "scplugin.h")) {
        $scribusInclude = $testPath
    } elseif (Test-Path (Join-Path $ScribusSourcePath "scplugin.h")) {
        $scribusInclude = $ScribusSourcePath
    }
}
if (-not $scribusInclude) {
    $paths = @(
        "F:/Scribus for Windows/scribus-1.7.x-svn/Scribus/scribus/plugins",
        "C:/Scribus/scribus-1.7.x-svn/Scribus/scribus/plugins",
        "$env:USERPROFILE/Downloads/scribus-1.7.x-svn/Scribus/scribus/plugins"
    )
    foreach ($p in $paths) {
        if (Test-Path (Join-Path $p "scplugin.h")) { $scribusInclude = $p; break }
    }
}
if (-not $scribusInclude) {
    Write-Host "[ERR] Scribus headers not found. Use -ScribusSourcePath."
    exit 1
}

# 3) Find Qt
$qtPath = ""
if ($QtPath) {
    if (Test-Path (Join-Path $QtPath "bin/qmake.exe")) { $qtPath = $QtPath }
}
if (-not $qtPath) {
    $paths = @(
        "C:/Qt/5.15.2/msvc2019_64",
        "C:/Qt/5.15.2/msvc2022_64",
        "C:/Qt/6.5.0/msvc2019_64",
        "C:/Program Files/Qt/5.15.2/msvc2019_64"
    )
    foreach ($p in $paths) {
        if (Test-Path (Join-Path $p "bin/qmake.exe")) { $qtPath = $p; break }
    }
}
if (-not $qtPath) {
    Write-Host "[ERR] Qt not found. Use -QtPath."
    exit 1
}

# 4) Configure and build
$pluginDir = Join-Path $PSScriptRoot "mcp_ai_dashboard"
if (-not (Test-Path $pluginDir)) {
    Write-Host "[ERR] Plugin dir not found: $pluginDir"
    exit 1
}

$buildDir = Join-Path $PSScriptRoot "build_mcp_ai_dashboard"
if (Test-Path $buildDir) { Remove-Item $buildDir -Recurse -Force }
New-Item -ItemType Directory -Path $buildDir | Out-Null

$cmakeArgs = @(
    "-S", $pluginDir,
    "-B", $buildDir,
    "-DSCRIBUS_INCLUDE_DIR=$scribusInclude",
    "-DCMAKE_PREFIX_PATH=$qtPath",
    "-DCMAKE_BUILD_TYPE=$BuildType"
)
& $cmakeExe @cmakeArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERR] CMake configure failed."
    exit 1
}

& $cmakeExe --build $buildDir --config $BuildType
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERR] Build failed."
    exit 1
}

$dll = Get-ChildItem $buildDir -Filter "mcp_ai_dashboard*.dll" -Recurse | Select-Object -First 1
if ($dll) {
    Write-Host "[OK] DLL: $($dll.FullName)"
    Write-Host "Copy to: C:/Program Files/Scribus 1.7.1/lib/scribus/plugins/"
} else {
    Write-Host "[WARN] DLL not found. Check build output."
}
