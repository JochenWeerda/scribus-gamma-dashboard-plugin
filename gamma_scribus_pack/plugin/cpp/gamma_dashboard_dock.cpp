#include "gamma_dashboard_dock.h"

#include <QFrame>
#include <QHBoxLayout>
#include <QLabel>
#include <QLineEdit>
#include <QProgressBar>
#include <QPushButton>
#include <QTextEdit>
#include <QComboBox>
#include <QVBoxLayout>
#include <QFileDialog>

namespace {
QFrame* makeCard(QWidget* parent)
{
    QFrame* card = new QFrame(parent);
    card->setObjectName("gammaCard");
    card->setFrameShape(QFrame::StyledPanel);
    card->setFrameShadow(QFrame::Plain);
    return card;
}
}

GammaDashboardDock::GammaDashboardDock(QWidget* parent)
    : QDockWidget(parent)
    , m_statusDot(nullptr)
    , m_statusText(nullptr)
    , m_settingsButton(nullptr)
    , m_pipelineStartButton(nullptr)
    , m_pipelineStopButton(nullptr)
    , m_pipelineProgress(nullptr)
    , m_pipelineSelect(nullptr)
    , m_logView(nullptr)
    , m_configPathLabel(nullptr)
    , m_findImagesForTextButton(nullptr)
    , m_findTextsForImageButton(nullptr)
    , m_suggestPairsButton(nullptr)
    , m_workflowRunButton(nullptr)
{
    setObjectName("GammaDashboardDock");
    setWindowTitle("Gamma Dashboard");

    setupUI();
}

