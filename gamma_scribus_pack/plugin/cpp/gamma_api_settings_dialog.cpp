#include "gamma_api_settings_dialog.h"
#include "gamma_api_client.h"

#include <QFormLayout>
#include <QHBoxLayout>
#include <QVBoxLayout>
#include <QLineEdit>
#include <QPushButton>
#include <QLabel>
#include <QCheckBox>
#include <QDialogButtonBox>
#include <QMessageBox>
#include <QUrl>
#include <QTimer>

GammaApiSettingsDialog::GammaApiSettingsDialog(QWidget* parent)
    : QDialog(parent)
    , m_urlEdit(nullptr)
    , m_apiKeyEdit(nullptr)
    , m_mockModeCheckBox(nullptr)
    , m_testButton(nullptr)
    , m_statusLabel(nullptr)
{
    setWindowTitle("Gamma Dashboard - API Settings");
    setMinimumWidth(500);
    setupUI();
}

GammaApiSettingsDialog::~GammaApiSettingsDialog() = default;

void GammaApiSettingsDialog::setupUI()
{
    QVBoxLayout* mainLayout = new QVBoxLayout(this);
    QFormLayout* formLayout = new QFormLayout();

    // Base URL
    m_urlEdit = new QLineEdit(this);
    m_urlEdit->setPlaceholderText("http://localhost:8000");
    formLayout->addRow("Backend URL:", m_urlEdit);

    // API Key
    m_apiKeyEdit = new QLineEdit(this);
    m_apiKeyEdit->setEchoMode(QLineEdit::Password);
    m_apiKeyEdit->setPlaceholderText("Enter API key (optional)");
    formLayout->addRow("API Key:", m_apiKeyEdit);

    // Mock Mode
    m_mockModeCheckBox = new QCheckBox("Use Mock Mode (for testing)", this);
    m_mockModeCheckBox->setToolTip("When enabled, plugin uses mock data instead of connecting to backend");
    formLayout->addRow("", m_mockModeCheckBox);

    mainLayout->addLayout(formLayout);

    // Status Label
    m_statusLabel = new QLabel("", this);
    m_statusLabel->setWordWrap(true);
    m_statusLabel->setStyleSheet("color: #666; font-style: italic;");
    mainLayout->addWidget(m_statusLabel);

    // Test Connection Button
    m_testButton = new QPushButton("Test Connection", this);
    connect(m_testButton, &QPushButton::clicked, this, &GammaApiSettingsDialog::onTestConnectionClicked);
    mainLayout->addWidget(m_testButton);

    mainLayout->addStretch();

    // Dialog Buttons
    QDialogButtonBox* buttonBox = new QDialogButtonBox(
        QDialogButtonBox::Ok | QDialogButtonBox::Cancel,
        Qt::Horizontal,
        this
    );
    connect(buttonBox, &QDialogButtonBox::accepted, this, &GammaApiSettingsDialog::onOkClicked);
    connect(buttonBox, &QDialogButtonBox::rejected, this, &GammaApiSettingsDialog::onCancelClicked);
    mainLayout->addWidget(buttonBox);
}

QString GammaApiSettingsDialog::baseUrl() const
{
    return m_urlEdit->text().trimmed();
}

QString GammaApiSettingsDialog::apiKey() const
{
    return m_apiKeyEdit->text();
}

bool GammaApiSettingsDialog::useMockMode() const
{
    return m_mockModeCheckBox->isChecked();
}

void GammaApiSettingsDialog::setBaseUrl(const QString& url)
{
    m_urlEdit->setText(url);
}

void GammaApiSettingsDialog::setApiKey(const QString& key)
{
    m_apiKeyEdit->setText(key);
}

void GammaApiSettingsDialog::setUseMockMode(bool useMock)
{
    m_mockModeCheckBox->setChecked(useMock);
}

void GammaApiSettingsDialog::onTestConnectionClicked()
{
    QString url = baseUrl();
    
    if (url.isEmpty())
    {
        m_statusLabel->setText("Error: URL cannot be empty");
        m_statusLabel->setStyleSheet("color: red;");
        return;
    }

    if (!validateUrl(url))
    {
        m_statusLabel->setText("Error: Invalid URL format");
        m_statusLabel->setStyleSheet("color: red;");
        return;
    }

    m_statusLabel->setText("Testing connection...");
    m_statusLabel->setStyleSheet("color: blue;");
    m_testButton->setEnabled(false);

    // Create temporary API client for test
    GammaApiClient* testClient = new GammaApiClient(this);
    testClient->setBaseUrl(url);
    if (!apiKey().isEmpty())
        testClient->setApiKey(apiKey());

    // Test-Request
    QTimer::singleShot(5000, this, [this]() {
        m_statusLabel->setText("Connection timeout - Backend might not be running");
        m_statusLabel->setStyleSheet("color: orange;");
        m_testButton->setEnabled(true);
    });

    connect(testClient, &GammaApiClient::connectionStatusChanged, this, [this](bool connected, int latency) {
        if (connected)
        {
            m_statusLabel->setText(QString("Connection successful! Latency: %1 ms").arg(latency));
            m_statusLabel->setStyleSheet("color: green;");
        }
        else
        {
            m_statusLabel->setText("Connection failed - Backend not reachable");
            m_statusLabel->setStyleSheet("color: red;");
        }
        m_testButton->setEnabled(true);
        sender()->deleteLater();
    });

    connect(testClient, &GammaApiClient::errorOccurred, this, [this](const QString& error, int) {
        m_statusLabel->setText(QString("Connection error: %1").arg(error));
        m_statusLabel->setStyleSheet("color: red;");
        m_testButton->setEnabled(true);
        sender()->deleteLater();
    });

    testClient->requestStatus();
}

void GammaApiSettingsDialog::onOkClicked()
{
    QString url = baseUrl();
    
    if (url.isEmpty())
    {
        QMessageBox::warning(this, "Invalid Settings", "Backend URL cannot be empty");
        return;
    }

    if (!validateUrl(url) && !useMockMode())
    {
        QMessageBox::warning(this, "Invalid Settings", "Please enter a valid URL (e.g., http://localhost:8000)");
        return;
    }

    emit settingsChanged(url, apiKey(), useMockMode());
    accept();
}

void GammaApiSettingsDialog::onCancelClicked()
{
    reject();
}

bool GammaApiSettingsDialog::validateUrl(const QString& url) const
{
    QUrl qurl(url);
    return qurl.isValid() && !qurl.scheme().isEmpty() && !qurl.host().isEmpty();
}

