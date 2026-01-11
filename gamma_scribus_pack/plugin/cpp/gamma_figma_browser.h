#pragma once

#include <QDialog>
#include <QListWidget>
#include <QPushButton>
#include <QLineEdit>
#include <QLabel>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QJsonObject>
#include <QJsonArray>

/**
 * GammaFigmaBrowser
 * 
 * Dialog für Figma File- und Frame-Auswahl.
 * Unterstützt OAuth-Login (Browser-Integration) und Frame-Import.
 */
class GammaApiClient;

class GammaFigmaBrowser : public QDialog
{
    Q_OBJECT

public:
    explicit GammaFigmaBrowser(QWidget* parent = nullptr, GammaApiClient* apiClient = nullptr);
    ~GammaFigmaBrowser();

    QString selectedFileKey() const { return m_selectedFileKey; }
    QString selectedFrameId() const { return m_selectedFrameId; }
    
    void setApiClient(GammaApiClient* client);

public slots:
    void onLoginClicked();
    void onFileSelected(QListWidgetItem* item);
    void onFrameSelected(QListWidgetItem* item);
    void onImportClicked();
    void onRefreshFilesClicked();
    void onRefreshFramesClicked();

signals:
    void frameImportRequested(const QString& fileKey, const QString& frameId);

private:
    void setupUI();
    void loadFiles();
    void loadFrames(const QString& fileKey);
    void updateFileList(const QJsonArray& files);
    void updateFrameList(const QJsonArray& frames);

    // UI Components
    QPushButton* m_loginButton;
    QLabel* m_statusLabel;
    QListWidget* m_filesList;
    QListWidget* m_framesList;
    QPushButton* m_refreshFilesButton;
    QPushButton* m_refreshFramesButton;
    QPushButton* m_importButton;
    QPushButton* m_cancelButton;

    // Data
    QString m_selectedFileKey;
    QString m_selectedFrameId;
    bool m_isAuthenticated;
    GammaApiClient* m_apiClient;
};

