#pragma once

#include <QObject>
#include <QString>
#include <QJsonObject>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QHttpMultiPart>
#include <QTimer>

/**
 * @brief API Client for Gamma Dashboard Backend
 * 
 * Responsible for all HTTP communication with the backend API server.
 * Provides methods for Status, Pipeline, Assets, and Layout-Audit.
 */
class GammaApiClient : public QObject
{
    Q_OBJECT

public:
    explicit GammaApiClient(QObject* parent = nullptr);
    ~GammaApiClient() override;

    // Configuration
    void setBaseUrl(const QString& url);
    QString baseUrl() const { return m_baseUrl; }
    
    void setApiKey(const QString& key);
    QString apiKey() const { return m_apiKey; }

    // Connection status
    bool isConnected() const { return m_connected; }
    int latencyMs() const { return m_latencyMs; }

    // API calls
    void requestStatus();
    void requestPipeline(const QString& pipelineId = QString());
    void requestAssets();
    void requestLayoutAudit();
    void startPipeline(const QString& pipelineId);
    void stopPipeline(const QString& pipelineId);

    // Workflow API calls
    void requestWorkflowRun(const QString& bundleZipPath, const QJsonObject& options = QJsonObject());
    
    // RAG API calls
    void requestRAGLLMContext(const QString& prompt, int topKLayouts = 3, int topKTexts = 5, int topKImages = 3);
    void requestFindImagesForText(const QString& text, int topK = 5);
    void requestFindTextsForImage(const QString& imagePath, int topK = 5);
    void requestSuggestTextImagePairs(const QJsonObject& layoutJson);
    
    // Figma API calls
    void requestFigmaFiles();
    void requestFigmaFrames(const QString& fileKey);
    void requestFigmaFrameImport(const QString& fileKey, const QString& frameId, int dpi = 300, int pageNumber = 1);

    // Auto-polling
    void startPolling(int intervalMs = 2000);
    void stopPolling();
    bool isPolling() const { return m_pollTimer && m_pollTimer->isActive(); }

signals:
    // Response signals
    void statusReceived(const QJsonObject& data);
    void ragLLMContextReceived(const QString& enhancedPrompt, const QJsonObject& contextData);
    void ragImagesForTextReceived(const QJsonArray& images);
    void ragTextsForImageReceived(const QJsonArray& texts);
    void ragSuggestPairsReceived(const QJsonArray& suggestions);
    void figmaFilesReceived(const QJsonArray& files);
    void figmaFramesReceived(const QString& fileKey, const QJsonArray& frames);
    void figmaFrameImportReceived(const QJsonObject& result);
    void pipelineReceived(const QJsonObject& data);
    void assetsReceived(const QJsonObject& data);
    void layoutAuditReceived(const QJsonObject& data);
    void pipelineStartResult(bool success, const QString& message);
    void pipelineStopResult(bool success, const QString& message);
    void workflowJobCreated(const QJsonObject& job);

    // Status signals
    void connectionStatusChanged(bool connected, int latencyMs);
    void errorOccurred(const QString& error, int httpStatusCode = 0);

private slots:
    void onReplyFinished(QNetworkReply* reply);
    void onPollTimerTimeout();

private:
    // HTTP methods
    QNetworkReply* sendGet(const QString& endpoint, const QString& tag);
    QNetworkReply* sendPost(const QString& endpoint, const QByteArray& payload, const QString& tag);
    QNetworkReply* sendMultipart(const QString& endpoint, QHttpMultiPart* multiPart, const QString& tag);

    // Response handlers
    void handleStatusResponse(const QJsonObject& obj);
    void handlePipelineResponse(const QJsonObject& obj);
    void handleAssetsResponse(const QJsonObject& obj);
    void handleLayoutAuditResponse(const QJsonObject& obj);
    void handleErrorResponse(QNetworkReply* reply);

    // Helper methods
    QString buildUrl(const QString& endpoint) const;
    void setConnectionStatus(bool connected, int latencyMs = -1);
    qint64 calculateLatency(QNetworkReply* reply) const;

    QNetworkAccessManager* m_networkManager;
    QTimer* m_pollTimer;
    QHash<QNetworkReply*, QString> m_replyTags;
    
    QString m_baseUrl;
    QString m_apiKey;
    
    bool m_connected;
    int m_latencyMs;
};

