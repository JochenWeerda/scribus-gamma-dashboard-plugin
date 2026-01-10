cmake_minimum_required(VERSION 3.15)
project(gamma_dashboard_plugin LANGUAGES CXX)

# WICHTIG: MSVC Runtime-Library auf /MD setzen (muss mit Scribus übereinstimmen)
# Muss VOR find_package() und add_library() gesetzt werden!
if(MSVC)
    # Force MultiThreadedDLL (/MD) - Dynamic Runtime
    # /MT würde statische Runtime verwenden → MSVCP140.dll fehlt
    set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreadedDLL")
    # Entferne /MT aus Flags falls vorhanden
    string(REPLACE "/MT" "/MD" CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE}")
    string(REPLACE "/MTd" "/MDd" CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG}")
    message(STATUS "MSVC Runtime Library: ${CMAKE_MSVC_RUNTIME_LIBRARY} (MultiThreadedDLL)")
endif()

# Automatische MOC-Verarbeitung fÃ¼r Q_OBJECT
set(CMAKE_AUTOMOC ON)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Finde Scribus-Plugin-Header
# Diese sollten in der Scribus-Installation oder im Quellcode sein
find_path(SCRIBUS_INCLUDE_DIR
    NAMES scplugin.h scactionplugin.h
    PATHS
        ${CMAKE_SOURCE_DIR}/../../../scribus/plugins
        ${CMAKE_SOURCE_DIR}/../../scribus
        ${CMAKE_SOURCE_DIR}/../scribus
        "C:/Program Files/Scribus 1.7.1/include"
        "C:/Program Files/Scribus/include"
        "F:/Scribus for Windows/scribus-1.7.x-svn/Scribus/scribus/plugins"
        ${CMAKE_SOURCE_DIR}/../../..
        /usr/include/scribus
        /usr/local/include/scribus
    PATH_SUFFIXES
        plugins
        scribus
        scribus/plugins
)

if(NOT SCRIBUS_INCLUDE_DIR)
    message(WARNING "Scribus-Header nicht gefunden! Versuche alternativen Pfad...")
    # Versuche Header aus Scribus-Installation zu finden
    find_path(SCRIBUS_INCLUDE_DIR
        NAMES scplugin.h
        PATHS
            "C:/Program Files/Scribus 1.7.1"
            "F:/Scribus for Windows/scribus-1.7.x-svn"
        PATH_SUFFIXES
            include
            scribus/plugins
    )
endif()

if(NOT SCRIBUS_INCLUDE_DIR)
    # Prüfe ob SCRIBUS_INCLUDE_DIR als CMake-Variable gesetzt wurde
    if(DEFINED ENV{SCRIBUS_INCLUDE_DIR})
        set(SCRIBUS_INCLUDE_DIR $ENV{SCRIBUS_INCLUDE_DIR})
        message(STATUS "Scribus Include Dir (aus Umgebung): ${SCRIBUS_INCLUDE_DIR}")
    else()
        message(FATAL_ERROR "Scribus-Header nicht gefunden! Bitte SCRIBUS_INCLUDE_DIR setzen (z.B. -DSCRIBUS_INCLUDE_DIR=...)")
    endif()
else()
    message(STATUS "Scribus Include Dir: ${SCRIBUS_INCLUDE_DIR}")
endif()

# Finde Qt5 oder Qt6 (fuer Steps 1, 2, 3 - nicht fuer Step 0)
# Step 0: Kein Qt (nur pluginapi.h)
# Step 1: Qt Core + Widgets (fuer scplugin.h)
# Steps 2, 3: Qt Core + Widgets + Network
if(NOT TEST_STEP EQUAL "0")
    set(QT_REQUIRED_COMPONENTS Core Widgets)
    if(NOT TEST_STEP EQUAL "1")
        list(APPEND QT_REQUIRED_COMPONENTS Network)
    endif()

    find_package(Qt6 QUIET COMPONENTS ${QT_REQUIRED_COMPONENTS})
    if(Qt6_FOUND)
        set(QT_VERSION_MAJOR 6)
        message(STATUS "Qt6 gefunden: ${Qt6_VERSION}")
    else()
        find_package(Qt5 REQUIRED COMPONENTS ${QT_REQUIRED_COMPONENTS})
        if(Qt5_FOUND)
            set(QT_VERSION_MAJOR 5)
            message(STATUS "Qt5 gefunden: ${Qt5_VERSION}")
        else()
            message(FATAL_ERROR "Qt5 oder Qt6 nicht gefunden! (Scribus-Header benoetigen Qt)")
        endif()
    endif()
