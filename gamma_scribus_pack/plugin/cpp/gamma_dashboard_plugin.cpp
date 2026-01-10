#include "gamma_dashboard_plugin.h"
#include "gamma_dashboard_dock.h"
#include "gamma_api_client.h"

#include <QAction>
#include <QApplication>
#include <QJsonDocument>
#include <QJsonArray>
#include <QJsonObject>
#include <QMainWindow>
#include <QMenu>
#include <QMenuBar>
#include <QSettings>
#include <QTimer>
#include <QUrl>
#include <QDateTime>
#include <QRandomGenerator>

#include "pluginapi.h"
#include "scplugin.h"

// Forward declarations - vermeide vollständige Scribus-Header
class ScribusMainWindow;

namespace {
QString cleanMenuText(const QString& text)
{
    QString out = text;
    out.remove('&');
    return out.trimmed();
}
}

GammaDashboardPlugin::GammaDashboardPlugin()
    : ScPlugin()
    , m_action(nullptr)
    , m_settingsAction(nullptr)
    , m_apiClient(nullptr)
    , m_mockTimer(nullptr)
    , m_baseUrl("http://localhost:8000")
    , m_apiKey()
    , m_useMockMode(false)
{
    // Create API Client
    m_apiClient = new GammaApiClient(this);
    
    // Load settings
    loadSettings();
    
    // Configure API Client
    m_apiClient->setBaseUrl(m_baseUrl);
    m_apiClient->setApiKey(m_apiKey);
    
    // Connect signals
    connect(m_apiClient, &GammaApiClient::statusReceived,
            this, &GammaDashboardPlugin::handleStatusReceived);
    connect(m_apiClient, &GammaApiClient::pipelineReceived,
            this, &GammaDashboardPlugin::handlePipelineReceived);
    connect(m_apiClient, &GammaApiClient::assetsReceived,
            this, &GammaDashboardPlugin::handleAssetsReceived);
    connect(m_apiClient, &GammaApiClient::layoutAuditReceived,
            this, &GammaDashboardPlugin::handleLayoutAuditReceived);
    connect(m_apiClient, &GammaApiClient::connectionStatusChanged,
            this, &GammaDashboardPlugin::handleConnectionStatusChanged);
    connect(m_apiClient, &GammaApiClient::errorOccurred,
            this, &GammaDashboardPlugin::handleErrorOccurred);
    connect(m_apiClient, &GammaApiClient::pipelineStartResult,
            this, &GammaDashboardPlugin::handlePipelineStartResult);
    connect(m_apiClient, &GammaApiClient::pipelineStopResult,
            this, &GammaDashboardPlugin::handlePipelineStopResult);

    // Mock timer for mock mode updates
    m_mockTimer = new QTimer(this);
    m_mockTimer->setInterval(2000);
    connect(m_mockTimer, &QTimer::timeout, this, &GammaDashboardPlugin::generateMockData);
}

GammaDashboardPlugin::~GammaDashboardPlugin() = default;

// NOTE: initPlugin() is only virtual in ScPersistentPlugin, not in ScPlugin.
// For ScPlugin, initialization happens in addToMainWindowMenu() and constructor.
// This method is provided for compatibility but may not be called by Scribus.
bool GammaDashboardPlugin::initPlugin()
{
    // API Client is already initialized in constructor
    // Menu integration happens in addToMainWindowMenu()
    return true;
}

bool GammaDashboardPlugin::cleanupPlugin()
{
    if (m_apiClient)
        m_apiClient->stopPolling();
    if (m_dock)
        m_dock->deleteLater();
    saveSettings();
    return true;
}

void GammaDashboardPlugin::languageChange()
{
    if (m_action)
        m_action->setText(tr("Gamma Dashboard"));
}

QString GammaDashboardPlugin::fullTrName() const
{
    return tr("Gamma Dashboard");
}

void GammaDashboardPlugin::addToMainWindowMenu(ScribusMainWindow* mw)
{
    // This method is called for ScPlugin (not initPlugin())
    // Menu integration happens here
    if (!mw)
        return;

    // API Client is already initialized in constructor

    // Add menu entry
    QMainWindow* mainWin = resolveMainWindow();
    if (!mainWin)
        return;

    QMenuBar* bar = mainWin->menuBar();
    if (!bar)
        return;

    QMenu* menu = ensureMenu(bar, QStringList() << "Extras" << "Tools");
    if (!menu)
        return;

    if (!m_action) {
        m_action = new QAction(tr("Gamma Dashboard"), mainWin);
        m_action->setCheckable(true);
        connect(m_action, &QAction::triggered, this, &GammaDashboardPlugin::toggleDashboard);
        menu->addAction(m_action);
        
        menu->addSeparator();
        
        m_settingsAction = new QAction(tr("Settings..."), mainWin);
        connect(m_settingsAction, &QAction::triggered, this, &GammaDashboardPlugin::showSettingsDialog);
        menu->addAction(m_settingsAction);
    }
}

