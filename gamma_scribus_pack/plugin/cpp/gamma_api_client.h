#pragma once

#include <QObject>
#include <QString>
#include <QJsonObject>
#include <QNetworkAccessManager>
#include <QNetworkReply>
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

    // Auto-polling
    void startPolling(int intervalMs = 2000);
    void stopPolling();
    bool isPolling() const { return m_pollTimer && m_pollTimer->isActive(); }

signals:
    // Response signals
    void statusReceived(const QJsonObject& data);
    void pipelineReceived(const QJsonObject& data);
    void assetsReceived(const QJsonObject& data);
    void layoutAuditReceived(const QJsonObject& data);
    void pipelineStartResult(bool success, const QString& message);
    void pipelineStopResult(bool success, const QString& message);

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