endif()

if(TEST_STEP EQUAL "0")
    message(STATUS "TEST STEP 0: Kein Qt (nur pluginapi.h)")
elseif(TEST_STEP EQUAL "1")
    message(STATUS "TEST STEP 1: Qt Core benötigt (für Scribus-Header)")
endif()

# Plugin-Quellen
# WICHTIG: Für Mini-Test-Strategie - setze TEST_STEP auf 0, 1, 2 oder 3
# STEP 0: Nur Export-Funktionen OHNE Qt/scplugin.h (gamma_dashboard_plugin_test_step0.cpp)
# STEP 1: Nur Export-Funktionen MIT scplugin.h (gamma_dashboard_plugin_test_step1.cpp)
# STEP 2: Mit Instanz ohne Q_OBJECT (gamma_dashboard_plugin_minimal.cpp)
# STEP 3: Mit Q_OBJECT (gamma_dashboard_plugin.cpp)

# FORCE TEST_STEP to 3 - always build full plugin
set(TEST_STEP "3" CACHE STRING "Test Step: 0=No Qt, 1=DLL only, 2=No Q_OBJECT, 3=Full" FORCE)

if(TEST_STEP EQUAL "0")
    set(PLUGIN_SOURCES gamma_dashboard_plugin_test_step0.cpp)
    set(PLUGIN_HEADERS "")
    message(STATUS "TEST STEP 0: DLL only, NO Qt (no scplugin.h)")
elseif(TEST_STEP EQUAL "1")
    set(PLUGIN_SOURCES gamma_dashboard_plugin_test_step1.cpp)
    set(PLUGIN_HEADERS "")
    message(STATUS "TEST STEP 1: DLL only (no instantiation)")
elseif(TEST_STEP EQUAL "2")
    set(PLUGIN_SOURCES gamma_dashboard_plugin_minimal.cpp)
    set(PLUGIN_HEADERS gamma_dashboard_plugin_minimal.h)
    message(STATUS "TEST STEP 2: With instance (no Q_OBJECT)")
else()
    set(PLUGIN_SOURCES
        gamma_dashboard_plugin.cpp
        gamma_dashboard_dock.cpp
        gamma_api_client.cpp
        gamma_api_settings_dialog.cpp
    )
    set(PLUGIN_HEADERS
        gamma_dashboard_plugin.h
        gamma_dashboard_dock.h
        gamma_api_client.h
        gamma_api_settings_dialog.h
    )
    message(STATUS "TEST STEP 3: Full version (with Q_OBJECT)")
endif()

# Erstelle Plugin als MODULE (shared library)
add_library(gamma_dashboard_plugin MODULE
    ${PLUGIN_SOURCES}
    ${PLUGIN_HEADERS}
)

# Include-Verzeichnisse - WICHTIG: SCRIBUS_INCLUDE_DIR für alle Steps
target_include_directories(gamma_dashboard_plugin PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${SCRIBUS_INCLUDE_DIR}
)

