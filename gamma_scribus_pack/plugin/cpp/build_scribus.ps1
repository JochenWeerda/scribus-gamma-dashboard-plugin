# Build Scribus from source (Windows)

# Creates scribuscore.lib and other required libraries

param(
    [string]$ScribusLibsDir = "",
    [switch]$UseNinja
)


$ErrorActionPreference = "Stop"

Write-Host "=== Build Scribus from Source ===" -ForegroundColor Cyan
Write-Host ""

$scribusSourceDir = "C:\Development\scribus-1.7"
$scribusBuildDir = Join-Path $scribusSourceDir "build"

# Verify source directory
if (-not (Test-Path $scribusSourceDir)
)
 {
    Write-Host "ERROR: Scribus source not found: $scribusSourceDir" -ForegroundColor Red
    exit 1
}

Write-Host "OK: Source directory found: $scribusSourceDir" -ForegroundColor Green
Write-Host ""

# Find CMake
$cmakeExe = "C:\Development\bin\cmake.exe"
if (-not (Test-Path $cmakeExe)
)
 {
    Write-Host "ERROR: CMake not found: $cmakeExe" -ForegroundColor Red
    exit 1
}

Write-Host "OK: CMake found: $cmakeExe" -ForegroundColor Green
Write-Host ""

# Locate Qt6 (adjust if you have a different Qt install)

$qt6Candidates = @(
    "C:\Development\Qt\6.10.1\msvc2022_64\lib\cmake\Qt6",
    "C:\Qt\6.6.0\msvc2022_64\lib\cmake\Qt6",
    "C:\Qt\6.6.0\msvc2019_64\lib\cmake\Qt6",
    "C:\Qt\6.5.3\msvc2022_64\lib\cmake\Qt6",
    "C:\Qt\6.5.3\msvc2019_64\lib\cmake\Qt6"
)
$qt6Dir = ($qt6Candidates | Where-Object { $_ -and (Test-Path $_)
 } | Select-Object -First 1)

if ($qt6Dir)
 {
    Write-Host "OK: Qt6 found: $qt6Dir" -ForegroundColor Green
} else {
    Write-Host "WARN: Qt6 not found in default locations. Set Qt6_DIR manually." -ForegroundColor Yellow
}
Write-Host ""

# Visual Studio / vcvarsall detection (for Ninja fallback)

$vswhereExe = Join-Path ${env:ProgramFiles(x86)} "Microsoft Visual Studio\Installer\vswhere.exe"
$vsInstanceFromWhere = ""
if (Test-Path $vswhereExe)
 {
    $vsInstanceFromWhere = & $vswhereExe -latest -products * -requires Microsoft.Component.MSBuild -property installationPath
    if ($vsInstanceFromWhere -and ($vsInstanceFromWhere -like '*BuildTools*')
)
 {
        # Avoid passing BuildTools as generator instance (can be unregistered)

        $vsInstanceFromWhere = ''
    }
}
$vsCandidates = @(
    $vsInstanceFromWhere,
    "C:\Program Files\Microsoft Visual Studio\2022\Community",
    "C:\Program Files\Microsoft Visual Studio\2022\Professional",
    "C:\Program Files\Microsoft Visual Studio\2022\Enterprise",
    "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools",
    "C:\Program Files (x86)\Microsoft Visual Studio\2022\Community",
    "C:\Program Files (x86)\Microsoft Visual Studio\2022\Professional",
    "C:\Program Files (x86)\Microsoft Visual Studio\2022\Enterprise"
)

$vsInstance = ($vsCandidates | Where-Object { $_ -and (Test-Path $_)
 } | Select-Object -First 1)

$vcvarsall = ""
if ($vsInstance)
 {
    $vcvarsall = Join-Path $vsInstance "VC\Auxiliary\Build\vcvarsall.bat"
    if (-not (Test-Path $vcvarsall)
)
 {
        $vcvarsall = ""
    }
}

$ninjaExe = (Get-Command ninja -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source)

$useNinja = $UseNinja.IsPresent
if (-not $useNinja -and (-not $vsInstance)
)
 {
    $useNinja = $true
}
if (-not $useNinja -and $vsInstance -and ($vsInstance -like '*BuildTools*')
)
 {
    Write-Host 'BuildTools instance detected - forcing Ninja generator' -ForegroundColor Yellow
    $useNinja = $true
}

