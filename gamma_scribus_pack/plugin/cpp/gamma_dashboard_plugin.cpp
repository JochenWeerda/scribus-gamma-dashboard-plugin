#include "gamma_dashboard_plugin.h"
#include "gamma_dashboard_dock.h"
#include "gamma_api_client.h"
#include "gamma_debug_log.h"
#include "gamma_api_settings_dialog.h"
#include "gamma_figma_browser.h"
#include "gamma_sla_inserter.h"

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
#include <QFile>
#include <QFileInfo>
#include <QInputDialog>
#include <QTextStream>
#include <QDebug>

#include "pluginapi.h"
#include "scplugin.h"
// Use the real Scribus main window type to avoid unsafe casts
#include "scribus.h"
#include "actionmanager.h"
#include "ui/scmwmenumanager.h"

namespace {
QString cleanMenuText(const QString& text)
{
    QString out = text;
    out.remove('&');
    return out.trimmed();
}
}

GammaDashboardPlugin::GammaDashboardPlugin()
    : ScActionPlugin()
    , m_action(nullptr)
    , m_settingsAction(nullptr)
    , m_importFigmaAction(nullptr)
    , m_exportFigmaAction(nullptr)
    , m_apiClient(nullptr)
    , m_figmaBrowser(nullptr)
    , m_slaInserter(nullptr)
    , m_mockTimer(nullptr)
    , m_baseUrl("http://localhost:8003")
    , m_apiKey()
    , m_llmProvider("backend")
    , m_useMockMode(false)
{
    // #region agent log
    QFile logFile(gamma_dashboard::debug_log::logPath());
    if (logFile.open(QIODevice::Append | QIODevice::Text)) {
        QTextStream out(&logFile);
        out << QString("{\"id\":\"log_%1\",\"timestamp\":%2,\"location\":\"gamma_dashboard_plugin.cpp:35\",\"message\":\"Constructor called\",\"data\":{\"type\":\"GammaDashboardPlugin\"},\"sessionId\":\"debug-session\",\"runId\":\"run2\",\"hypothesisId\":\"A\"}\n")
            .arg(QDateTime::currentMSecsSinceEpoch())
            .arg(QDateTime::currentMSecsSinceEpoch());
        logFile.close();
    }
    // #endregion

    // Set action info in languageChange, so we only have to do it in one place.
    // IMPORTANT: This must be called in the constructor, otherwise m_actionInfo.text
    // will be null when Scribus calls actionInfo() during plugin registration.
    languageChange();

    // Create API Client
    m_apiClient = new GammaApiClient(this);
    connect(m_apiClient, &GammaApiClient::ragLLMContextReceived, this,
            [this](const QString& enhancedPrompt, const QJsonObject& contextData) {
                if (!m_dock)
                    return;

                m_dock->appendLog("RAG context received");
                if (!enhancedPrompt.isEmpty())
                    m_dock->appendLog(QString("Enhanced prompt: %1").arg(enhancedPrompt.left(200)));

                const QJsonDocument doc(contextData);
                const QString json = QString::fromUtf8(doc.toJson(QJsonDocument::Compact));
                if (!json.isEmpty())
                    m_dock->appendLog(QString("Context: %1").arg(json.left(400)));
            });
     
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
    connect(m_apiClient, &GammaApiClient::ragImagesForTextReceived,
            this, &GammaDashboardPlugin::handleRAGImagesForTextReceived);
    connect(m_apiClient, &GammaApiClient::ragTextsForImageReceived,
            this, &GammaDashboardPlugin::handleRAGTextsForImageReceived);
    connect(m_apiClient, &GammaApiClient::ragSuggestPairsReceived,
            this, &GammaDashboardPlugin::handleRAGSuggestPairsReceived);
    connect(m_apiClient, &GammaApiClient::workflowJobCreated,
            this, &GammaDashboardPlugin::handleWorkflowJobCreated);

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
    // #region agent log
    QFile logFile(gamma_dashboard::debug_log::logPath());
    if (logFile.open(QIODevice::Append | QIODevice::Text)) {
        QTextStream out(&logFile);
        out << QString("{\"id\":\"log_%1\",\"timestamp\":%2,\"location\":\"gamma_dashboard_plugin.cpp:84\",\"message\":\"initPlugin called\",\"data\":{},\"sessionId\":\"debug-session\",\"runId\":\"run1\",\"hypothesisId\":\"D\"}\n")
            .arg(QDateTime::currentMSecsSinceEpoch())
            .arg(QDateTime::currentMSecsSinceEpoch());
        logFile.close();
    }
    // #endregion

    // API Client is already initialized in constructor
    // Menu integration happens in addToMainWindowMenu()
    return true;
}

