#ifndef GAMMA_DASHBOARD_PLUGIN_MINIMAL_H
#define GAMMA_DASHBOARD_PLUGIN_MINIMAL_H

#include <QString>
#include "pluginapi.h"
#include "scplugin.h"

// Minimales Plugin ohne Q_OBJECT für Crash-Test
class GammaDashboardPluginMinimal : public ScPlugin
{
public:
    GammaDashboardPluginMinimal();
    ~GammaDashboardPluginMinimal() override;

    void languageChange() override;
    QString fullTrName() const override;
    void addToMainWindowMenu(ScribusMainWindow* mw) override;

    bool newPrefsPanelWidget(QWidget* parent, Prefs_Pane*& panel) override;
    void setDoc(ScribusDoc* doc) override;
    void unsetDoc() override;
    void changedDoc(ScribusDoc* doc) override;

    const ScPlugin::AboutData* getAboutData() const override;
    void deleteAboutData(const ScPlugin::AboutData* about) const override;

private:
    // Keine Member-Variablen, keine Initialisierung
};

// Plugin-Export-Funktionen
extern "C" PLUGIN_API int gamma_dashboard_getPluginAPIVersion();
extern "C" PLUGIN_API ScPlugin* gamma_dashboard_getPlugin();
extern "C" PLUGIN_API void gamma_dashboard_freePlugin(ScPlugin* plugin);

#endif