# Create build directory
if (-not (Test-Path $scribusBuildDir)
)
 {
    Write-Host "Creating build directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $scribusBuildDir | Out-Null
    Write-Host "OK: Build directory created: $scribusBuildDir" -ForegroundColor Green
} else {
    Write-Host "Build directory exists: $scribusBuildDir" -ForegroundColor Yellow
    Write-Host "(will reconfigure)
" -ForegroundColor Gray
}

Write-Host ""

# If Ninja selected, clear old cache to avoid generator mismatch
if ($useNinja)
 {
    $cacheFile = Join-Path $scribusBuildDir "CMakeCache.txt"
    $cacheDir = Join-Path $scribusBuildDir "CMakeFiles"
    if (Test-Path $cacheFile)
 {
        Remove-Item $cacheFile -Force
    }
    if (Test-Path $cacheDir)
 {
        Remove-Item $cacheDir -Recurse -Force
    }
    Write-Host "Ninja selected - cleared CMake cache." -ForegroundColor Yellow
    Write-Host ""
}

# Optional: Scribus libs kit (include/lib)

$libsIncludeDirs = @()

$libsLibDirs = @()

$libsPrefixDirs = @()

$pkgConfigDirs = @()

if ($ScribusLibsDir)
 {
    if (-not (Test-Path $ScribusLibsDir)
)
 {
        Write-Host "ERROR: ScribusLibsDir not found: $ScribusLibsDir" -ForegroundColor Red
        exit 1
    }
    $libsPrefixDirs += $ScribusLibsDir
    $subdirs = Get-ChildItem -Path $ScribusLibsDir -Directory -ErrorAction SilentlyContinue
    foreach ($d in $subdirs)
 {
        $libsPrefixDirs += $d.FullName
        $inc = Join-Path $d.FullName "include"
        if (Test-Path $inc)
 {
            $libsIncludeDirs += $inc
        }
        foreach ($libSuffix in @("lib\x64-v145", "lib\x64-v144", "lib\x64-v143", "lib\x64-v142", "lib\x64-v141", "lib\x64", "lib")
)
 {
            $cand = Join-Path $d.FullName $libSuffix
            if (Test-Path $cand)
 {
                $libsLibDirs += $cand
            }
        }
        foreach ($pcSuffix in @("lib\x64-v145\pkgconfig", "lib\x64-v144\pkgconfig", "lib\x64-v143\pkgconfig", "lib\x64-v142\pkgconfig", "lib\x64\pkgconfig", "lib\pkgconfig")
)
 {
            $pc = Join-Path $d.FullName $pcSuffix
            if (Test-Path $pc)
 {
                $pkgConfigDirs += $pc
            }
        }
    }

    $libsPrefixDirs = $libsPrefixDirs | Select-Object -Unique
    $libsIncludeDirs = $libsIncludeDirs | Select-Object -Unique
    $libsLibDirs = $libsLibDirs | Select-Object -Unique
    $pkgConfigDirs = $pkgConfigDirs | Select-Object -Unique

    if ($pkgConfigDirs)
 {
        $env:PKG_CONFIG_PATH = ($pkgConfigDirs -join ";")

    }

    if (-not $libsLibDirs)
 {
        Write-Host "WARNING: No lib/x64-v143 found - dependencies may not be detected." -ForegroundColor Yellow
    }
}

function Join-ArgsForCmd([string[]]$items)
 {
    $out = @()

    foreach ($a in $items)
 {
        if ($a -match "\s")
 {
            $out += '"' + $a + '"'
        } else {
            $out += $a
        }
    }
    return ($out -join " ")

}

# Configure CMake
Write-Host "=== Configure CMake ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Note: Scribus expects LIBPODOFO_SHARED" -ForegroundColor Yellow
Write-Host "Trying LIBPODOFO_SHARED=1 (DLL)
" -ForegroundColor Gray
Write-Host ""