bool GammaDashboardPlugin::newPrefsPanelWidget(QWidget* parent, Prefs_Pane*& panel)
{
    Q_UNUSED(parent);
    Q_UNUSED(panel);
    return false; // Kein Prefs-Panel
}

void GammaDashboardPlugin::setDoc(ScribusDoc* doc)
{
    Q_UNUSED(doc);
    // Plugin does not react to document changes
}

void GammaDashboardPlugin::unsetDoc()
{
    // Plugin does not react to document changes
}

void GammaDashboardPlugin::changedDoc(ScribusDoc* doc)
{
    Q_UNUSED(doc);
    // Plugin does not react to document changes
}

const ScPlugin::AboutData* GammaDashboardPlugin::getAboutData() const
{
    ScPlugin::AboutData* about = new ScPlugin::AboutData;
    about->authors = "jochen.weerda@gmail.com";
    about->shortDescription = tr("Gamma → Scribus Pipeline Dashboard");
    about->description = tr(
        "Gamma → Scribus Pipeline Dashboard\n\n"
        "Importiert Gamma-Exports (PPTX + PNG), clustert Cards, "
        "generiert Crops und erstellt Hints für die Setzerei-Engine.\n\n"
        "Features:\n"
        "• Native QT-GUI-Integration\n"
        "• Pipeline-Management\n"
        "• Live-Status-Updates\n"
        "• Automatische Crop-Generierung"
    );
    about->license = "Proprietary";
    about->copyright = "© 2025 Setzerei Engine";
    about->releaseDate = QDateTime::fromString("2025-01-27", Qt::ISODate);
    about->version = "1.0.0";
    return about;
}

void GammaDashboardPlugin::deleteAboutData(const ScPlugin::AboutData* about) const
{
    delete about;
}

void GammaDashboardPlugin::toggleDashboard()
{
    QMainWindow* mw = resolveMainWindow();
    if (!mw)
        return;

    if (!m_dock)
    {
        m_dock = new GammaDashboardDock(qobject_cast<QWidget*>(mw));
        mw->addDockWidget(Qt::RightDockWidgetArea, m_dock);
        connect(m_dock, &GammaDashboardDock::pipelineStartRequested, this, &GammaDashboardPlugin::onPipelineStart);
        connect(m_dock, &GammaDashboardDock::pipelineStopRequested, this, &GammaDashboardPlugin::onPipelineStop);
        connect(m_dock, &GammaDashboardDock::settingsRequested, this, &GammaDashboardPlugin::showSettingsDialog);
    }

    bool show = !m_dock->isVisible();
    m_dock->setVisible(show);
    if (m_action)
        m_action->setChecked(show);

    if (show)
    {
        if (m_useMockMode)
        {
            // Mock mode: Generate mock data immediately and start timer
            generateMockData();
            if (m_mockTimer)
                m_mockTimer->start();
        }
        else
        {
            // Real API: Status abrufen und Polling starten
            if (m_apiClient)
            {
                m_apiClient->requestStatus();
                m_apiClient->requestPipeline();
                m_apiClient->requestAssets();
                m_apiClient->requestLayoutAudit();
                m_apiClient->startPolling(2000);
            }
        }
    }
    else
    {
        // Polling stoppen
        if (m_useMockMode)
        {
            if (m_mockTimer)
                m_mockTimer->stop();
        }
        else
        {
            if (m_apiClient)
                m_apiClient->stopPolling();
        }
    }
}

void GammaDashboardPlugin::onPipelineStart()
{
    if (!m_apiClient)
        return;
    
    // Pipeline-ID aus Dock holen (später erweitern)
    QString pipelineId = "pipeline-001"; // Default
    if (m_dock)
        m_dock->appendLog(QString("Starting pipeline: %1").arg(pipelineId));
    
    m_apiClient->startPipeline(pipelineId);
}

