#include "gamma_figma_browser.h"
#include "gamma_api_client.h"
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QMessageBox>
#include <QUrl>
#include <QDesktopServices>

GammaFigmaBrowser::GammaFigmaBrowser(QWidget* parent, GammaApiClient* apiClient)
    : QDialog(parent)
    , m_selectedFileKey()
    , m_selectedFrameId()
    , m_isAuthenticated(false)
    , m_apiClient(apiClient)
{
    setWindowTitle("Figma Browser");
    setMinimumSize(800, 600);
    resize(900, 700);

    setupUI();
    
    // Verbinde API Client Signals
    if (m_apiClient)
    {
        connect(m_apiClient, &GammaApiClient::figmaFilesReceived,
                this, [this](const QJsonArray& files) {
                    updateFileList(files);
                    m_statusLabel->setText(QString("Files loaded: %1").arg(files.size()));
                });
        connect(m_apiClient, &GammaApiClient::figmaFramesReceived,
                this, [this](const QString& fileKey, const QJsonArray& frames) {
                    if (fileKey == m_selectedFileKey)
                    {
                        updateFrameList(frames);
                        m_statusLabel->setText(QString("Frames loaded: %1").arg(frames.size()));
                    }
                });
    }
    
    // Authentifizierung prüfen (Token aus ENV)
    m_isAuthenticated = true;  // Personal Access Token wird aus ENV verwendet
    m_statusLabel->setText("Authenticated (Personal Access Token)");
    m_loginButton->setEnabled(false);
    
    loadFiles();
}

void GammaFigmaBrowser::setApiClient(GammaApiClient* client)
{
    m_apiClient = client;
    
    if (m_apiClient)
    {
        connect(m_apiClient, &GammaApiClient::figmaFilesReceived,
                this, [this](const QJsonArray& files) {
                    updateFileList(files);
                    m_statusLabel->setText(QString("Files loaded: %1").arg(files.size()));
                });
        connect(m_apiClient, &GammaApiClient::figmaFramesReceived,
                this, [this](const QString& fileKey, const QJsonArray& frames) {
                    if (fileKey == m_selectedFileKey)
                    {
                        updateFrameList(frames);
                        m_statusLabel->setText(QString("Frames loaded: %1").arg(frames.size()));
                    }
                });
    }
}

GammaFigmaBrowser::~GammaFigmaBrowser()
{
}

void GammaFigmaBrowser::setupUI()
{
    QVBoxLayout* mainLayout = new QVBoxLayout(this);

    // Header mit Login
    QHBoxLayout* headerLayout = new QHBoxLayout();
    m_loginButton = new QPushButton("Login to Figma", this);
    m_statusLabel = new QLabel("Not authenticated", this);
    headerLayout->addWidget(m_loginButton);
    headerLayout->addWidget(m_statusLabel);
    headerLayout->addStretch();
    mainLayout->addLayout(headerLayout);

    // Files und Frames (Side by Side)
    QHBoxLayout* contentLayout = new QHBoxLayout();

    // Files List
    QVBoxLayout* filesLayout = new QVBoxLayout();
    QLabel* filesLabel = new QLabel("Figma Files:", this);
    m_filesList = new QListWidget(this);
    m_refreshFilesButton = new QPushButton("Refresh", this);
    filesLayout->addWidget(filesLabel);
    filesLayout->addWidget(m_filesList);
    filesLayout->addWidget(m_refreshFilesButton);

    // Frames List
    QVBoxLayout* framesLayout = new QVBoxLayout();
    QLabel* framesLabel = new QLabel("Frames:", this);
    m_framesList = new QListWidget(this);
    m_refreshFramesButton = new QPushButton("Refresh", this);
    m_refreshFramesButton->setEnabled(false);
    framesLayout->addWidget(framesLabel);
    framesLayout->addWidget(m_framesList);
    framesLayout->addWidget(m_refreshFramesButton);

    contentLayout->addLayout(filesLayout, 1);
    contentLayout->addLayout(framesLayout, 1);
    mainLayout->addLayout(contentLayout);

    // Buttons
    QHBoxLayout* buttonLayout = new QHBoxLayout();
    buttonLayout->addStretch();
    m_importButton = new QPushButton("Import Frame", this);
    m_importButton->setEnabled(false);
    m_cancelButton = new QPushButton("Cancel", this);
    buttonLayout->addWidget(m_importButton);
    buttonLayout->addWidget(m_cancelButton);
    mainLayout->addLayout(buttonLayout);

    // Connections
    connect(m_loginButton, &QPushButton::clicked, this, &GammaFigmaBrowser::onLoginClicked);
    connect(m_filesList, &QListWidget::itemClicked, this, &GammaFigmaBrowser::onFileSelected);
    connect(m_framesList, &QListWidget::itemClicked, this, &GammaFigmaBrowser::onFrameSelected);
    connect(m_importButton, &QPushButton::clicked, this, &GammaFigmaBrowser::onImportClicked);
    connect(m_refreshFilesButton, &QPushButton::clicked, this, &GammaFigmaBrowser::onRefreshFilesClicked);
    connect(m_refreshFramesButton, &QPushButton::clicked, this, &GammaFigmaBrowser::onRefreshFramesClicked);
    connect(m_cancelButton, &QPushButton::clicked, this, &QDialog::reject);
}

