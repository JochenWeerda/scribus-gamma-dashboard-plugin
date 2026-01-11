#pragma once

#include <QDialog>

class QLineEdit;
class QPushButton;
class QLabel;
class QCheckBox;
class QComboBox;

/**
 * @brief Settings Dialog for Gamma Dashboard API Configuration
 */
class GammaApiSettingsDialog : public QDialog
{
    Q_OBJECT

public:
    explicit GammaApiSettingsDialog(QWidget* parent = nullptr);
    ~GammaApiSettingsDialog() override;

    QString baseUrl() const;
    QString apiKey() const;
    QString provider() const;
    bool useMockMode() const;

    void setBaseUrl(const QString& url);
    void setApiKey(const QString& key);
    void setProvider(const QString& provider);
    void setUseMockMode(bool useMock);

signals:
    void settingsChanged(const QString& baseUrl, const QString& apiKey, const QString& provider, bool useMockMode);

private slots:
    void onTestConnectionClicked();
    void onOkClicked();
    void onCancelClicked();

private:
    void setupUI();
    bool validateUrl(const QString& url) const;
    void onProviderChanged(int index);
    void updateProviderHints();

    QComboBox* m_providerCombo;
    QLineEdit* m_urlEdit;
    QLineEdit* m_apiKeyEdit;
    QLabel* m_apiKeyHint;
    QCheckBox* m_mockModeCheckBox;
    QPushButton* m_testButton;
    QLabel* m_statusLabel;
};