void GammaDashboardDock::setupUI()
{
    QWidget* root = new QWidget(this);
    root->setObjectName("gammaRoot");

    QVBoxLayout* main = new QVBoxLayout(root);
    main->setContentsMargins(12, 12, 12, 12);
    main->setSpacing(10);

    // Header mit Status und Settings-Button
    QHBoxLayout* header = new QHBoxLayout();
    QLabel* title = new QLabel("Gamma Dashboard", root);
    title->setObjectName("gammaTitle");

    m_statusDot = new QLabel(root);
    m_statusDot->setFixedSize(10, 10);
    m_statusDot->setObjectName("gammaStatusDot");

    m_statusText = new QLabel("Disconnected", root);
    m_statusText->setObjectName("gammaStatusText");

    m_settingsButton = new QPushButton("Settings", root);
    m_settingsButton->setObjectName("gammaSettingsButton");
    m_settingsButton->setToolTip("Open API Settings");
    m_settingsButton->setMinimumWidth(80);
    m_settingsButton->setMaximumWidth(100);

    header->addWidget(title);
    header->addStretch(1);
    header->addWidget(m_statusDot);
    header->addWidget(m_statusText);
    header->addWidget(m_settingsButton);
    main->addLayout(header);

    // Pipeline Control Card
    QFrame* pipelineCard = makeCard(root);
    QVBoxLayout* pipelineLayout = new QVBoxLayout(pipelineCard);
    QLabel* pipelineTitle = new QLabel("Pipeline Control", pipelineCard);
    
    m_pipelineSelect = new QComboBox(pipelineCard);
    m_pipelineSelect->addItem("Gamma → Scribus Pipeline");
    m_pipelineSelect->setObjectName("gammaPipelineSelect");
    
    QHBoxLayout* buttonRow = new QHBoxLayout();
    m_pipelineStartButton = new QPushButton("Start Pipeline", pipelineCard);
    m_pipelineStartButton->setObjectName("gammaPipelineStart");
    m_pipelineStopButton = new QPushButton("Stop Pipeline", pipelineCard);
    m_pipelineStopButton->setObjectName("gammaPipelineStop");
    m_pipelineStopButton->setEnabled(false);
    
    buttonRow->addWidget(m_pipelineStartButton);
    buttonRow->addWidget(m_pipelineStopButton);
    
    m_pipelineProgress = new QProgressBar(pipelineCard);
    m_pipelineProgress->setRange(0, 100);
    m_pipelineProgress->setValue(0);
    m_pipelineProgress->setObjectName("gammaPipelineProgress");
    
    pipelineLayout->addWidget(pipelineTitle);
    pipelineLayout->addWidget(m_pipelineSelect);
    pipelineLayout->addLayout(buttonRow);
    pipelineLayout->addWidget(m_pipelineProgress);
    main->addWidget(pipelineCard);

    // Configuration Card with Settings Button
    QFrame* configCard = makeCard(root);
    QVBoxLayout* configLayout = new QVBoxLayout(configCard);
    QHBoxLayout* configHeader = new QHBoxLayout();
    QLabel* configTitle = new QLabel("Configuration", configCard);
    QPushButton* configSettingsButton = new QPushButton("API Settings", configCard);
    configSettingsButton->setObjectName("gammaConfigSettingsButton");
    configSettingsButton->setMaximumWidth(120);
    configHeader->addWidget(configTitle);
    configHeader->addStretch();
    configHeader->addWidget(configSettingsButton);
    
    m_configPathLabel = new QLabel("Config path: (not set)", configCard);
    m_configPathLabel->setWordWrap(true);
    configLayout->addLayout(configHeader);
    configLayout->addWidget(m_configPathLabel);

    m_workflowRunButton = new QPushButton("Run Workflow Bundle…", configCard);
    m_workflowRunButton->setObjectName("gammaWorkflowRunButton");
    m_workflowRunButton->setToolTip("Select a workflow bundle ZIP and start the end-to-end pipeline in the backend");
    configLayout->addWidget(m_workflowRunButton);
    main->addWidget(configCard);
    
    // Connect config settings button to same slot
    connect(configSettingsButton, &QPushButton::clicked, this, &GammaDashboardDock::onSettingsClicked);

    // RAG Text-Image Matching Card
    QFrame* ragCard = makeCard(root);
    QVBoxLayout* ragLayout = new QVBoxLayout(ragCard);
    QLabel* ragTitle = new QLabel("RAG Text-Image Matching", ragCard);
    
    m_findImagesForTextButton = new QPushButton("Find Images for Text", ragCard);
    m_findImagesForTextButton->setObjectName("gammaRAGFindImages");
    m_findImagesForTextButton->setToolTip("Find matching images for selected text object");
    
    m_findTextsForImageButton = new QPushButton("Find Texts for Image", ragCard);
    m_findTextsForImageButton->setObjectName("gammaRAGFindTexts");
    m_findTextsForImageButton->setToolTip("Find matching texts for selected image object");
    
    m_suggestPairsButton = new QPushButton("Suggest Text-Image Pairs", ragCard);
    m_suggestPairsButton->setObjectName("gammaRAGSuggestPairs");
    m_suggestPairsButton->setToolTip("Suggest text-image pairings for current page");
    
    ragLayout->addWidget(ragTitle);
    ragLayout->addWidget(m_findImagesForTextButton);
    ragLayout->addWidget(m_findTextsForImageButton);
    ragLayout->addWidget(m_suggestPairsButton);
    main->addWidget(ragCard);

    // Log Viewer
    QFrame* logCard = makeCard(root);
    QVBoxLayout* logLayout = new QVBoxLayout(logCard);
    QLabel* logTitle = new QLabel("Log Viewer", logCard);
    m_logView = new QTextEdit(logCard);
    m_logView->setReadOnly(true);
    m_logView->setObjectName("gammaLogView");
    logLayout->addWidget(logTitle);
    logLayout->addWidget(m_logView);
    main->addWidget(logCard);

    main->addStretch(1);

    setWidget(root);

    // Connections
    connect(m_pipelineStartButton, &QPushButton::clicked, this, &GammaDashboardDock::onPipelineStartClicked);
    connect(m_pipelineStopButton, &QPushButton::clicked, this, &GammaDashboardDock::onPipelineStopClicked);
    connect(m_settingsButton, &QPushButton::clicked, this, &GammaDashboardDock::onSettingsClicked);
    connect(m_findImagesForTextButton, &QPushButton::clicked, this, &GammaDashboardDock::onFindImagesForTextClicked);
    connect(m_findTextsForImageButton, &QPushButton::clicked, this, &GammaDashboardDock::onFindTextsForImageClicked);
    connect(m_suggestPairsButton, &QPushButton::clicked, this, &GammaDashboardDock::onSuggestTextImagePairsClicked);
    connect(m_workflowRunButton, &QPushButton::clicked, this, &GammaDashboardDock::onWorkflowRunClicked);

    // Styling (dunkles Theme, ähnlich MCP Dashboard)
    root->setStyleSheet(
        "QWidget#gammaRoot { background-color: #1f2328; color: #e6edf3; }"
        "QFrame#gammaCard { background-color: #0f1318; border: 1px solid #2a2f36; border-radius: 8px; padding: 8px; }"
        "QLabel#gammaTitle { font-size: 14px; font-weight: 600; }"
        "QLabel#gammaStatusDot { border-radius: 5px; background-color: #c0392b; }"
        "QPushButton#gammaSettingsButton { background-color: #3498db; color: #ffffff; padding: 4px 8px; border-radius: 4px; font-weight: 500; }"
        "QPushButton#gammaSettingsButton:hover { background-color: #2980b9; }"
        "QPushButton#gammaSettingsButton { background-color: #3498db; color: #ffffff; padding: 4px 8px; border-radius: 4px; font-weight: 500; }"
        "QPushButton#gammaSettingsButton:hover { background-color: #2980b9; }"
        "QPushButton#gammaConfigSettingsButton { background-color: #3498db; color: #ffffff; padding: 4px 8px; border-radius: 4px; font-weight: 500; }"
        "QPushButton#gammaConfigSettingsButton:hover { background-color: #2980b9; }"
        "QPushButton#gammaWorkflowRunButton { background-color: #9b59b6; color: #ffffff; padding: 6px 10px; border-radius: 6px; font-weight: 600; }"
        "QPushButton#gammaWorkflowRunButton:hover { background-color: #8e44ad; }"
        "QPushButton#gammaPipelineStart { background-color: #2ecc71; color: #ffffff; padding: 6px 10px; border-radius: 6px; }"
        "QPushButton#gammaPipelineStop { background-color: #e74c3c; color: #ffffff; padding: 6px 10px; border-radius: 6px; }"
        "QProgressBar#gammaPipelineProgress { background-color: #2a2f36; border: 1px solid #2a2f36; border-radius: 4px; height: 8px; }"
        "QProgressBar#gammaPipelineProgress::chunk { background-color: #3498db; }"
        "QTextEdit#gammaLogView { background-color: #0b0f14; color: #c9d1d9; border: 1px solid #2a2f36; font-family: 'Consolas', 'Monaco', monospace; }"
        "QComboBox#gammaPipelineSelect { background-color: #0b0f14; color: #c9d1d9; border: 1px solid #2a2f36; padding: 4px; }"
        "QPushButton { background-color: #2a2f36; color: #e6edf3; border-radius: 6px; padding: 6px 10px; }"
        "QPushButton:hover { background-color: #3a3f46; }"
        "QPushButton:disabled { background-color: #1a1f26; color: #6a6f76; }"
    );

    setStatus(false, -1);
    appendLog("Gamma Dashboard initialized");
}