void GammaFigmaBrowser::onLoginClicked()
{
    // Personal Access Token wird aus ENV verwendet
    // OAuth Flow kann später implementiert werden
    m_isAuthenticated = true;
    m_statusLabel->setText("Authenticated (Personal Access Token)");
    m_loginButton->setEnabled(false);
    loadFiles();
}

void GammaFigmaBrowser::loadFiles()
{
    if (!m_isAuthenticated) {
        return;
    }

    m_statusLabel->setText("Loading files...");

    if (m_apiClient)
    {
        // Echter API Call
        m_apiClient->requestFigmaFiles();
    }
    else
    {
        // Fallback: Mock (für Entwicklung)
        QJsonArray mockFiles;
        QJsonObject file1;
        file1["key"] = "abc123";
        file1["name"] = "Magazine Template";
        file1["last_modified"] = "2024-01-01T00:00:00Z";
        mockFiles.append(file1);
        
        updateFileList(mockFiles);
        m_statusLabel->setText("Files loaded (mock)");
    }
}

void GammaFigmaBrowser::updateFileList(const QJsonArray& files)
{
    m_filesList->clear();

    for (const QJsonValue& value : files) {
        QJsonObject file = value.toObject();
        QString name = file["name"].toString();
        QString key = file["key"].toString();
        QString lastModified = file["last_modified"].toString();

        QString itemText = QString("%1\n  Key: %2\n  Modified: %3")
            .arg(name)
            .arg(key)
            .arg(lastModified);

        QListWidgetItem* item = new QListWidgetItem(itemText, m_filesList);
        item->setData(Qt::UserRole, key);
        m_filesList->addItem(item);
    }
}

void GammaFigmaBrowser::onFileSelected(QListWidgetItem* item)
{
    if (!item) {
        return;
    }

    m_selectedFileKey = item->data(Qt::UserRole).toString();
    m_refreshFramesButton->setEnabled(true);
    loadFrames(m_selectedFileKey);
}

void GammaFigmaBrowser::loadFrames(const QString& fileKey)
{
    if (fileKey.isEmpty()) {
        return;
    }

    m_statusLabel->setText("Loading frames...");

    if (m_apiClient)
    {
        // Echter API Call
        m_apiClient->requestFigmaFrames(fileKey);
    }
    else
    {
        // Fallback: Mock (für Entwicklung)
        QJsonArray mockFrames;
        QJsonObject frame1;
        frame1["id"] = "123:456";
        frame1["name"] = "Doppelseite 1";
        frame1["path"] = "/Doppelseite 1";
        mockFrames.append(frame1);

        QJsonObject frame2;
        frame2["id"] = "123:789";
        frame2["name"] = "Doppelseite 2";
        frame2["path"] = "/Doppelseite 2";
        mockFrames.append(frame2);

        updateFrameList(mockFrames);
        m_statusLabel->setText("Frames loaded (mock)");
    }
}

void GammaFigmaBrowser::updateFrameList(const QJsonArray& frames)
{
    m_framesList->clear();

    for (const QJsonValue& value : frames) {
        QJsonObject frame = value.toObject();
        QString name = frame["name"].toString();
        QString id = frame["id"].toString();
        QString path = frame["path"].toString();

        QString itemText = QString("%1\n  ID: %2\n  Path: %3")
            .arg(name)
            .arg(id)
            .arg(path);

        QListWidgetItem* item = new QListWidgetItem(itemText, m_framesList);
        item->setData(Qt::UserRole, id);
        m_framesList->addItem(item);
    }
}

void GammaFigmaBrowser::onFrameSelected(QListWidgetItem* item)
{
    if (!item) {
        m_importButton->setEnabled(false);
        return;
    }

    m_selectedFrameId = item->data(Qt::UserRole).toString();
    m_importButton->setEnabled(!m_selectedFileKey.isEmpty() && !m_selectedFrameId.isEmpty());
}

void GammaFigmaBrowser::onImportClicked()
{
    if (m_selectedFileKey.isEmpty() || m_selectedFrameId.isEmpty()) {
        QMessageBox::warning(this, "Import", "Please select a file and frame");
        return;
    }

    emit frameImportRequested(m_selectedFileKey, m_selectedFrameId);
    accept();
}

void GammaFigmaBrowser::onRefreshFilesClicked()
{
    loadFiles();
}

void GammaFigmaBrowser::onRefreshFramesClicked()
{
    if (!m_selectedFileKey.isEmpty()) {
        loadFrames(m_selectedFileKey);
    }
}