bool GammaDashboardPlugin::cleanupPlugin()
{
    if (m_apiClient)
        m_apiClient->stopPolling();
    if (m_mockTimer)
        m_mockTimer->stop();
    if (m_dock)
    {
        delete m_dock;
        m_dock = nullptr;
    }
    saveSettings();
    return true;
}

void GammaDashboardPlugin::languageChange()
{
    // #region agent log
    QFile logFile(gamma_dashboard::debug_log::logPath());
    if (logFile.open(QIODevice::Append | QIODevice::Text)) {
        QTextStream out(&logFile);
        out << QString("{\"id\":\"log_%1\",\"timestamp\":%2,\"location\":\"gamma_dashboard_plugin.cpp:101\",\"message\":\"languageChange called\",\"data\":{},\"sessionId\":\"debug-session\",\"runId\":\"run2\",\"hypothesisId\":\"B\"}\n")
            .arg(QDateTime::currentMSecsSinceEpoch())
            .arg(QDateTime::currentMSecsSinceEpoch());
        logFile.close();
    }
    // #endregion

    // Set ActionInfo for ScActionPlugin menu integration
    m_actionInfo.name = "GammaDashboard";
    m_actionInfo.text = tr("Gamma Dashboard");
    m_actionInfo.helpText = tr("Open the Gamma Dashboard panel for pipeline monitoring and control.");
    // Try setting both menu and parentMenu (like subdivide plugin does)
    m_actionInfo.menu = "Extras";
    // Note: parentMenu might be needed - leaving empty for now to test
    m_actionInfo.enabledOnStartup = true;
    m_actionInfo.needsNumObjects = -1; // No objects needed
    
    // #region agent log
    if (logFile.open(QIODevice::Append | QIODevice::Text)) {
        QTextStream out(&logFile);
        out << QString("{\"id\":\"log_%1\",\"timestamp\":%2,\"location\":\"gamma_dashboard_plugin.cpp:157\",\"message\":\"m_actionInfo set\",\"data\":{\"name\":\"%3\",\"menu\":\"%4\",\"text\":\"%5\",\"textIsNull\":%6},\"sessionId\":\"debug-session\",\"runId\":\"run2\",\"hypothesisId\":\"C\"}\n")
            .arg(QDateTime::currentMSecsSinceEpoch())
            .arg(QDateTime::currentMSecsSinceEpoch())
            .arg(m_actionInfo.name)
            .arg(m_actionInfo.menu)
            .arg(m_actionInfo.text)
            .arg(m_actionInfo.text.isNull() ? "true" : "false");
        logFile.close();
    }
    // #endregion
    
    // Update manual menu actions if they exist
    if (m_action)
        m_action->setText(tr("Gamma Dashboard"));
    if (m_settingsAction)
        m_settingsAction->setText(tr("Gamma Dashboard Settings..."));
}

QString GammaDashboardPlugin::fullTrName() const
{
    return tr("Gamma Dashboard");
}

