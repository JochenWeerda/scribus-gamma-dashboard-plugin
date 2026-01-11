#include "gamma_rag_search_dialog.h"
#include "gamma_api_client.h"
#include <QJsonArray>
#include <QJsonDocument>
#include <QFileDialog>
#include <QMessageBox>
#include <QDateTime>

GammaRAGSearchDialog::GammaRAGSearchDialog(QWidget* parent, GammaApiClient* apiClient)
    : QDialog(parent)
    , m_apiClient(apiClient)
{
    setupUI();
    
    // Verbinde API Client Signals
    if (m_apiClient)
    {
        // TODO: Signal für RAG-Results verbinden (wenn verfügbar)
    }
}

void GammaRAGSearchDialog::setApiClient(GammaApiClient* client)
{
    m_apiClient = client;
}

GammaRAGSearchDialog::~GammaRAGSearchDialog()
{
}

void GammaRAGSearchDialog::setupUI()
{
    setWindowTitle("RAG Layout Search");
    setMinimumSize(800, 600);
    resize(1000, 700);

    QVBoxLayout* mainLayout = new QVBoxLayout(this);

    // Search Section
    QHBoxLayout* searchLayout = new QHBoxLayout();
    m_searchEdit = new QLineEdit(this);
    m_searchEdit->setPlaceholderText("Search for similar layouts...");
    m_searchButton = new QPushButton("Search", this);
    m_uploadButton = new QPushButton("Upload Layout JSON", this);
    
    searchLayout->addWidget(m_searchEdit);
    searchLayout->addWidget(m_searchButton);
    searchLayout->addWidget(m_uploadButton);

    // Filters
    QHBoxLayout* filterLayout = new QHBoxLayout();
    filterLayout->addWidget(new QLabel("Source:", this));
    m_sourceFilter = new QComboBox(this);
    m_sourceFilter->addItem("All");
    m_sourceFilter->addItem("Figma");
    m_sourceFilter->addItem("Scribus");
    m_sourceFilter->addItem("LLM");
    filterLayout->addWidget(m_sourceFilter);
    
    filterLayout->addWidget(new QLabel("Date:", this));
    m_dateFilter = new QComboBox(this);
    m_dateFilter->addItem("All");
    m_dateFilter->addItem("Last 24 hours");
    m_dateFilter->addItem("Last week");
    m_dateFilter->addItem("Last month");
    filterLayout->addWidget(m_dateFilter);
    filterLayout->addStretch();

    // Results
    m_resultsList = new QListWidget(this);
    m_resultsList->setAlternatingRowColors(true);

    // Status
    m_statusLabel = new QLabel("Ready to search", this);

    // Buttons
    QHBoxLayout* buttonLayout = new QHBoxLayout();
    buttonLayout->addStretch();
    m_useTemplateButton = new QPushButton("Use as Template", this);
    m_useTemplateButton->setEnabled(false);
    QPushButton* closeButton = new QPushButton("Close", this);
    buttonLayout->addWidget(m_useTemplateButton);
    buttonLayout->addWidget(closeButton);

    // Assemble
    mainLayout->addLayout(searchLayout);
    mainLayout->addLayout(filterLayout);
    mainLayout->addWidget(m_resultsList);
    mainLayout->addWidget(m_statusLabel);
    mainLayout->addLayout(buttonLayout);

    // Connections
    connect(m_searchButton, &QPushButton::clicked, this, &GammaRAGSearchDialog::onSearchClicked);
    connect(m_uploadButton, &QPushButton::clicked, this, &GammaRAGSearchDialog::onUploadLayoutClicked);
    connect(m_resultsList, &QListWidget::itemClicked, this, &GammaRAGSearchDialog::onResultSelected);
    connect(m_useTemplateButton, &QPushButton::clicked, this, &GammaRAGSearchDialog::onUseAsTemplateClicked);
    connect(m_sourceFilter, QOverload<int>::of(&QComboBox::currentIndexChanged), this, &GammaRAGSearchDialog::onFilterChanged);
    connect(m_dateFilter, QOverload<int>::of(&QComboBox::currentIndexChanged), this, &GammaRAGSearchDialog::onFilterChanged);
    connect(closeButton, &QPushButton::clicked, this, &QDialog::accept);
}

void GammaRAGSearchDialog::onSearchClicked()
{
    QString query = m_searchEdit->text().trimmed();
    if (query.isEmpty()) {
        QMessageBox::warning(this, "Search", "Please enter a search query");
        return;
    }

    m_statusLabel->setText("Searching...");
    performSearch(query);
}

