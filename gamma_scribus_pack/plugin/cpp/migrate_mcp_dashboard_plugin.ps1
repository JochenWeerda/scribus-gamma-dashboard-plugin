# Migrate MCP AI Dashboard plugin into gamma_scribus_pack/plugin/cpp
param(
    [string]$RepoRoot = "",
    [switch]$NoBackup
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $RepoRoot) {
    $RepoRoot = Resolve-Path (Join-Path $ScriptDir "..")
    $RepoRoot = Resolve-Path (Join-Path $RepoRoot "..")
    $RepoRoot = Resolve-Path (Join-Path $RepoRoot "..")
}

$Source = Join-Path $RepoRoot "scribus/plugins/mcp_ai_dashboard"
$Target = Join-Path $ScriptDir "mcp_ai_dashboard"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Backup = Join-Path $ScriptDir ("backup_mcp_migration_" + $Timestamp)

Write-Host "[INFO] RepoRoot : $RepoRoot"
Write-Host "[INFO] Source   : $Source"
Write-Host "[INFO] Target   : $Target"

if (-not (Test-Path $Source)) {
    Write-Host "[ERR] Source not found. Expected: $Source"
    exit 1
}

if ((Test-Path $Target) -and (-not $NoBackup)) {
    Write-Host "[INFO] Backup existing target to $Backup"
    Copy-Item -Path $Target -Destination $Backup -Recurse -Force
}

if (Test-Path $Target) {
    Remove-Item -Path $Target -Recurse -Force
}

Copy-Item -Path $Source -Destination $Target -Recurse -Force

Write-Host "[OK] MCP dashboard plugin copied."

# Overwrite CMakeLists.txt with a standalone-friendly template.
$cmakePath = Join-Path $Target "CMakeLists.txt"
$cmakeContent = @(
    'cmake_minimum_required(VERSION 3.15)',
    'project(mcp_ai_dashboard_plugin)',
    '',
    'find_path(SCRIBUS_INCLUDE_DIR',
    '    NAMES scplugin.h scactionplugin.h',
    '    PATHS',
    '        ${CMAKE_SOURCE_DIR}/../../../scribus/plugins',
    '        ${CMAKE_SOURCE_DIR}/../../scribus',
    '        ${CMAKE_SOURCE_DIR}/../scribus',
    '        "C:/Program Files/Scribus 1.7.1/include"',
    '        "C:/Program Files/Scribus/include"',
    '        "F:/Scribus for Windows/scribus-1.7.x-svn/Scribus/scribus/plugins"',
    '        ${CMAKE_SOURCE_DIR}/../../..',
    '        /usr/include/scribus',
    '        /usr/local/include/scribus',
    '    PATH_SUFFIXES',
    '        plugins',
    '        scribus',
    '        scribus/plugins',
    ')',
    '',
    'if(NOT SCRIBUS_INCLUDE_DIR)',
    '    message(FATAL_ERROR "Scribus headers not found. Set SCRIBUS_INCLUDE_DIR.")',
    'else()',
    '    message(STATUS "Scribus Include Dir: ${SCRIBUS_INCLUDE_DIR}")',
    'endif()',
    '',
    'find_package(Qt6 QUIET COMPONENTS Core Widgets Network)',
    'if(Qt6_FOUND)',
    '    set(QT_VERSION_MAJOR 6)',
    '    message(STATUS "Qt6 found: ${Qt6_VERSION}")',
    'else()',
    '    find_package(Qt5 REQUIRED COMPONENTS Core Widgets Network)',
    '    if(Qt5_FOUND)',
    '        set(QT_VERSION_MAJOR 5)',
    '        message(STATUS "Qt5 found: ${Qt5_VERSION}")',
    '    else()',
    '        message(FATAL_ERROR "Qt5 or Qt6 not found")',
    '    endif()',
    'endif()',
    '',
    'set(PLUGIN_SOURCES',
    '    MCPDashboardPlugin.cpp',
    '    MCPDashboardDock.cpp',
    ')',
    '',
    'set(PLUGIN_HEADERS',
    '    MCPDashboardPlugin.h',
    '    MCPDashboardDock.h',
    ')',
    '',
    'add_library(mcp_ai_dashboard MODULE',
    '    ${PLUGIN_SOURCES}',
    '    ${PLUGIN_HEADERS}',
    ')',
    '',
    'if(QT_VERSION_MAJOR EQUAL 6)',
    '    target_include_directories(mcp_ai_dashboard PRIVATE',
    '        ${CMAKE_CURRENT_SOURCE_DIR}',
    '        ${SCRIBUS_INCLUDE_DIR}',
    '        ${Qt6Core_INCLUDE_DIRS}',
    '        ${Qt6Widgets_INCLUDE_DIRS}',
    '        ${Qt6Network_INCLUDE_DIRS}',
    '    )',
    '    target_link_libraries(mcp_ai_dashboard Qt6::Core Qt6::Widgets Qt6::Network)',
    'else()',
    '    target_include_directories(mcp_ai_dashboard PRIVATE',
    '        ${CMAKE_CURRENT_SOURCE_DIR}',
    '        ${SCRIBUS_INCLUDE_DIR}',
    '        ${Qt5Core_INCLUDE_DIRS}',
    '        ${Qt5Widgets_INCLUDE_DIRS}',
    '        ${Qt5Network_INCLUDE_DIRS}',
    '    )',
    '    target_link_libraries(mcp_ai_dashboard Qt5::Core Qt5::Widgets Qt5::Network)',
    'endif()',
    '',
    'if(WIN32)',
    '    set_target_properties(mcp_ai_dashboard PROPERTIES',
    '        PREFIX ""',
    '        SUFFIX ".dll"',
    '        OUTPUT_NAME "mcp_ai_dashboard"',
    '    )',
    '    target_compile_definitions(mcp_ai_dashboard PRIVATE',
    '        _CRT_SECURE_NO_WARNINGS',
    '        COMPILE_PLUGIN_AS_DLL',
    '    )',
    'else()',
    '    set_target_properties(mcp_ai_dashboard PROPERTIES',
    '        PREFIX ""',
    '        SUFFIX ".so"',
    '        OUTPUT_NAME "mcp_ai_dashboard"',
    '    )',
    'endif()',
    '',
    'if(MSVC)',
    '    target_compile_options(mcp_ai_dashboard PRIVATE /W3 /EHsc)',
    '    target_link_options(mcp_ai_dashboard PRIVATE /FORCE:UNRESOLVED)',
    'else()',
    '    target_compile_options(mcp_ai_dashboard PRIVATE -Wall -Wextra -fPIC)',
    'endif()',
    '',
    'install(TARGETS mcp_ai_dashboard DESTINATION lib/scribus/plugins)',
    ''
) -join "`n"
$cmakeContent | Set-Content -Path $cmakePath -Encoding UTF8

Write-Host "[OK] CMakeLists.txt refreshed for standalone build."
Write-Host "[NEXT] Build script: ./build_mcp_ai_dashboard.ps1"