void GammaDashboardPlugin::addToMainWindowMenu(ScribusMainWindow* mw)
{
    // IMPORTANT: This method is called BEFORE menu rebuild in PluginManager::setupPluginActions()
    // After this call, Scribus calls clearMenu("Extras") and rebuilds it via addMenuItemStringsToMenuBar()
    // Therefore, we must make our Settings action idempotent and re-add it after rebuilds
    // The action will be re-added on next call to this method (e.g., after language change)
    
    // #region agent log
    QFile logFile(gamma_dashboard::debug_log::logPath());
    if (logFile.open(QIODevice::Append | QIODevice::Text)) {
        QTextStream out(&logFile);
        out << QString("{\"id\":\"log_%1\",\"timestamp\":%2,\"location\":\"gamma_dashboard_plugin.cpp:178\",\"message\":\"addToMainWindowMenu called\",\"data\":{\"mw\":\"%3\"},\"sessionId\":\"debug-session\",\"runId\":\"run3\",\"hypothesisId\":\"E\"}\n")
            .arg(QDateTime::currentMSecsSinceEpoch())
            .arg(QDateTime::currentMSecsSinceEpoch())
            .arg(mw ? "not null" : "null");
        logFile.close();
    }
    // #endregion

    // ScActionPlugin handles menu integration automatically via m_actionInfo
    // This method is used for additional manual menu entries (like Settings)
    if (!mw)
        return;

    // Use ScribusMainWindow API directly (scribus.h included)
    QMenuBar* bar = mw->menuBar();
    if (!bar) {
        // #region agent log
        if (logFile.open(QIODevice::Append | QIODevice::Text)) {
            QTextStream out(&logFile);
            out << QString("{\"id\":\"log_%1\",\"timestamp\":%2,\"location\":\"gamma_dashboard_plugin.cpp:205\",\"message\":\"menuBar is null\",\"data\":{},\"sessionId\":\"debug-session\",\"runId\":\"run3\",\"hypothesisId\":\"K\"}\n")
                .arg(QDateTime::currentMSecsSinceEpoch())
                .arg(QDateTime::currentMSecsSinceEpoch());
            logFile.close();
        }
        // #endregion
        return;
    }

    // DEBUG: Log all top-level menus with titles and objectNames
    qDebug() << "GammaDashboard: Top-level menus:";
    QStringList menuDebugInfo;
    for (QAction* a : bar->actions()) {
        if (!a) continue;
        QMenu* m = a->menu();
        if (!m) continue;
        const QString titleClean = cleanMenuText(m->title());
        const QString titleRaw = m->title();
        const QString objName = m->objectName();
        qDebug() << "  -" << titleClean << "| titleRaw=" << titleRaw << "| obj=" << objName;
        menuDebugInfo << QString("%1 (raw:%2, obj:%3)").arg(titleClean, titleRaw, objName);
    }

    // Find Extras menu by title (robust, localization-tolerant)
    // Do NOT rely on findChild("menuExtras") - objectName is not guaranteed
    QMenu* extrasMenu = nullptr;
    QStringList menuNames;
    for (QAction* a : bar->actions()) {
        if (!a) continue;
        QMenu* m = a->menu();
        if (!m) continue;
        
        const QString menuTitle = cleanMenuText(m->title());
        menuNames << menuTitle;
        if (menuTitle.compare("Extras", Qt::CaseInsensitive) == 0 ||
            menuTitle.compare("Extra", Qt::CaseInsensitive) == 0) {
            extrasMenu = m;
            break;
        }
    }

    // #region agent log
    if (logFile.open(QIODevice::Append | QIODevice::Text)) {
        QTextStream out(&logFile);
        out << QString("{\"id\":\"log_%1\",\"timestamp\":%2,\"location\":\"gamma_dashboard_plugin.cpp:230\",\"message\":\"Menu search complete\",\"data\":{\"extrasMenuFound\":%3,\"menuCount\":%4,\"menuNames\":\"%5\"},\"sessionId\":\"debug-session\",\"runId\":\"run3\",\"hypothesisId\":\"L\"}\n")
            .arg(QDateTime::currentMSecsSinceEpoch())
            .arg(QDateTime::currentMSecsSinceEpoch())
            .arg(extrasMenu ? "true" : "false")
            .arg(menuNames.size())
            .arg(menuNames.join(", "));
        logFile.close();
    }
    // #endregion

    if (!extrasMenu) {
        // Log available menus for debugging
        qWarning() << "GammaDashboard: Extras menu not found. Top-level menus:";
        for (const QString& name : menuNames) {
            qWarning() << " -" << name;
        }
        // #region agent log
        if (logFile.open(QIODevice::Append | QIODevice::Text)) {
            QTextStream out(&logFile);
            out << QString("{\"id\":\"log_%1\",\"timestamp\":%2,\"location\":\"gamma_dashboard_plugin.cpp:243\",\"message\":\"Extras menu not found\",\"data\":{\"availableMenus\":\"%3\"},\"sessionId\":\"debug-session\",\"runId\":\"run3\",\"hypothesisId\":\"M\"}\n")
                .arg(QDateTime::currentMSecsSinceEpoch())
                .arg(QDateTime::currentMSecsSinceEpoch())
                .arg(menuNames.join(", "));
            logFile.close();
        }
        // #endregion
        return;
    }

    // DEBUG: Log all actions in Extras menu (for anchor detection)
    qDebug() << "GammaDashboard: Extras menu actions:";
    QStringList extrasActionsDebug;
    for (QAction* a : extrasMenu->actions()) {
        if (!a) continue;
        const QString text = a->text();
        const QString textClean = cleanMenuText(text);
        const QString objName = a->objectName();
        const bool isSep = a->isSeparator();
        qDebug() << "  * sep=" << isSep << "| text=" << text << "| textClean=" << textClean << "| obj=" << objName;
        if (!isSep) {
            extrasActionsDebug << QString("%1 (obj:%2)").arg(textClean, objName);
        }
    }

    // Post-rebuild-sichere Registrierung der Settings-Aktion
    const QString settingsActionName = "GammaDashboardSettings";
    auto ensureSettings = [this, mw, settingsActionName]()
    {
        // 1) ScrAction persistent registrieren (falls noch nicht vorhanden)
        ScrAction* act = qobject_cast<ScrAction*>(mw->scrActions.value(settingsActionName, nullptr));
        if (!act)
        {
            act = new ScrAction(
                ScrAction::ActionDLL,
                QString(), QString(),
                tr("Gamma Dashboard Settings..."),
                QKeySequence(),
                mw
            );
            Q_CHECK_PTR(act);
            act->setStatusTip(tr("Open Gamma Dashboard settings"));
            act->setToolTip(tr("Configure Gamma Dashboard connection and behavior"));
            act->setObjectName("GammaDashboardSettingsAction");
            connect(act, &QAction::triggered, this, &GammaDashboardPlugin::showSettingsDialog);
            mw->scrActions.insert(settingsActionName, act);
        }
        m_settingsAction = act;

        // 2) Menü-String (idempotent) registrieren
        mw->scrMenuMgr->addMenuItemString(settingsActionName, "Extras");

        // 3) Optional sofort anwenden, damit es ohne globalen Rebuild sichtbar wird
        mw->scrMenuMgr->addMenuItemStringsToMenuBar("Extras", mw->scrActions);
    };

    // Einmal jetzt ausführen
    ensureSettings();
    // Und einmal direkt nach dem (potenziellen) Rebuild
    QTimer::singleShot(0, mw, ensureSettings);

    // Figma Actions hinzufügen
    const QString importFigmaActionName = "GammaDashboardImportFigma";
    const QString exportFigmaActionName = "GammaDashboardExportFigma";
    
    auto ensureFigmaActions = [this, mw, importFigmaActionName, exportFigmaActionName]()
    {
        // Import Figma Action
        ScrAction* importAct = qobject_cast<ScrAction*>(mw->scrActions.value(importFigmaActionName, nullptr));
        if (!importAct)
        {
            importAct = new ScrAction(
                ScrAction::ActionDLL,
                QString(), QString(),
                tr("Import Frame from Figma..."),
                QKeySequence(),
                mw
            );
            Q_CHECK_PTR(importAct);
            importAct->setStatusTip(tr("Import a Figma frame as a new page"));
            importAct->setToolTip(tr("Browse Figma files and import a frame"));
            importAct->setObjectName("GammaDashboardImportFigmaAction");
            connect(importAct, &QAction::triggered, this, &GammaDashboardPlugin::onImportFrameFromFigma);
            mw->scrActions.insert(importFigmaActionName, importAct);
        }
        m_importFigmaAction = importAct;
        mw->scrMenuMgr->addMenuItemString(importFigmaActionName, "Extras");

        // Export Figma Action
        ScrAction* exportAct = qobject_cast<ScrAction*>(mw->scrActions.value(exportFigmaActionName, nullptr));
        if (!exportAct)
        {
            exportAct = new ScrAction(
                ScrAction::ActionDLL,
                QString(), QString(),
                tr("Export Page to Figma..."),
                QKeySequence(),
                mw
            );
            Q_CHECK_PTR(exportAct);
            exportAct->setStatusTip(tr("Export current page to Figma"));
            exportAct->setToolTip(tr("Export the current Scribus page as a Figma frame"));
            exportAct->setObjectName("GammaDashboardExportFigmaAction");
            connect(exportAct, &QAction::triggered, this, &GammaDashboardPlugin::onExportPageToFigma);
            mw->scrActions.insert(exportFigmaActionName, exportAct);
        }
        m_exportFigmaAction = exportAct;
        mw->scrMenuMgr->addMenuItemString(exportFigmaActionName, "Extras");

        // Menü aktualisieren
        mw->scrMenuMgr->addMenuItemStringsToMenuBar("Extras", mw->scrActions);
    };

    // Einmal jetzt ausführen
    ensureFigmaActions();
    // Und einmal direkt nach dem (potenziellen) Rebuild
    QTimer::singleShot(0, mw, ensureFigmaActions);
}

