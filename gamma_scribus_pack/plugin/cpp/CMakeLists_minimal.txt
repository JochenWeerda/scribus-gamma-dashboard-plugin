# Minimal Test-Version ohne Q_OBJECT

cmake_minimum_required(VERSION 3.15)
project(gamma_dashboard_plugin_minimal LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
# KEIN CMAKE_AUTOMOC - kein Q_OBJECT!

# Finde Scribus-Header
find_path(SCRIBUS_INCLUDE_DIR
    NAMES scplugin.h
    PATHS
        ${CMAKE_SOURCE_DIR}/../../../scribus/plugins
        "C:/Development/scribus-1.7/scribus"
        "C:/Program Files/Scribus 1.7.1/include"
    PATH_SUFFIXES
        plugins
        scribus/plugins
)

if(NOT SCRIBUS_INCLUDE_DIR)
    message(FATAL_ERROR "Scribus-Header nicht gefunden!")
endif()

# Finde Qt6
find_package(Qt6 REQUIRED COMPONENTS Core Widgets)

# Plugin-Quellen (NUR minimal!)
set(PLUGIN_SOURCES
    gamma_dashboard_plugin_minimal.cpp
)

set(PLUGIN_HEADERS
    gamma_dashboard_plugin_minimal.h
)

# Erstelle Plugin
add_library(gamma_dashboard_plugin_minimal MODULE
    ${PLUGIN_SOURCES}
    ${PLUGIN_HEADERS}
)

# Include-Verzeichnisse
target_include_directories(gamma_dashboard_plugin_minimal PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${SCRIBUS_INCLUDE_DIR}
    ${Qt6Core_INCLUDE_DIRS}
    ${Qt6Widgets_INCLUDE_DIRS}
)

# Linke Qt6
target_link_libraries(gamma_dashboard_plugin_minimal
    Qt6::Core
    Qt6::Widgets
)

# Windows-Einstellungen
if(WIN32)
    set_target_properties(gamma_dashboard_plugin_minimal PROPERTIES
        PREFIX ""
        SUFFIX ".dll"
        OUTPUT_NAME "gamma_dashboard"
    )
    
    target_compile_definitions(gamma_dashboard_plugin_minimal PRIVATE
        _CRT_SECURE_NO_WARNINGS
        COMPILE_PLUGIN_AS_DLL
    )
    
    target_compile_options(gamma_dashboard_plugin_minimal PRIVATE
        /W3
        /EHsc
    )
    
    target_link_options(gamma_dashboard_plugin_minimal PRIVATE /FORCE:UNRESOLVED)
endif()