$cmakeArgs = @(
    "-S", $scribusSourceDir,
    "-B", $scribusBuildDir,
    "-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreadedDLL",
    "-DCMAKE_BUILD_TYPE=Release",
    "-DLIBPODOFO_SHARED=1"
)


if ($useNinja)
 {
    if (-not $ninjaExe)
 {
        Write-Host "ERROR: Ninja not found. Install Ninja or use Visual Studio generator." -ForegroundColor Red
        exit 1
    }
    if (-not $vcvarsall)
 {
        Write-Host "ERROR: vcvarsall.bat not found. Install VS Build Tools or do not use Ninja." -ForegroundColor Red
        exit 1
    }
    $cmakeArgs += @(
        "-G", "Ninja",
        "-DCMAKE_MAKE_PROGRAM=$ninjaExe"
    )

} else {
    $cmakeArgs += @(
        "-G", "Visual Studio 17 2022",
        "-A", "x64"
    )

}

if ($ScribusLibsDir)
 {
    $prefixPath = ($libsPrefixDirs -join ";")

    $includePath = ($libsIncludeDirs -join ";")

    $libPath = ($libsLibDirs -join ";")


    if ($prefixPath)
 { $env:CMAKE_PREFIX_PATH = $prefixPath }
    if ($includePath)
 { $env:CMAKE_INCLUDE_PATH = $includePath }
    if ($libPath)
 { $env:CMAKE_LIBRARY_PATH = $libPath }

    Write-Host "Env CMAKE_PREFIX_PATH set ($($libsPrefixDirs.Count)
 entries)
" -ForegroundColor Gray
    Write-Host "Env CMAKE_INCLUDE_PATH set ($($libsIncludeDirs.Count)
 entries)
" -ForegroundColor Gray
    Write-Host "Env CMAKE_LIBRARY_PATH set ($($libsLibDirs.Count)
 entries)
