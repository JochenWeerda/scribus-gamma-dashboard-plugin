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
class Prefs_Pane;

class GammaDashboardDock;
class GammaApiClient;
class GammaApiSettingsDialog;
class GammaFigmaBrowser;
class GammaSLAInserter;

/**
 * @brief Gamma Dashboard Plugin for Scribus
 * 
 * Native C++ Plugin with Dock Widget Integration.
 * Inspired by MCP Dashboard Plugin Pattern.
 */
class GammaDashboardPlugin : public ScActionPlugin
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
    
    // ScActionPlugin methods
    bool run(ScribusDoc* doc, const QString& target = QString()) override;

    // Virtual methods from ScPlugin (with default implementations)
    bool newPrefsPanelWidget(QWidget* parent, Prefs_Pane*& panel) override;
    void setDoc(ScribusDoc* doc) override;
    void unsetDoc() override;
    void changedDoc(ScribusDoc* doc) override;

    // Additional plugin info methods
    const ScActionPlugin::AboutData* getAboutData() const override;
    void deleteAboutData(const ScActionPlugin::AboutData* about) const override;

private slots:
    void toggleDashboard();
    void showSettingsDialog();
    void onPipelineStart();
    void onPipelineStop();
    void onSettingsChanged(const QString& baseUrl, const QString& apiKey, const QString& provider, bool useMockMode);
    void handleStatusReceived(const QJsonObject& obj);
    void handlePipelineReceived(const QJsonObject& obj);
    void handleAssetsReceived(const QJsonObject& obj);
    void handleLayoutAuditReceived(const QJsonObject& obj);
    void handleConnectionStatusChanged(bool connected, int latencyMs);
    void handleErrorOccurred(const QString& error, int httpStatusCode);
    void handlePipelineStartResult(bool success, const QString& message);
    void handlePipelineStopResult(bool success, const QString& message);
    void handleRAGImagesForTextReceived(const QJsonArray& images);
    void handleRAGTextsForImageReceived(const QJsonArray& texts);
    void handleRAGSuggestPairsReceived(const QJsonArray& suggestions);
    void onImportFrameFromFigma();
    void onExportPageToFigma();
    void onFigmaFrameImportRequested(const QString& fileKey, const QString& frameId);
    void onFindImagesForText();
    void onFindTextsForImage();
    void onSuggestTextImagePairs();
    void onWorkflowRunBundle(const QString& bundleZipPath);
    void handleWorkflowJobCreated(const QJsonObject& job);

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
    QAction* m_importFigmaAction = nullptr;
    QAction* m_exportFigmaAction = nullptr;
    GammaApiClient* m_apiClient = nullptr;
    GammaFigmaBrowser* m_figmaBrowser = nullptr;
    GammaSLAInserter* m_slaInserter = nullptr;
    QTimer* m_mockTimer = nullptr;
    ScribusDoc* m_currentDoc = nullptr;  // Aktuelles Dokument (via setDoc())
    QString m_baseUrl;
    QString m_apiKey;
    QString m_llmProvider;
    bool m_useMockMode = false;
    bool m_settingsMenuRegistered = false;
};

// Plugin export functions (required by Scribus)
extern "C" PLUGIN_API int gamma_dashboard_getPluginAPIVersion();
extern "C" PLUGIN_API ScPlugin* gamma_dashboard_getPlugin();
extern "C" PLUGIN_API void gamma_dashboard_freePlugin(ScPlugin* plugin);

#endif // GAMMA_DASHBOARD_PLUGIN_H