bool GammaDashboardPlugin::run(ScribusDoc* doc, const QString& target)
{
    Q_UNUSED(doc);
    Q_UNUSED(target);
    
    // This is called when the menu action is triggered
    toggleDashboard();
    return true;
}

bool GammaDashboardPlugin::newPrefsPanelWidget(QWidget* parent, Prefs_Pane*& panel)
{
    Q_UNUSED(parent);
    Q_UNUSED(panel);
    return false; // Kein Prefs-Panel
}

void GammaDashboardPlugin::setDoc(ScribusDoc* doc)
{
    // Store reference to current document
    // This is called by Scribus when a document is opened/activated
    m_currentDoc = doc;
    
    if (m_dock && doc)
    {
        m_dock->appendLog("Document set");
    }
}

void GammaDashboardPlugin::unsetDoc()
{
    // Clear reference when document is closed
    m_currentDoc = nullptr;
    
    if (m_dock)
    {
        m_dock->appendLog("Document unset");
    }
}

void GammaDashboardPlugin::changedDoc(ScribusDoc* doc)
{
    Q_UNUSED(doc);
    // Plugin does not react to document changes
}

const ScActionPlugin::AboutData* GammaDashboardPlugin::getAboutData() const
{
    ScActionPlugin::AboutData* about = new ScActionPlugin::AboutData;
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

void GammaDashboardPlugin::deleteAboutData(const ScActionPlugin::AboutData* about) const
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
        connect(m_dock, &GammaDashboardDock::workflowRunRequested, this, &GammaDashboardPlugin::onWorkflowRunBundle);
        connect(m_dock, &GammaDashboardDock::findImagesForTextRequested, this, &GammaDashboardPlugin::onFindImagesForText);
        connect(m_dock, &GammaDashboardDock::findTextsForImageRequested, this, &GammaDashboardPlugin::onFindTextsForImage);
        connect(m_dock, &GammaDashboardDock::suggestTextImagePairsRequested, this, &GammaDashboardPlugin::onSuggestTextImagePairs);
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

void GammaDashboardPlugin::handleRAGImagesForTextReceived(const QJsonArray& images)
{
    if (m_dock)
    {
        m_dock->appendLog(QString("RAG: Found %1 images").arg(images.size()));
        for (int i = 0; i < qMin(images.size(), 5); ++i)
        {
            QJsonObject img = images[i].toObject();
            QString path = img.value("path").toString();
            double similarity = img.value("similarity").toDouble(0.0);
            m_dock->appendLog(QString("  - %1 (similarity: %2)").arg(path).arg(similarity, 0, 'f', 2));
        }
    }
}

void GammaDashboardPlugin::handleRAGTextsForImageReceived(const QJsonArray& texts)
{
    if (m_dock)
    {
        m_dock->appendLog(QString("RAG: Found %1 texts").arg(texts.size()));
        for (int i = 0; i < qMin(texts.size(), 5); ++i)
        {
            QJsonObject text = texts[i].toObject();
            QString content = text.value("content").toString();
            double similarity = text.value("similarity").toDouble(0.0);
            m_dock->appendLog(QString("  - %1 (similarity: %2)").arg(content.left(50)).arg(similarity, 0, 'f', 2));
        }
    }
}

void GammaDashboardPlugin::handleRAGSuggestPairsReceived(const QJsonArray& suggestions)
{
    if (m_dock)
    {
        m_dock->appendLog(QString("RAG: Suggested %1 text-image pairs").arg(suggestions.size()));
        for (int i = 0; i < qMin(suggestions.size(), 5); ++i)
        {
            QJsonObject pair = suggestions[i].toObject();
            QString textId = pair.value("textId").toString();
            QString imageId = pair.value("imageId").toString();
            double similarity = pair.value("similarity").toDouble(0.0);
            m_dock->appendLog(QString("  - Text %1 ↔ Image %2 (similarity: %3)")
                             .arg(textId).arg(imageId).arg(similarity, 0, 'f', 2));
        }
    }
}

void GammaDashboardPlugin::onImportFrameFromFigma()
{
    if (!m_figmaBrowser)
    {
        m_figmaBrowser = new GammaFigmaBrowser(resolveMainWindow(), m_apiClient);
        connect(m_figmaBrowser, &GammaFigmaBrowser::frameImportRequested,
                this, &GammaDashboardPlugin::onFigmaFrameImportRequested);
    }
    else
    {
        // API Client aktualisieren (falls geändert)
        m_figmaBrowser->setApiClient(m_apiClient);
    }

    if (m_figmaBrowser)
    {
        m_figmaBrowser->show();
        m_figmaBrowser->raise();
        m_figmaBrowser->activateWindow();
    }
}

void GammaDashboardPlugin::onExportPageToFigma()
{
    // TODO: Implementierung für Export
    // 1. Aktuelle Seite als Layout JSON extrahieren
    // 2. API Call zu /api/figma/frames/export
    // 3. Figma Browser öffnen für Frame-Auswahl
    
    if (m_dock)
    {
        m_dock->appendLog("Export to Figma: Not yet implemented");
    }
}

void GammaDashboardPlugin::onFigmaFrameImportRequested(const QString& fileKey, const QString& frameId)
{
    if (m_dock)
    {
        m_dock->appendLog(QString("Importing Figma frame: %1/%2").arg(fileKey, frameId));
    }

    if (!m_apiClient)
    {
        if (m_dock)
            m_dock->appendLog("Error: API Client not initialized");
        return;
    }

    // Verbinde Signal für Import-Response
    connect(m_apiClient, &GammaApiClient::figmaFrameImportReceived,
            this, [this](const QJsonObject& result) {
                if (m_dock)
                {
                    QString layoutId = result.value("layout_id").toString();
                    int slaSize = result.value("sla_xml_size").toInt(0);
                    m_dock->appendLog(QString("Figma import successful: Layout ID %1, SLA size: %2 bytes")
                                     .arg(layoutId).arg(slaSize));
                    
                    // SLA XML aus Response extrahieren
                    QString slaXmlHex = result.value("sla_xml_bytes").toString();
                    if (!slaXmlHex.isEmpty())
                    {
                        // Hex → Bytes konvertieren
                        QByteArray slaXmlBytes = QByteArray::fromHex(slaXmlHex.toUtf8());
                        
                        // SLA in Scribus einfügen
                        if (m_slaInserter)
                        {
                            // Verwende aktuelles Dokument (via setDoc() gesetzt)
                            ScribusDoc* doc = m_currentDoc;
                            
                            int pageNumber = result.value("page_number").toInt(1);
                            
                            if (doc)
                            {
                                // Versuche SLA direkt einzufügen
                                bool success = m_slaInserter->insertSLAAsPage(doc, slaXmlBytes, pageNumber);
                                if (!success)
                                {
                                    // Fallback: Als temporäre Datei speichern
                                    m_slaInserter->loadSLATempFile(slaXmlBytes);
                                    if (m_dock)
                                    {
                                        m_dock->appendLog("SLA saved to temp file (direct insert failed)");
                                    }
                                }
                            }
                            else
                            {
                                // Kein Dokument geöffnet: Als temporäre Datei speichern
                                bool success = m_slaInserter->loadSLATempFile(slaXmlBytes);
                                if (success && m_dock)
                                {
                                    m_dock->appendLog("SLA saved to temp file (no document open). Please open document first.");
                                }
                            }
                        }
                    }
                    else
                    {
                        m_dock->appendLog("Warning: No SLA XML in response");
                    }
                }
            }, Qt::UniqueConnection);

    // API Call zu /api/figma/frames/import
    m_apiClient->requestFigmaFrameImport(fileKey, frameId, 300, 1);
}

void GammaDashboardPlugin::onFindImagesForText()
{
    if (!m_apiClient)
    {
        if (m_dock)
            m_dock->appendLog("RAG: API client not initialized");
        return;
    }

    if (m_useMockMode)
    {
        if (m_dock)
            m_dock->appendLog("RAG: mock mode active (no backend calls)");
        return;
    }

    bool ok = false;
    const QString query = QInputDialog::getText(resolveMainWindow(),
                                                tr("Find Images For Text"),
                                                tr("Text query:"),
                                                QLineEdit::Normal,
                                                QString(),
                                                &ok).trimmed();
    if (!ok || query.isEmpty())
        return;

    if (m_dock)
        m_dock->appendLog(QString("RAG: find images for text: %1").arg(query.left(200)));

    m_apiClient->requestFindImagesForText(query, /*topK=*/8);
}

void GammaDashboardPlugin::onFindTextsForImage()
{
    if (!m_apiClient)
    {
        if (m_dock)
            m_dock->appendLog("RAG: API client not initialized");
        return;
    }

    if (m_useMockMode)
    {
        if (m_dock)
            m_dock->appendLog("RAG: mock mode active (no backend calls)");
        return;
    }

    bool ok = false;
    const QString query = QInputDialog::getText(resolveMainWindow(),
                                                tr("Find Texts For Image"),
                                                tr("Describe the image (or paste an image caption / filename):"),
                                                QLineEdit::Normal,
                                                QString(),
                                                &ok).trimmed();
    if (!ok || query.isEmpty())
        return;

    if (m_dock)
        m_dock->appendLog(QString("RAG: find texts for image: %1").arg(query.left(200)));

    m_apiClient->requestFindTextsForImage(query, /*topK=*/8);
}

void GammaDashboardPlugin::onSuggestTextImagePairs()
{
    if (!m_apiClient)
    {
        if (m_dock)
            m_dock->appendLog("RAG: API client not initialized");
        return;
    }

    if (m_useMockMode)
    {
        if (m_dock)
            m_dock->appendLog("RAG: mock mode active (no backend calls)");
        return;
    }

    // Für jetzt: Verwende aktuelles Dokument als Layout JSON
    // TODO: Extrahiere Layout JSON aus aktueller Scribus-Seite
    QJsonObject layoutJson;
    
    if (m_currentDoc)
    {
        // TODO: Konvertiere ScribusDoc zu Layout JSON
        // Für jetzt: Leeres Layout JSON
        layoutJson["document"] = QJsonObject();
        layoutJson["pages"] = QJsonArray();
    }
    else
    {
        if (m_dock)
            m_dock->appendLog("RAG: No document open - cannot suggest pairs");
        return;
    }

    if (m_dock)
        m_dock->appendLog("RAG: Suggesting text-image pairs for current layout...");

    m_apiClient->requestSuggestTextImagePairs(layoutJson);
}

void GammaDashboardPlugin::onWorkflowRunBundle(const QString& bundleZipPath)
{
    if (!m_apiClient)
    {
        if (m_dock)
            m_dock->appendLog("Workflow: API client not initialized");
        return;
    }

    if (m_useMockMode)
    {
        if (m_dock)
            m_dock->appendLog("Workflow: mock mode active (no backend calls)");
        return;
    }

    if (bundleZipPath.isEmpty())
        return;

    if (m_dock)
        m_dock->appendLog(QString("Workflow: uploading bundle and starting job: %1").arg(QFileInfo(bundleZipPath).fileName()));

    m_apiClient->requestWorkflowRun(bundleZipPath);
}

void GammaDashboardPlugin::handleWorkflowJobCreated(const QJsonObject& job)
{
    if (!m_dock)
        return;

    const QString id = job.value("id").toString();
    const QString status = job.value("status").toString();
    const QString jobType = job.value("job_type").toString();
    m_dock->appendLog(QString("Workflow job created: id=%1 type=%2 status=%3").arg(id, jobType, status));
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
    dialog.setProvider(m_llmProvider);
    dialog.setUseMockMode(m_useMockMode);
    
    connect(&dialog, &GammaApiSettingsDialog::settingsChanged,
            this, &GammaDashboardPlugin::onSettingsChanged);
    
    dialog.exec();
}

void GammaDashboardPlugin::onSettingsChanged(const QString& baseUrl, const QString& apiKey, const QString& provider, bool useMockMode)
{
    m_baseUrl = baseUrl;
    m_apiKey = apiKey;
    m_llmProvider = provider;
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
    
    m_baseUrl = settings.value("baseUrl", "http://localhost:8003").toString();
    m_apiKey = settings.value("apiKey", "").toString();
    m_llmProvider = settings.value("llmProvider", "backend").toString();
    m_useMockMode = settings.value("useMockMode", false).toBool();
    
    // Environment variables take precedence over settings
    QString envUrl = qEnvironmentVariable("GAMMA_BASE_URL");
    if (!envUrl.isEmpty()) {
        m_baseUrl = envUrl;
    }
    
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
    settings.setValue("llmProvider", m_llmProvider);
    settings.setValue("useMockMode", m_useMockMode);
    
    settings.endGroup();
}

// Plugin export functions are in gamma_dashboard_exports.cpp

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