" -ForegroundColor Gray

    $pkgConfigExe = ""
    $pkgConfigCmd = Get-Command pkg-config -ErrorAction SilentlyContinue
    if ($pkgConfigCmd)
 { $pkgConfigExe = $pkgConfigCmd.Source }

    if (-not $pkgConfigExe)
 {
        $toolsDir = Join-Path $scribusBuildDir "tools"
        if (-not (Test-Path $toolsDir)
)
 {
            New-Item -ItemType Directory -Path $toolsDir | Out-Null
        }
        $stubPy = Join-Path $toolsDir "pkg_config_stub.py"
        $stubBat = Join-Path $toolsDir "pkg-config.bat"
        $stubPythonExe = ""
        $pyCandidates = @(
            (Join-Path $ScribusLibsDir "python\\python.exe"),
            (Join-Path $ScribusLibsDir "Python\\python.exe")
        )
        if (Test-Path $ScribusLibsDir) {
            $pyDir = Get-ChildItem -Path $ScribusLibsDir -Directory -Filter "python*" -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($pyDir) {
                $pyCandidates += Join-Path $pyDir.FullName "python.exe"
            }
        }
        foreach ($cand in $pyCandidates) {
            if (-not $stubPythonExe -and $cand -and (Test-Path $cand)) {
                $stubPythonExe = $cand
            }
        }
        if (-not $stubPythonExe) {
            $stubPythonExe = "python"
        }
        if (-not (Test-Path $stubPy)
)
 {
                        $stubContent = @'
import os, sys, glob

def _first_match(patterns):
    for pat in patterns:
        matches = glob.glob(pat, recursive=True)
        if matches:
            return matches[0]
    return ''

def _find_lib(base, name):
    patterns = [
        os.path.join(base, '**', 'lib', '**', name),
        os.path.join(base, '**', name),
    ]
    return _first_match(patterns)

def _find_include(base, pkg):
    patterns = [
        os.path.join(base, pkg + '*', 'include'),
        os.path.join(base, pkg, 'include'),
    ]
    inc = _first_match(patterns)
    if inc and os.path.isdir(inc):
        return inc
    for root, dirs, files in os.walk(base):
        if os.path.basename(root).lower() == 'include' and pkg in root.lower():
            return root
    return ''

def _normalize(p):
    return p.replace('\\', '/')

def _pkg_harfbuzz(base):
    inc = _find_include(base, 'harfbuzz')
    lib = _find_lib(base, 'harfbuzz.lib')
    if not inc or not lib:
        return None
    return {
        'version': '11.2.1',
        'includes': [inc],
        'libdir': os.path.dirname(lib),
        'libs': ['harfbuzz'],
    }

def _pkg_icu(base):
    inc = _find_include(base, 'icu')
    lib_uc = _find_lib(base, 'icuuc.lib')
    lib_dt = _find_lib(base, 'icudt.lib')
    lib_in = _find_lib(base, 'icuin.lib')
    if not inc or not lib_uc:
        return None
    libs = ['icuuc']
    if lib_in:
        libs.append('icuin')
    if lib_dt:
        libs.append('icudt')
    return {
        'version': '76.1',
        'includes': [inc],
        'libdir': os.path.dirname(lib_uc),
        'libs': libs,
    }

def _pkg_harfbuzz_icu(base):
    hb = _pkg_harfbuzz(base)
    icu = _pkg_icu(base)
    if not hb or not icu:
        return None
    libs = hb['libs'] + icu['libs']
    includes = []
    for inc in hb['includes'] + icu['includes']:
        if inc not in includes:
            includes.append(inc)
    return {
        'version': hb['version'],
        'includes': includes,
        'libdir': hb['libdir'] or icu['libdir'],
        'libs': libs,
    }

def _pkg_hunspell(base):
    inc = _find_include(base, 'hunspell')
    lib = _find_lib(base, 'libhunspell_static.lib') or _find_lib(base, 'hunspell.lib') or _find_lib(base, 'libhunspell.lib')
    if not inc or not lib:
        return None
    lib_name = os.path.splitext(os.path.basename(lib))[0]
    if lib_name.lower().startswith('lib'):
        lib_name = lib_name[3:]
    return {
        'version': '1.7.2',
        'includes': [inc],
        'libdir': os.path.dirname(lib),
        'libs': [lib_name],
    }

def _get_pkg(base, name):
    if name == 'harfbuzz':
        return _pkg_harfbuzz(base)
    if name in ('harfbuzz-icu', 'harfbuzz_icu'):
        return _pkg_harfbuzz_icu(base)
    if name in ('icu-uc', 'icu_uc'):
        return _pkg_icu(base)
    if name == 'hunspell':
        return _pkg_hunspell(base)
    return None

def main():
    base = os.environ.get('PKG_CONFIG_STUB_LIBS_DIR', '')
    if not base:
        sys.exit(1)
    args = sys.argv[1:]
    pkgs = [a for a in args if not a.startswith('-')]
    pkg = pkgs[-1] if pkgs else ''
    info = _get_pkg(base, pkg)
    if '--exists' in args:
        sys.exit(0 if info else 1)
    if not info:
        sys.exit(1)
    if '--modversion' in args:
        sys.stdout.write(info.get('version', '0'))
        return
    if '--cflags' in args or '--cflags-only-I' in args:
        flags = ['-I' + _normalize(p) for p in info.get('includes', []) if p]
        sys.stdout.write(' '.join(flags))
        return
    if '--libs' in args or '--libs-only-l' in args or '--libs-only-L' in args:
        parts = []
        if '--libs-only-L' in args:
            parts = ['-L' + _normalize(info.get('libdir', ''))]
        elif '--libs-only-l' in args:
            parts = ['-l' + lib for lib in info.get('libs', [])]
        else:
            parts = ['-L' + _normalize(info.get('libdir', ''))] + ['-l' + lib for lib in info.get('libs', [])]
        sys.stdout.write(' '.join(parts))
        return
    sys.stdout.write('')

if __name__ == '__main__':
    main()
'@
            Set-Content -Path $stubPy -Value $stubContent -Encoding ASCII
        }
        if (-not (Test-Path $stubBat))
 {
            $batLines = @(
                "@echo off",
                "set PYTHON_EXE=$stubPythonExe",
                "if exist `"%PYTHON_EXE%`" (",
                "  `"%PYTHON_EXE%`" `"%~dp0pkg_config_stub.py`" %*",
                ") else (",
                "  python `"%~dp0pkg_config_stub.py`" %*",
                ")"
            )

            Set-Content -Path $stubBat -Value ($batLines -join "`n") -Encoding ASCII
        }
        $env:PKG_CONFIG_STUB_LIBS_DIR = $ScribusLibsDir
        $pkgConfigExe = $stubBat
        Write-Host "Using pkg-config stub: $pkgConfigExe" -ForegroundColor Yellow
    } else {
        Write-Host "Using pkg-config: $pkgConfigExe" -ForegroundColor Gray
    }

    $prefixPathCmake = $prefixPath -replace "\\", "/"
    $includePathCmake = $includePath -replace "\\", "/"
    $libPathCmake = $libPath -replace "\\", "/"

    $jpegLibCmake = ""
    $jpegIncludeCmake = ""
    $jpegLib = Get-ChildItem -Path $ScribusLibsDir -Filter "libjpeg9f.lib" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($jpegLib)
 {
        $jpegRoot = Split-Path -Parent $jpegLib.FullName
        $jpegRoot = Split-Path -Parent $jpegRoot
        $jpegRoot = Split-Path -Parent $jpegRoot
        $jpegInclude = Join-Path $jpegRoot "include"
        if (Test-Path $jpegInclude)
 {
            $jpegLibCmake = $jpegLib.FullName -replace "\\", "/"
            $jpegIncludeCmake = $jpegInclude -replace "\\", "/"
            Write-Host "JPEG: $($jpegLib.FullName)
" -ForegroundColor Gray
        } else {
            Write-Host "WARN: JPEG include not found under $jpegRoot" -ForegroundColor Yellow
        }
    } else {
        Write-Host "WARN: libjpeg9f.lib not found under Scribus libs dir" -ForegroundColor Yellow
    }


    $tiffLibCmake = ""
    $tiffIncludeCmake = ""
    $tiffLib = Get-ChildItem -Path $ScribusLibsDir -Filter "libtiff5.lib" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($tiffLib)
 {
        $tiffRoot = Split-Path -Parent $tiffLib.FullName
        $tiffRoot = Split-Path -Parent $tiffRoot
        $tiffRoot = Split-Path -Parent $tiffRoot
        $tiffInclude = Join-Path $tiffRoot "include"
        if (Test-Path $tiffInclude)
 {
            $tiffLibCmake = $tiffLib.FullName -replace "\\", "/"
            $tiffIncludeCmake = $tiffInclude -replace "\\", "/"
            Write-Host "TIFF: $($tiffLib.FullName)
" -ForegroundColor Gray
        } else {
            Write-Host "WARN: TIFF include not found under $tiffRoot" -ForegroundColor Yellow
        }
    } else {
        Write-Host "WARN: libtiff5.lib not found under Scribus libs dir" -ForegroundColor Yellow
    }

    $lcms2LibReleaseCmake = ""
    $lcms2LibDebugCmake = ""
    $lcms2IncludeCmake = ""
    $lcms2Lib = Get-ChildItem -Path $ScribusLibsDir -Filter "lcms2_static.lib" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    $lcms2LibDebug = Get-ChildItem -Path $ScribusLibsDir -Filter "lcms2_staticd.lib" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($lcms2Lib)
 {
        $lcms2Root = Split-Path -Parent $lcms2Lib.FullName
        $lcms2Root = Split-Path -Parent $lcms2Root
        $lcms2Root = Split-Path -Parent $lcms2Root
        $lcms2Include = Join-Path $lcms2Root "include"
        if (Test-Path $lcms2Include)
 {
            $lcms2LibReleaseCmake = $lcms2Lib.FullName -replace "\\", "/"
            $lcms2IncludeCmake = $lcms2Include -replace "\\", "/"
            Write-Host "LCMS2: $($lcms2Lib.FullName)
" -ForegroundColor Gray
        } else {
            Write-Host "WARN: LCMS2 include not found under $lcms2Root" -ForegroundColor Yellow
        }
    } else {
        Write-Host "WARN: lcms2_static.lib not found under Scribus libs dir" -ForegroundColor Yellow
    }
    if ($lcms2LibDebug)
 {
        $lcms2LibDebugCmake = $lcms2LibDebug.FullName -replace "\\", "/"
    }

    $depsCache = Join-Path $scribusBuildDir "deps_cache.cmake"
    $cacheLines = @()
    if ($prefixPathCmake) { $cacheLines += ('set(CMAKE_PREFIX_PATH "{0}" CACHE STRING "")' -f $prefixPathCmake) }
    if ($includePathCmake) { $cacheLines += ('set(CMAKE_INCLUDE_PATH "{0}" CACHE STRING "")' -f $includePathCmake) }
    if ($libPathCmake) { $cacheLines += ('set(CMAKE_LIBRARY_PATH "{0}" CACHE STRING "")' -f $libPathCmake) }
    if ($jpegLibCmake) { $cacheLines += ('set(JPEG_LIBRARY "{0}" CACHE FILEPATH "")' -f $jpegLibCmake) }
    if ($jpegIncludeCmake) { $cacheLines += ('set(JPEG_INCLUDE_DIR "{0}" CACHE PATH "")' -f $jpegIncludeCmake) }
    if ($tiffLibCmake) { $cacheLines += ('set(TIFF_LIBRARY "{0}" CACHE FILEPATH "")' -f $tiffLibCmake) }
    if ($tiffIncludeCmake) { $cacheLines += ('set(TIFF_INCLUDE_DIR "{0}" CACHE PATH "")' -f $tiffIncludeCmake) }
    if ($lcms2LibReleaseCmake) { $cacheLines += ('set(LCMS2_LIBRARY_RELEASE "{0}" CACHE FILEPATH "")' -f $lcms2LibReleaseCmake) }
    if ($lcms2LibDebugCmake) { $cacheLines += ('set(LCMS2_LIBRARY_DEBUG "{0}" CACHE FILEPATH "")' -f $lcms2LibDebugCmake) }
    if ($lcms2LibReleaseCmake) { $cacheLines += ('set(LCMS2_LIBRARY "{0}" CACHE FILEPATH "")' -f $lcms2LibReleaseCmake) }
    if ($lcms2IncludeCmake) { $cacheLines += ('set(LCMS2_INCLUDE_DIR "{0}" CACHE PATH "")' -f $lcms2IncludeCmake) }
    if ($pkgConfigExe) {
        $pkgConfigExeCmake = $pkgConfigExe -replace '\\', '/'
        $cacheLines += ('set(PKG_CONFIG_EXECUTABLE "{0}" CACHE FILEPATH "")' -f $pkgConfigExeCmake)
    }
    if ($qt6Dir) {
        $qt6DirCmake = $qt6Dir -replace '\\', '/'
        $cacheLines += ('set(Qt6_DIR "{0}" CACHE PATH "")' -f $qt6DirCmake)
        $cacheLines += ('set(QT_DIR "{0}" CACHE PATH "")' -f $qt6DirCmake)
    }
    if ($cacheLines.Count -gt 0) {
        Set-Content -Path $depsCache -Value ($cacheLines -join "`n") -Encoding UTF8
        $cmakeArgs += @("-C", $depsCache)
        Write-Host "CMake cache init: $depsCache" -ForegroundColor Gray
    }
}
if ($useNinja)
 {
    $argLine = Join-ArgsForCmd $cmakeArgs
    $cmd = "`"$vcvarsall`" x64 && `"$cmakeExe`" $argLine"
    cmd /c $cmd
} else {
    & $cmakeExe $cmakeArgs
}