void GammaDashboardPlugin::onPipelineStop()
{
    if (!m_apiClient)
        return;
    
    QString pipelineId = "pipeline-001"; // Default
    if (m_dock)
        m_dock->appendLog(QString("Stopping pipeline: %1").arg(pipelineId));
    
    m_apiClient->stopPipeline(pipelineId);
}

// Handler methods for API client signals
void GammaDashboardPlugin::handleStatusReceived(const QJsonObject& obj)
{
    // Status already processed in ApiClient, only UI update if needed
    if (m_dock)
    {
        QString status = obj.value("status").toString("unknown");
        m_dock->appendLog(QString("Status: %1").arg(status));
    }
}

void GammaDashboardPlugin::handlePipelineReceived(const QJsonObject& obj)
{
    if (!m_dock)
        return;
    
    // Process pipeline status
    QJsonArray pipelines = obj.value("pipelines").toArray();
    if (!pipelines.isEmpty())
    {
        QJsonObject pipeline = pipelines[0].toObject();
        QString status = pipeline.value("status").toString("unknown");
        int progress = pipeline.value("progress").toInt(0);
        
        m_dock->setPipelineProgress(progress);
        m_dock->appendLog(QString("Pipeline: %1 (%2%)").arg(status).arg(progress));
    }
    else
    {
        // Single pipeline object
        QString status = obj.value("status").toString("unknown");
        int progress = obj.value("progress").toInt(0);
        m_dock->setPipelineProgress(progress);
        m_dock->appendLog(QString("Pipeline: %1 (%2%)").arg(status).arg(progress));
    }
}

void GammaDashboardPlugin::handleAssetsReceived(const QJsonObject& obj)
{
    if (m_dock)
    {
        int total = obj.value("total_assets").toInt(0);
        int validated = obj.value("validated_assets").toInt(0);
        int progress = obj.value("progress_percent").toInt(0);
        
        m_dock->appendLog(QString("Assets: %1/%2 (%3%)").arg(validated).arg(total).arg(progress));
    }
}

void GammaDashboardPlugin::handleLayoutAuditReceived(const QJsonObject& obj)
{
    if (m_dock)
    {
        QJsonObject zOrder = obj.value("z_order_guard").toObject();
        QJsonObject overlaps = obj.value("overlaps").toObject();
        QJsonObject lowRes = obj.value("low_res_images").toObject();
        
        QString zOrderStatus = zOrder.value("status").toString("unknown");
        int overlapCount = overlaps.value("count").toInt(0);
        int lowResCount = lowRes.value("count").toInt(0);
        
        m_dock->appendLog(QString("Layout Audit: Z-Order=%1, Overlaps=%2, Low-Res=%3")
                          .arg(zOrderStatus).arg(overlapCount).arg(lowResCount));
    }
}

void GammaDashboardPlugin::handleConnectionStatusChanged(bool connected, int latencyMs)
{
    if (m_dock)
    {
        m_dock->setStatus(connected, latencyMs);
        if (connected)
            m_dock->appendLog(QString("Connected (latency: %1 ms)").arg(latencyMs));
        else
            m_dock->appendLog("Disconnected");
    }
}

void GammaDashboardPlugin::handleErrorOccurred(const QString& error, int httpStatusCode)
{
    if (m_dock)
    {
        if (httpStatusCode > 0)
            m_dock->appendLog(QString("Error [HTTP %1]: %2").arg(httpStatusCode).arg(error));
        else
            m_dock->appendLog(QString("Error: %1").arg(error));
    }
}

void GammaDashboardPlugin::handlePipelineStartResult(bool success, const QString& message)
{
    if (m_dock)
    {
        if (success)
            m_dock->appendLog(QString("Pipeline started: %1").arg(message));
        else
            m_dock->appendLog(QString("Pipeline start failed: %1").arg(message));
    }
}

void GammaDashboardPlugin::handlePipelineStopResult(bool success, const QString& message)
{
    if (m_dock)
    {
        if (success)
            m_dock->appendLog(QString("Pipeline stopped: %1").arg(message));
        else
            m_dock->appendLog(QString("Pipeline stop failed: %1").arg(message));
    }
}