# Finde Scribus Libraries (nur für Steps 2 und 3)
# Step 0: Keine Scribus-Libs nötig (nur pluginapi.h)
# Step 1: Keine Scribus-Libs nötig (nur Header)
# Steps 2/3: Scribus-Libs erforderlich (Instanziierung von ScPlugin)
if((TEST_STEP STREQUAL "2") OR (TEST_STEP STREQUAL "3"))
    # Pfad für Scribus Build-Libs
    set(SCRIBUS_LIB_DIR "" CACHE PATH "Path to Scribus build libs (contains scribuscore.lib)")
    # Legacy support
    set(SCRIBUS_BUILD_DIR "" CACHE PATH "Scribus Build-Verzeichnis (z.B. C:/Development/scribus-1.7/build)")
    
    # Wenn SCRIBUS_LIB_DIR nicht gesetzt, versuche aus Umgebung
    if(NOT SCRIBUS_LIB_DIR AND DEFINED ENV{SCRIBUS_LIB_DIR})
        set(SCRIBUS_LIB_DIR $ENV{SCRIBUS_LIB_DIR})
    endif()
    
    # Falls SCRIBUS_LIB_DIR nicht gesetzt, verwende SCRIBUS_BUILD_DIR
    if(SCRIBUS_LIB_DIR AND NOT SCRIBUS_BUILD_DIR)
        set(SCRIBUS_BUILD_DIR ${SCRIBUS_LIB_DIR})
    endif()
    
    # Debug: Zeige gesuchte Pfade
    if(SCRIBUS_LIB_DIR)
        message(STATUS "Scribus Lib Dir: ${SCRIBUS_LIB_DIR}")
    endif()
    if(SCRIBUS_BUILD_DIR)
        message(STATUS "Scribus Build Dir: ${SCRIBUS_BUILD_DIR}")
    endif()
    
    # Suche nach scribuscore.lib
    find_library(SCRIBUSCORE_LIB
        NAMES scribuscore scribuscore.lib
        PATHS
            ${SCRIBUS_LIB_DIR}
            ${SCRIBUS_BUILD_DIR}
            ${SCRIBUS_BUILD_DIR}/Release
            ${SCRIBUS_BUILD_DIR}/Debug
            ${SCRIBUS_BUILD_DIR}/lib
            ${SCRIBUS_BUILD_DIR}/Release/lib
            ${SCRIBUS_BUILD_DIR}/Debug/lib
            "C:/Development/scribus-1.7/build/Release"
            "C:/Development/scribus-1.7/build/Debug"
            "C:/Development/scribus-1.7/build/lib"
            "C:/Development/scribus-1.7/build"
            "F:/Scribus for Windows/scribus-1.7.x-svn/build/Release"
            "F:/Scribus for Windows/scribus-1.7.x-svn/build/Debug"
        NO_DEFAULT_PATH
    )
    
    # Debug: Zeige Ergebnis
    if(SCRIBUSCORE_LIB)
        message(STATUS "Scribus Core Library gefunden: ${SCRIBUSCORE_LIB}")
    else()
        message(STATUS "Scribus Core Library NICHT gefunden")
        message(STATUS "Gesuchte Pfade:")
        if(SCRIBUS_LIB_DIR)
            message(STATUS "  - ${SCRIBUS_LIB_DIR}")
        endif()
        if(SCRIBUS_BUILD_DIR)
            message(STATUS "  - ${SCRIBUS_BUILD_DIR}")
            message(STATUS "  - ${SCRIBUS_BUILD_DIR}/Release")
            message(STATUS "  - ${SCRIBUS_BUILD_DIR}/Debug")
        endif()
    endif()
    
    if(SCRIBUSCORE_LIB)
        message(STATUS "Scribus Core Library gefunden: ${SCRIBUSCORE_LIB}")
        # Linke gegen Scribus Core Library
        target_link_libraries(gamma_dashboard_plugin PRIVATE ${SCRIBUSCORE_LIB})
        message(STATUS "Linked against scribuscore.lib - /FORCE:UNRESOLVED nicht nötig")
    else()
        message(FATAL_ERROR "Scribus core library not found. Set SCRIBUS_BUILD_DIR or SCRIBUS_LIB_DIR to your Scribus build lib directory.")
    endif()
endif()

