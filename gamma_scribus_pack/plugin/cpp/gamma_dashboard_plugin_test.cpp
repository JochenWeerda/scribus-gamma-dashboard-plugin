// Minimale Test-Version - nur Export-Funktionen
// Keine Instanziierung, kein Constructor

#include "pluginapi.h"
#include "scplugin.h"

// Minimaler Test: Nur Export-Funktionen ohne Instanziierung
extern "C" PLUGIN_API int gamma_dashboard_getPluginAPIVersion()
{
    return PLUGIN_API_VERSION;
}

extern "C" PLUGIN_API ScPlugin* gamma_dashboard_getPlugin()
{
    // TEST: Gib nullptr zurück - kein Instanziieren
    // Falls Scribus damit startet, liegt Problem beim Constructor
    return nullptr;
}

extern "C" PLUGIN_API void gamma_dashboard_freePlugin(ScPlugin* plugin)
{
    // Nichts tun - plugin ist nullptr
    (void)plugin;
}

