#include "gamma_api_settings_dialog.h"
#include "gamma_api_client.h"

#include <QFormLayout>
#include <QHBoxLayout>
#include <QVBoxLayout>
#include <QLineEdit>
#include <QPushButton>
#include <QLabel>
#include <QCheckBox>
#include <QComboBox>
#include <QDialogButtonBox>
#include <QMessageBox>
#include <QUrl>
#include <QTimer>
#include <QGroupBox>
#include <QDesktopServices>

GammaApiSettingsDialog::GammaApiSettingsDialog(QWidget* parent)
    : QDialog(parent)
    , m_providerCombo(nullptr)
    , m_urlEdit(nullptr)
    , m_apiKeyEdit(nullptr)
    , m_apiKeyHint(nullptr)
    , m_mockModeCheckBox(nullptr)
    , m_testButton(nullptr)
    , m_statusLabel(nullptr)
{
    setWindowTitle("Gamma Dashboard - API Settings");
    setMinimumWidth(550);
    setupUI();
}

GammaApiSettingsDialog::~GammaApiSettingsDialog() = default;

void GammaApiSettingsDialog::setupUI()
{
    QVBoxLayout* mainLayout = new QVBoxLayout(this);
    QFormLayout* formLayout = new QFormLayout();

    // LLM Provider Selection
    m_providerCombo = new QComboBox(this);
    m_providerCombo->addItem("Backend API (Standard)", "backend");
    m_providerCombo->addItem("OpenAI (GPT-4, GPT-3.5)", "openai");
    m_providerCombo->addItem("Google Gemini", "gemini");
    m_providerCombo->addItem("Anthropic Claude", "anthropic");
    m_providerCombo->addItem("Ollama (Lokal)", "ollama");
    m_providerCombo->addItem("LM Studio (Lokal)", "lmstudio");
    m_providerCombo->addItem("Benutzerdefiniert", "custom");
    m_providerCombo->setCurrentIndex(0);
    connect(m_providerCombo, QOverload<int>::of(&QComboBox::currentIndexChanged),
            this, &GammaApiSettingsDialog::onProviderChanged);
    formLayout->addRow("LLM Provider:", m_providerCombo);

    // Base URL
    m_urlEdit = new QLineEdit(this);
    m_urlEdit->setPlaceholderText("http://localhost:8003");
    formLayout->addRow("Backend URL:", m_urlEdit);

    // API Key
    m_apiKeyEdit = new QLineEdit(this);
    m_apiKeyEdit->setEchoMode(QLineEdit::Password);
    m_apiKeyEdit->setPlaceholderText("Enter API key");
    formLayout->addRow("API Key:", m_apiKeyEdit);

    // API Key Hint
    m_apiKeyHint = new QLabel("", this);
    m_apiKeyHint->setWordWrap(true);
    m_apiKeyHint->setStyleSheet("color: #666; font-size: 10pt; font-style: italic;");
    m_apiKeyHint->setTextFormat(Qt::RichText);
    m_apiKeyHint->setOpenExternalLinks(true);
    formLayout->addRow("", m_apiKeyHint);

    // Mock Mode
    m_mockModeCheckBox = new QCheckBox("Use Mock Mode (for testing)", this);
    m_mockModeCheckBox->setToolTip("When enabled, plugin uses mock data instead of connecting to backend");
    formLayout->addRow("", m_mockModeCheckBox);

    mainLayout->addLayout(formLayout);
    
    // Initial provider hints
    updateProviderHints();

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

QString GammaApiSettingsDialog::provider() const
{
    return m_providerCombo->currentData().toString();
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

void GammaApiSettingsDialog::setProvider(const QString& provider)
{
    int index = m_providerCombo->findData(provider);
    if (index >= 0) {
        m_providerCombo->setCurrentIndex(index);
        updateProviderHints();
    }
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
        QMessageBox::warning(this, "Invalid Settings", "Please enter a valid URL (e.g., http://localhost:8003)");
        return;
    }

    emit settingsChanged(url, apiKey(), provider(), useMockMode());
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

void GammaApiSettingsDialog::onProviderChanged(int index)
{
    Q_UNUSED(index);
    updateProviderHints();
}

void GammaApiSettingsDialog::updateProviderHints()
{
    QString provider = m_providerCombo->currentData().toString();
    QString currentUrl = m_urlEdit->text().trimmed();
    bool shouldAutoFillUrl = currentUrl.isEmpty() || currentUrl == m_urlEdit->placeholderText();
    
    if (provider == "backend") {
        if (shouldAutoFillUrl) m_urlEdit->setText("http://localhost:8003");
        m_urlEdit->setPlaceholderText("http://localhost:8003");
        m_apiKeyEdit->setPlaceholderText("Optional: Backend API key");
        m_apiKeyEdit->setEnabled(true);
        m_apiKeyHint->setText("<small>Verbindet sich mit dem lokalen Backend-Server. API-Key ist optional.</small>");
    }
    else if (provider == "openai") {
        if (shouldAutoFillUrl) m_urlEdit->setText("https://api.openai.com/v1");
        m_urlEdit->setPlaceholderText("https://api.openai.com/v1");
        m_apiKeyEdit->setPlaceholderText("sk-... (OpenAI API Key)");
        m_apiKeyEdit->setEnabled(true);
        m_apiKeyHint->setText("<small>API-Key erhalten: <a href='https://platform.openai.com/api-keys'>platform.openai.com/api-keys</a></small>");
    }
    else if (provider == "gemini") {
        if (shouldAutoFillUrl) m_urlEdit->setText("https://generativelanguage.googleapis.com/v1");
        m_urlEdit->setPlaceholderText("https://generativelanguage.googleapis.com/v1");
        m_apiKeyEdit->setPlaceholderText("AIza... (Google Gemini API Key)");
        m_apiKeyEdit->setEnabled(true);
        m_apiKeyHint->setText("<small>API-Key erhalten: <a href='https://makersuite.google.com/app/apikey'>makersuite.google.com/app/apikey</a></small>");
    }
    else if (provider == "anthropic") {
        if (shouldAutoFillUrl) m_urlEdit->setText("https://api.anthropic.com/v1");
        m_urlEdit->setPlaceholderText("https://api.anthropic.com/v1");
        m_apiKeyEdit->setPlaceholderText("sk-ant-... (Anthropic API Key)");
        m_apiKeyEdit->setEnabled(true);
        m_apiKeyHint->setText("<small>API-Key erhalten: <a href='https://console.anthropic.com/'>console.anthropic.com</a></small>");
    }
    else if (provider == "ollama") {
        if (shouldAutoFillUrl) m_urlEdit->setText("http://localhost:11434");
        m_urlEdit->setPlaceholderText("http://localhost:11434");
        m_apiKeyEdit->setText("");
        m_apiKeyEdit->setPlaceholderText("Nicht erforderlich (lokal)");
        m_apiKeyEdit->setEnabled(false);
        m_apiKeyHint->setText("<small>Lokale Ollama-Installation. Installiere Modelle mit: <code>ollama pull llama2</code></small>");
    }
    else if (provider == "lmstudio") {
        if (shouldAutoFillUrl) m_urlEdit->setText("http://localhost:1234");
        m_urlEdit->setPlaceholderText("http://localhost:1234");
        m_apiKeyEdit->setPlaceholderText("lm-studio (oder leer)");
        m_apiKeyEdit->setEnabled(true);
        m_apiKeyHint->setText("<small>Lokale LM Studio-Installation. Stelle sicher, dass der Server läuft.</small>");
    }
    else { // custom
        if (shouldAutoFillUrl) m_urlEdit->clear();
        m_urlEdit->setPlaceholderText("https://your-custom-api.com");
        m_apiKeyEdit->setPlaceholderText("Enter your API key");
        m_apiKeyEdit->setEnabled(true);
        m_apiKeyHint->setText("<small>Benutzerdefinierter LLM-Endpunkt. Konfiguriere URL und API-Key nach Bedarf.</small>");
    }
}