# Qt-spezifische Include-Verzeichnisse und Libraries
# Step 0: Kein Qt
# Step 1: Qt Core + Widgets (fr Scribus-Header)
# Steps 2/3: Qt Core, Widgets, Network
if(NOT TEST_STEP EQUAL "0")
    if(QT_VERSION_MAJOR EQUAL 6)
        if(TEST_STEP EQUAL "1")
            # Step 1: Qt Core + Widgets
            target_include_directories(gamma_dashboard_plugin PRIVATE
                ${Qt6Core_INCLUDE_DIRS}
                ${Qt6Widgets_INCLUDE_DIRS}
            )
            target_link_libraries(gamma_dashboard_plugin
                Qt6::Core
                Qt6::Widgets
            )
        else()
            # Steps 2/3: Qt Core, Widgets, Network
            target_include_directories(gamma_dashboard_plugin PRIVATE
                ${Qt6Core_INCLUDE_DIRS}
                ${Qt6Widgets_INCLUDE_DIRS}
                ${Qt6Network_INCLUDE_DIRS}
            )
            target_link_libraries(gamma_dashboard_plugin
                Qt6::Core
                Qt6::Widgets
                Qt6::Network
            )
        endif()
    else()
        if(TEST_STEP EQUAL "1")
            # Step 1: Qt Core + Widgets
            target_include_directories(gamma_dashboard_plugin PRIVATE
                ${Qt5Core_INCLUDE_DIRS}
                ${Qt5Widgets_INCLUDE_DIRS}
            )
            target_link_libraries(gamma_dashboard_plugin
                Qt5::Core
                Qt5::Widgets
            )
        else()
            # Steps 2/3: Qt Core, Widgets, Network
            target_include_directories(gamma_dashboard_plugin PRIVATE
                ${Qt5Core_INCLUDE_DIRS}
                ${Qt5Widgets_INCLUDE_DIRS}
                ${Qt5Network_INCLUDE_DIRS}
            )
            target_link_libraries(gamma_dashboard_plugin
                Qt5::Core
                Qt5::Widgets
                Qt5::Network
            )
        endif()
    endif()
else()
    message(STATUS "TEST STEP 0: Kein Qt-Linking (nur pluginapi.h)")
endif()
# Windows-spezifische Einstellungen
if(WIN32)
    # Kein PrÃ¤fix, .dll Extension
    set_target_properties(gamma_dashboard_plugin PROPERTIES
        PREFIX ""
        SUFFIX ".dll"
        OUTPUT_NAME "gamma_dashboard"
    )
    
    # Windows-Definitionen
    target_compile_definitions(gamma_dashboard_plugin PRIVATE
        _CRT_SECURE_NO_WARNINGS
        COMPILE_PLUGIN_AS_DLL
    )
else()
    # Linux/Mac: .so Extension
    set_target_properties(gamma_dashboard_plugin PROPERTIES
        PREFIX ""
        SUFFIX ".so"
        OUTPUT_NAME "gamma_dashboard"
    )
endif()

# Compiler-Flags
if(MSVC)
    # /MD wird bereits durch CMAKE_MSVC_RUNTIME_LIBRARY gesetzt (siehe oben)
    # Keine zusätzliche /MD Option nötig - CMake setzt das automatisch
    target_compile_options(gamma_dashboard_plugin PRIVATE
        /W3
        /EHsc
    )
    # /FORCE:UNRESOLVED entfernt - scribuscore.lib ist jetzt obligatorisch
    # Nur für Step 1: Keine Libraries nötig
    if(TEST_STEP EQUAL "1")
        message(STATUS "Step 1: Kein /FORCE:UNRESOLVED nötig (keine Scribus-Libs)")
    else()
        # Steps 2/3: scribuscore.lib ist obligatorisch (FATAL_ERROR wenn nicht gefunden)
        message(STATUS "/FORCE:UNRESOLVED entfernt - scribuscore.lib ist obligatorisch")
    endif()
else()
    target_compile_options(gamma_dashboard_plugin PRIVATE
        -Wall
        -Wextra
        -fPIC
    )
endif()

# Installation
install(TARGETS gamma_dashboard_plugin
    DESTINATION lib/scribus/plugins
)

# Installiere auch Python-Script-Verzeichnis (optional)
if(EXISTS ${CMAKE_SOURCE_DIR}/../gamma_dashboard)
    install(DIRECTORY ${CMAKE_SOURCE_DIR}/../gamma_dashboard/
        DESTINATION plugins/gamma_dashboard
        FILES_MATCHING
            PATTERN "*.py"
            PATTERN "*.json"
    )
endif()