if ($LASTEXITCODE -ne 0)
 {
    Write-Host "";
    Write-Host "ERROR: CMake configure failed." -ForegroundColor Red
    Write-Host "";
    Write-Host "Possible issues:" -ForegroundColor Yellow
    Write-Host "  - Dependencies missing (Qt, Python, etc.)
" -ForegroundColor White
    Write-Host "  - CMake too old" -ForegroundColor White
    Write-Host "";
    exit 1
}

Write-Host "";
Write-Host "OK: CMake configure succeeded." -ForegroundColor Green
Write-Host ""

# Build (scribuscore target)

Write-Host "=== Build Scribus Core ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Note: This can take 10-30 minutes..." -ForegroundColor Yellow
Write-Host ""

$coreProject = Join-Path $scribusBuildDir "scribus\scribuscore.vcxproj"
if ($useNinja)
{
    $buildArgs = @("--build", $scribusBuildDir, "--config", "Release", "--target", "scribuscore")
    $buildLine = Join-ArgsForCmd $buildArgs
    $buildCmd = "`"$vcvarsall`" x64 && `"$cmakeExe`" $buildLine"
    Write-Host "Building scribuscore (Ninja)..." -ForegroundColor Yellow
    cmd /c $buildCmd
}
else
{
    $msbuildExe = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin\MSBuild.exe"
    if (-not (Test-Path $msbuildExe))
    {
        Write-Host "ERROR: MSBuild not found!" -ForegroundColor Red
        exit 1
    }
    if (Test-Path $coreProject)
    {
        Write-Host "Building scribuscore only..." -ForegroundColor Yellow
        & $msbuildExe $coreProject /p:Configuration=Release /p:Platform=x64 /t:Build /v:minimal
    }
    else
    {
        Write-Host "Building Scribus (full target)..." -ForegroundColor Yellow
        $slnFile = Join-Path $scribusBuildDir "scribus.sln"
        if (Test-Path $slnFile)
        {
            & $msbuildExe $slnFile /p:Configuration=Release /p:Platform=x64 /t:scribuscore /v:minimal
        }
        else
        {
            Write-Host "No project file found - trying cmake --build" -ForegroundColor Yellow
            & $cmakeExe --build $scribusBuildDir --config Release --target scribuscore
        }
    }
}