void GammaRAGSearchDialog::onUploadLayoutClicked()
{
    QString fileName = QFileDialog::getOpenFileName(
        this,
        "Select Layout JSON",
        "",
        "JSON Files (*.json)"
    );

    if (fileName.isEmpty()) {
        return;
    }

    QFile file(fileName);
    if (!file.open(QIODevice::ReadOnly)) {
        QMessageBox::critical(this, "Error", "Could not open file");
        return;
    }

    QByteArray data = file.readAll();
    QJsonDocument doc = QJsonDocument::fromJson(data);
    
    if (doc.isNull() || !doc.isObject()) {
        QMessageBox::critical(this, "Error", "Invalid JSON file");
        return;
    }

    m_statusLabel->setText("Searching similar layouts...");
    performLayoutSearch(doc.object());
}

void GammaRAGSearchDialog::performSearch(const QString& query)
{
    if (m_apiClient)
    {
        // TODO: API Call zu /api/rag/layouts/similar
        // Für jetzt: Mock (API-Endpoint muss noch in GammaApiClient hinzugefügt werden)
        m_statusLabel->setText("Searching... (API call pending)");
        
        // Mock für Entwicklung
        QJsonArray mockResults;
        QJsonObject mockLayout;
        mockLayout["layout_id"] = "layout_001";
        mockLayout["similarity"] = 0.85;
        mockLayout["source"] = "figma";
        mockLayout["document"] = "Layout: 2480x3508px, 1 page, 3 text objects, 2 images";
        mockResults.append(mockLayout);
        
        updateResults(mockResults);
        m_statusLabel->setText(QString("Found %1 results").arg(mockResults.size()));
    }
    else
    {
        QMessageBox::warning(this, "Search", "API Client not available");
    }
}

void GammaRAGSearchDialog::performLayoutSearch(const QJsonObject& layoutJson)
{
    // TODO: API Call zu /api/rag/layouts/similar mit layout_json
    // Für jetzt: Mock
    QJsonArray mockResults;
    QJsonObject mockLayout;
    mockLayout["layout_id"] = "layout_002";
    mockLayout["similarity"] = 0.92;
    mockLayout["source"] = "scribus";
    mockLayout["document"] = "Layout: 2480x3508px, 1 page, 2 text objects, 1 image";
    mockResults.append(mockLayout);

    updateResults(mockResults);
    m_statusLabel->setText(QString("Found %1 similar layouts").arg(mockResults.size()));
}

void GammaRAGSearchDialog::updateResults(const QJsonArray& layouts)
{
    m_resultsList->clear();
    m_currentResults = layouts;

    for (const QJsonValue& value : layouts) {
        QJsonObject layout = value.toObject();
        
        QString source = layout["source"].toString();
        double similarity = layout["similarity"].toDouble();
        QString doc = layout["document"].toString();
        QString layoutId = layout["layout_id"].toString();

        QString itemText = QString("[%1] Similarity: %2% | %3")
            .arg(source)
            .arg(similarity * 100, 0, 'f', 1)
            .arg(doc.left(80));

        QListWidgetItem* item = new QListWidgetItem(itemText, m_resultsList);
        item->setData(Qt::UserRole, layoutId);
        m_resultsList->addItem(item);
    }
}

void GammaRAGSearchDialog::onResultSelected(QListWidgetItem* item)
{
    if (!item) {
        m_useTemplateButton->setEnabled(false);
        return;
    }

    QString layoutId = item->data(Qt::UserRole).toString();
    
    // Finde Layout in currentResults
    for (const QJsonValue& value : m_currentResults) {
        QJsonObject layout = value.toObject();
        if (layout["layout_id"].toString() == layoutId) {
            m_selectedLayout = layout;
            m_useTemplateButton->setEnabled(true);
            break;
        }
    }
}

void GammaRAGSearchDialog::onUseAsTemplateClicked()
{
    if (m_selectedLayout.isEmpty()) {
        return;
    }

    emit templateRequested(m_selectedLayout);
    accept();
}

void GammaRAGSearchDialog::onFilterChanged()
{
    // TODO: Filtere Ergebnisse basierend auf Source und Date
    // Für jetzt: Nur UI-Update
    QString source = m_sourceFilter->currentText();
    QString date = m_dateFilter->currentText();
    
    m_statusLabel->setText(QString("Filter: %1, %2").arg(source, date));
}