void GammaDashboardDock::setStatus(bool connected, int latencyMs)
{
    QString color = connected ? "#2ecc71" : "#c0392b";
    m_statusDot->setStyleSheet(QString("border-radius:5px; background-color:%1;").arg(color));
    if (connected)
    {
        if (latencyMs >= 0)
            m_statusText->setText(QString("Connected (%1 ms)").arg(latencyMs));
        else
            m_statusText->setText("Connected");
    }
    else
    {
        m_statusText->setText("Disconnected");
    }
}

void GammaDashboardDock::setPipelineProgress(int value)
{
    if (m_pipelineProgress)
        m_pipelineProgress->setValue(value);
}

void GammaDashboardDock::appendLog(const QString& line)
{
    if (!m_logView)
        return;
    m_logView->append(line);
}

void GammaDashboardDock::onPipelineStartClicked()
{
    if (m_pipelineStartButton)
        m_pipelineStartButton->setEnabled(false);
    if (m_pipelineStopButton)
        m_pipelineStopButton->setEnabled(true);
    emit pipelineStartRequested();
}

void GammaDashboardDock::onPipelineStopClicked()
{
    if (m_pipelineStartButton)
        m_pipelineStartButton->setEnabled(true);
    if (m_pipelineStopButton)
        m_pipelineStopButton->setEnabled(false);
    emit pipelineStopRequested();
}

void GammaDashboardDock::onSettingsClicked()
{
    emit settingsRequested();
}

void GammaDashboardDock::onFindImagesForTextClicked()
{
    emit findImagesForTextRequested();
}

void GammaDashboardDock::onFindTextsForImageClicked()
{
    emit findTextsForImageRequested();
}

void GammaDashboardDock::onSuggestTextImagePairsClicked()
{
    emit suggestTextImagePairsRequested();
}

void GammaDashboardDock::onWorkflowRunClicked()
{
    const QString zipPath = QFileDialog::getOpenFileName(
        this,
        tr("Select Workflow Bundle ZIP"),
        QString(),
        tr("ZIP files (*.zip)")
    );
    if (zipPath.isEmpty())
        return;

    appendLog(QString("Selected workflow bundle: %1").arg(zipPath));
    emit workflowRunRequested(zipPath);
}

