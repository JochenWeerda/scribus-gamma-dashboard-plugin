#pragma once

#include <QDialog>
#include <QLineEdit>
#include <QListWidget>
#include <QPushButton>
#include <QComboBox>
#include <QLabel>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QJsonDocument>
#include <QJsonArray>
#include <QJsonObject>

/**
 * GammaRAGSearchDialog
 * 
 * Dialog für RAG-Suche nach ähnlichen Layouts.
 * Unterstützt Text-Query oder Layout-JSON-Upload.
 */
class GammaApiClient;

class GammaRAGSearchDialog : public QDialog
{
    Q_OBJECT

public:
    explicit GammaRAGSearchDialog(QWidget* parent = nullptr, GammaApiClient* apiClient = nullptr);
    ~GammaRAGSearchDialog();

    QJsonObject selectedLayout() const { return m_selectedLayout; }
    
    void setApiClient(GammaApiClient* client);

public slots:
    void onSearchClicked();
    void onUploadLayoutClicked();
    void onResultSelected(QListWidgetItem* item);
    void onUseAsTemplateClicked();
    void onFilterChanged();

signals:
    void layoutSelected(const QJsonObject& layout);
    void templateRequested(const QJsonObject& layout);

private:
    void setupUI();
    void performSearch(const QString& query);
    void performLayoutSearch(const QJsonObject& layoutJson);
    void updateResults(const QJsonArray& layouts);
    void updateFilters();

    // UI Components
    QLineEdit* m_searchEdit;
    QPushButton* m_searchButton;
    QPushButton* m_uploadButton;
    QListWidget* m_resultsList;
    QComboBox* m_sourceFilter;
    QComboBox* m_dateFilter;
    QPushButton* m_useTemplateButton;
    QLabel* m_statusLabel;

    // Data
    QJsonArray m_currentResults;
    QJsonObject m_selectedLayout;
    GammaApiClient* m_apiClient;
};

