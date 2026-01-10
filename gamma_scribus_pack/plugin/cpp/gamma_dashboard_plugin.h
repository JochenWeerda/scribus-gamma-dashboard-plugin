#ifndef GAMMA_DASHBOARD_PLUGIN_H
#define GAMMA_DASHBOARD_PLUGIN_H

#include <QHash>
#include <QJsonObject>
#include <QPointer>
#include <QString>
#include <QStringList>

#include "pluginapi.h"
#include "scplugin.h"

// Forward declarations (Qt)
class QAction;
class QMainWindow;
class QMenu;
class QMenuBar;
class QTimer;
class QWidget;

// Forward declarations (Scribus)
class ScribusMainWindow;
class ScribusDoc;
struct Prefs_Pane;

class GammaDashboardDock;
class GammaApiClient;
class GammaApiSettingsDialog;

/**
 * @brief Gamma Dashboard Plugin for Scribus
 * 
 * Native C++ Plugin with Dock Widget Integration.
 * Inspired by MCP Dashboard Plugin Pattern.
 */
class GammaDashboardPlugin : public ScPlugin
{
    Q_OBJECT

public:
    GammaDashboardPlugin();
    ~GammaDashboardPlugin() override;

    // Plugin lifecycle methods
    // NOTE: initPlugin()/cleanupPlugin() are NOT virtual in ScPlugin (only in ScPersistentPlugin).
    // For ScPlugin, initialization happens in addToMainWindowMenu() and constructor.
    // These methods are provided for compatibility but may not be called by Scribus.
    bool initPlugin();
    bool cleanupPlugin();
    
    void languageChange() override;

    QString fullTrName() const override;
    void addToMainWindowMenu(ScribusMainWindow *) override;

    // Virtual methods from ScPlugin (with default implementations)
    bool newPrefsPanelWidget(QWidget* parent, Prefs_Pane*& panel) override;
    void setDoc(ScribusDoc* doc) override;
    void unsetDoc() override;
    void changedDoc(ScribusDoc* doc) override;

    // Additional plugin info methods
    const ScPlugin::AboutData* getAboutData() const override;
    void deleteAboutData(const ScPlugin::AboutData* about) const override;

private slots:
    void toggleDashboard();
    void showSettingsDialog();
    void onPipelineStart();
    void onPipelineStop();
    void onSettingsChanged(const QString& baseUrl, const QString& apiKey, bool useMockMode);
    void handleStatusReceived(const QJsonObject& obj);
    void handlePipelineReceived(const QJsonObject& obj);
    void handleAssetsReceived(const QJsonObject& obj);
    void handleLayoutAuditReceived(const QJsonObject& obj);
    void handleConnectionStatusChanged(bool connected, int latencyMs);
    void handleErrorOccurred(const QString& error, int httpStatusCode);
    void handlePipelineStartResult(bool success, const QString& message);
    void handlePipelineStopResult(bool success, const QString& message);

private:
    QMainWindow* resolveMainWindow() const;
    QMenu* ensureMenu(QMenuBar* bar, const QStringList& names) const;
    void loadSettings();
    void saveSettings();
    void generateMockData();
    QJsonObject createMockStatusResponse();
    QJsonObject createMockPipelineResponse();
    QJsonObject createMockAssetsResponse();
    QJsonObject createMockLayoutAuditResponse();

    QPointer<GammaDashboardDock> m_dock = nullptr;
    QAction* m_action = nullptr;
    QAction* m_settingsAction = nullptr;
    GammaApiClient* m_apiClient = nullptr;
    QTimer* m_mockTimer = nullptr;
    QString m_baseUrl;
    QString m_apiKey;
    bool m_useMockMode = false;
};

// Plugin export functions (required by Scribus)
extern "C" PLUGIN_API int gamma_dashboard_getPluginAPIVersion();
extern "C" PLUGIN_API ScPlugin* gamma_dashboard_getPlugin();
extern "C" PLUGIN_API void gamma_dashboard_freePlugin(ScPlugin* plugin);

#endif // GAMMA_DASHBOARD_PLUGIN_H