if ($LASTEXITCODE -ne 0)
{
    Write-Host ""
    Write-Host "ERROR: Build failed." -ForegroundColor Red
    Write-Host ""
    Write-Host "Possible issues:" -ForegroundColor Yellow
    Write-Host "  - Dependencies missing" -ForegroundColor White
    Write-Host "  - Compiler errors" -ForegroundColor White
    Write-Host ""
    exit 1
}

Write-Host ""
Write-Host "OK: Build succeeded." -ForegroundColor Green
Write-Host ""

# Check for scribuscore.lib
$libPaths = @(
    "$scribusBuildDir\Release\scribuscore.lib",
    "$scribusBuildDir\scribus\Release\scribuscore.lib",
    "$scribusBuildDir\lib\Release\scribuscore.lib"
)

$foundLib = $null
foreach ($libPath in $libPaths)
{
    if (Test-Path $libPath)
    {
        $foundLib = $libPath
        break
    }
}

if ($foundLib)
{
    $libInfo = Get-Item $foundLib
    Write-Host "OK: scribuscore.lib found." -ForegroundColor Green
    Write-Host ""
    Write-Host "Details:" -ForegroundColor Cyan
    Write-Host "  File: $($libInfo.Name)" -ForegroundColor White
    Write-Host "  Size: $([math]::Round($libInfo.Length / 1KB, 1)) KB" -ForegroundColor White
    Write-Host "  Path: $($libInfo.FullName)" -ForegroundColor White
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Rebuild plugin:" -ForegroundColor White
    Write-Host "     .\rebuild_with_runtime_fix.ps1 -ScribusBuildDir '$($libInfo.DirectoryName)'" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  2. Or auto-detect:" -ForegroundColor White
    Write-Host "     .\rebuild_with_runtime_fix.ps1" -ForegroundColor Cyan
}
else
{
    Write-Host "WARNING: scribuscore.lib not found." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Searching for other .lib files..." -ForegroundColor Yellow
    $allLibs = Get-ChildItem -Path $scribusBuildDir -Filter "*.lib" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 10
    if ($allLibs)
    {
        Write-Host "Found libraries:" -ForegroundColor Cyan
        foreach ($lib in $allLibs)
        {
            Write-Host "  $($lib.Name) - $($lib.FullName)" -ForegroundColor White
        }
    }
    else
    {
        Write-Host "ERROR: No .lib files found!" -ForegroundColor Red
        Write-Host ""
        Write-Host "Possible issues:" -ForegroundColor Yellow
        Write-Host "  - Build did not produce targets" -ForegroundColor White
        Write-Host "  - Wrong build type" -ForegroundColor White
    }
}