QMainWindow* GammaDashboardPlugin::resolveMainWindow() const
{
    // Versuche ScCore zu verwenden (wenn verfügbar)
    // Forward declaration verhindert direkten Zugriff, daher verwenden wir nur QApplication
    QWidget* active = QApplication::activeWindow();
    if (active)
    {
        QMainWindow* mw = qobject_cast<QMainWindow*>(active);
        if (mw)
            return mw;
    }

    // Durchsuche alle Top-Level-Widgets
    const auto top = QApplication::topLevelWidgets();
    for (QWidget* w : top)
    {
        QMainWindow* mw = qobject_cast<QMainWindow*>(w);
        if (mw)
            return mw;
    }
    return nullptr;
}

QMenu* GammaDashboardPlugin::ensureMenu(QMenuBar* bar, const QStringList& names) const
{
    if (!bar || names.isEmpty())
        return nullptr;

    // Helper to find menu by title
    auto findMenuByTitle = [](QMenu* parent, const QString& title) -> QMenu* {
        if (!parent) return nullptr;
        for (QAction* act : parent->actions())
        {
            if (QMenu* menu = act->menu())
            {
                if (cleanMenuText(menu->title()).compare(title, Qt::CaseInsensitive) == 0)
                    return menu;
            }
        }
        return nullptr;
    };

    // Find or create first level menu (e.g., "Extras")
    QMenu* currentMenu = nullptr;
    for (QAction* act : bar->actions())
    {
        if (QMenu* menu = act->menu())
        {
            if (cleanMenuText(menu->title()).compare(names[0], Qt::CaseInsensitive) == 0)
            {
                currentMenu = menu;
                break;
            }
        }
    }

    if (!currentMenu)
        currentMenu = bar->addMenu(tr(names[0].toUtf8().constData()));

    // Navigate through submenus (e.g., "Extras" -> "Tools")
    for (int i = 1; i < names.size(); ++i)
    {
        QMenu* subMenu = findMenuByTitle(currentMenu, names[i]);
        if (!subMenu)
        {
            // Check for German translation "Werkzeuge" if looking for "Tools"
            if (names[i].compare("Tools", Qt::CaseInsensitive) == 0)
            {
                subMenu = findMenuByTitle(currentMenu, "Werkzeuge");
            }
            if (!subMenu)
            {
                subMenu = currentMenu->addMenu(tr(names[i].toUtf8().constData()));
            }
        }
        currentMenu = subMenu;
    }

    return currentMenu;
}

void GammaDashboardPlugin::showSettingsDialog()
{
    GammaApiSettingsDialog dialog;
    dialog.setBaseUrl(m_baseUrl);
    dialog.setApiKey(m_apiKey);
    dialog.setUseMockMode(m_useMockMode);
    
    connect(&dialog, &GammaApiSettingsDialog::settingsChanged,
            this, &GammaDashboardPlugin::onSettingsChanged);
    
    dialog.exec();
}

void GammaDashboardPlugin::onSettingsChanged(const QString& baseUrl, const QString& apiKey, bool useMockMode)
{
    m_baseUrl = baseUrl;
    m_apiKey = apiKey;
    bool wasMockMode = m_useMockMode;
    m_useMockMode = useMockMode;
    
    if (m_apiClient)
    {
        m_apiClient->setBaseUrl(m_baseUrl);
        m_apiClient->setApiKey(m_apiKey);
    }
    
    // If mock mode changed and dashboard is visible
    if (m_dock && m_dock->isVisible())
    {
        if (useMockMode && !wasMockMode)
        {
            // Switch to mock mode
            if (m_apiClient)
                m_apiClient->stopPolling();
            if (m_mockTimer)
            {
                generateMockData();
                m_mockTimer->start();
            }
        }
        else if (!useMockMode && wasMockMode)
        {
            // Switch to real API
            if (m_mockTimer)
                m_mockTimer->stop();
            if (m_apiClient)
            {
                m_apiClient->requestStatus();
                m_apiClient->requestPipeline();
                m_apiClient->requestAssets();
                m_apiClient->requestLayoutAudit();
                m_apiClient->startPolling(2000);
            }
        }
    }
    
    saveSettings();
}

void GammaDashboardPlugin::loadSettings()
{
    QSettings settings;
    settings.beginGroup("GammaDashboard");
    
    m_baseUrl = settings.value("baseUrl", "http://localhost:8000").toString();
    m_apiKey = settings.value("apiKey", "").toString();
    m_useMockMode = settings.value("useMockMode", false).toBool();
    
    // Environment variables take precedence
    QString envUrl = qEnvironmentVariable("GAMMA_BASE_URL");
    if (!envUrl.isEmpty())
        m_baseUrl = envUrl;
    
    QString envKey = qEnvironmentVariable("GAMMA_API_KEY");
    if (!envKey.isEmpty())
        m_apiKey = envKey;
    
    settings.endGroup();
}

