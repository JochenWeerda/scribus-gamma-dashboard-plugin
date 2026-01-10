#include "gamma_dashboard_plugin_minimal.h"

#include <QWidget>
#include <QDateTime>
#include "scplugin.h"
#include "scribuscore.h"
#include "scribus.h"

// Forward declarations
class ScribusMainWindow;
class ScribusDoc;
class Prefs_Pane;

GammaDashboardPluginMinimal::GammaDashboardPluginMinimal()
    : ScPlugin()
{
    // Minimale Initialisierung - nichts tun
}

GammaDashboardPluginMinimal::~GammaDashboardPluginMinimal() = default;

void GammaDashboardPluginMinimal::languageChange()
{
    // Nichts tun
}

QString GammaDashboardPluginMinimal::fullTrName() const
{
    return "Gamma Dashboard (Minimal Test)";
}

void GammaDashboardPluginMinimal::addToMainWindowMenu(ScribusMainWindow* mw)
{
    Q_UNUSED(mw);
    // Nichts tun - keine Menü-Integration
}

bool GammaDashboardPluginMinimal::newPrefsPanelWidget(QWidget* parent, Prefs_Pane*& panel)
{
    Q_UNUSED(parent);
    Q_UNUSED(panel);
    return false;
}

void GammaDashboardPluginMinimal::setDoc(ScribusDoc* doc)
{
    Q_UNUSED(doc);
}

void GammaDashboardPluginMinimal::unsetDoc()
{
}

void GammaDashboardPluginMinimal::changedDoc(ScribusDoc* doc)
{
    Q_UNUSED(doc);
}

const ScPlugin::AboutData* GammaDashboardPluginMinimal::getAboutData() const
{
    ScPlugin::AboutData* about = new ScPlugin::AboutData;
    about->authors = "jochen.weerda@gmail.com";
    about->shortDescription = "Gamma Dashboard (Minimal Test)";
    about->description = "Minimale Test-Version ohne Q_OBJECT";
    about->license = "Proprietary";
    about->copyright = "© 2025";
    about->releaseDate = QDateTime::currentDateTime();
    about->version = "0.0.1-test";
    return about;
}

void GammaDashboardPluginMinimal::deleteAboutData(const ScPlugin::AboutData* about) const
{
    delete about;
}

// Export-Funktionen
extern "C" PLUGIN_API int gamma_dashboard_getPluginAPIVersion()
{
    return PLUGIN_API_VERSION;
}

extern "C" PLUGIN_API ScPlugin* gamma_dashboard_getPlugin()
{
    // TEST: Versuche Instanziierung mit Try-Catch
    // Falls das abstürzt, liegt Problem beim new-Operator oder Constructor
    try {
        auto* plugin = new GammaDashboardPluginMinimal();
        return plugin;
    } catch (const std::exception& e) {
        // Catch C++ exceptions
        return nullptr;
    } catch (...) {
        // Catch alle anderen Exceptions
        return nullptr;
    }
}

extern "C" PLUGIN_API void gamma_dashboard_freePlugin(ScPlugin* plugin)
{
    delete plugin;
}

