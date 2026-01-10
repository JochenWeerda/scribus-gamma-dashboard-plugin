// STEP 0: Absolute Minimal-Version - OHNE scplugin.h
// Test: DLL lädt ohne Qt-Abhängigkeit

#include "pluginapi.h"

// Definiere PLUGIN_API_VERSION manuell (ohne scplugin.h)
// Aus scplugin.h: #define PLUGIN_API_VERSION 0x00000107
#define PLUGIN_API_VERSION 0x00000107

// Forward-Declaration (ohne scplugin.h)
class ScPlugin;

// Minimaler Test: Nur Export-Funktionen OHNE Qt
extern "C" PLUGIN_API int gamma_dashboard_getPluginAPIVersion()
{
    return PLUGIN_API_VERSION;
}

extern "C" PLUGIN_API ScPlugin* gamma_dashboard_getPlugin()
{
    // TEST STEP 0: Gib nullptr zurück - kein Instanziieren, kein Qt
    // Falls Scribus damit startet, liegt Problem bei Qt-Initialisierung
    return nullptr;
}

extern "C" PLUGIN_API void gamma_dashboard_freePlugin(ScPlugin* plugin)
{
    // Nichts tun - plugin ist nullptr
    (void)plugin;
}