void GammaDashboardPlugin::saveSettings()
{
    QSettings settings;
    settings.beginGroup("GammaDashboard");
    
    settings.setValue("baseUrl", m_baseUrl);
    settings.setValue("apiKey", m_apiKey);
    settings.setValue("useMockMode", m_useMockMode);
    
    settings.endGroup();
}

// Plugin export functions (required by Scribus)
extern "C" PLUGIN_API int gamma_dashboard_getPluginAPIVersion()
{
    return PLUGIN_API_VERSION;
}

extern "C" PLUGIN_API ScPlugin* gamma_dashboard_getPlugin()
{
    try {
        return new GammaDashboardPlugin();
    } catch (...) {
        // Catch any exceptions during instantiation
        return nullptr;
    }
}

extern "C" PLUGIN_API void gamma_dashboard_freePlugin(ScPlugin* plugin)
{
    delete plugin;
}

void GammaDashboardPlugin::generateMockData()
{
    if (!m_dock)
        return;
    
    // Generate and process mock data
    handleStatusReceived(createMockStatusResponse());
    handlePipelineReceived(createMockPipelineResponse());
    handleAssetsReceived(createMockAssetsResponse());
    handleLayoutAuditReceived(createMockLayoutAuditResponse());
}

QJsonObject GammaDashboardPlugin::createMockStatusResponse()
{
    QJsonObject obj;
    obj["status"] = "connected";
    obj["latency_ms"] = 30 + QRandomGenerator::global()->bounded(20); // 30-50ms
    obj["version"] = "1.0.0";
    obj["timestamp"] = QDateTime::currentDateTimeUtc().toString(Qt::ISODate);
    return obj;
}

QJsonObject GammaDashboardPlugin::createMockPipelineResponse()
{
    QJsonObject pipeline;
    pipeline["id"] = "pipeline-001";
    pipeline["name"] = "Default Pipeline";
    
    // Simulate progress (0-100%)
    static int mockProgress = 0;
    mockProgress = (mockProgress + 2) % 101;
    
    pipeline["status"] = mockProgress < 100 ? "running" : "completed";
    pipeline["progress"] = mockProgress;
    pipeline["current_step"] = mockProgress < 50 ? "validation" : (mockProgress < 80 ? "rendering" : "finalization");
    
    QJsonObject obj;
    QJsonArray pipelines;
    pipelines.append(pipeline);
    obj["pipelines"] = pipelines;
    
    return obj;
}

QJsonObject GammaDashboardPlugin::createMockAssetsResponse()
{
    QJsonObject obj;
    obj["total_assets"] = 150;
    
    // Simulate validated assets
    static int mockValidated = 100;
    mockValidated = qMin(150, mockValidated + 1);
    
    obj["validated_assets"] = mockValidated;
    obj["progress_percent"] = (mockValidated * 100) / 150;
    obj["text_fit_progress"] = 15 + QRandomGenerator::global()->bounded(5); // 15-20%
    
    return obj;
}

QJsonObject GammaDashboardPlugin::createMockLayoutAuditResponse()
{
    QJsonObject obj;
    
    // Z-Order Guard
    QJsonObject zOrder;
    zOrder["status"] = "passed";
    zOrder["message"] = "Z-order validation successful";
    obj["z_order_guard"] = zOrder;
    
    // Overlaps
    QJsonObject overlaps;
    overlaps["status"] = "passed";
    overlaps["count"] = 0;
    overlaps["message"] = "No overlaps detected";
    obj["overlaps"] = overlaps;
    
    // Low-Res Images (sometimes warning)
    QJsonObject lowRes;
    int lowResCount = QRandomGenerator::global()->bounded(5); // 0-4
    lowRes["status"] = lowResCount == 0 ? "passed" : "warning";
    lowRes["count"] = lowResCount;
    lowRes["message"] = lowResCount == 0 ? "All images have sufficient resolution" 
                                         : QString("%1 low-resolution images detected").arg(lowResCount);
    obj["low_res_images"] = lowRes;
    
    // Font Issues
    QJsonObject fonts;
    fonts["status"] = "passed";
    fonts["count"] = 0;
    obj["font_issues"] = fonts;
    
    return obj;
}
