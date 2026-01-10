#include "gamma_api_client.h"

#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QJsonParseError>
#include <QNetworkRequest>
#include <QNetworkReply>
#include <QUrl>
#include <QTimer>
#include <QDateTime>
#include <QElapsedTimer>

GammaApiClient::GammaApiClient(QObject* parent)
    : QObject(parent)
    , m_networkManager(new QNetworkAccessManager(this))
    , m_pollTimer(new QTimer(this))
    , m_baseUrl("http://localhost:8000")
    , m_apiKey()
    , m_connected(false)
    , m_latencyMs(-1)
{
    // Network Manager Signals verbinden
    connect(m_networkManager, &QNetworkAccessManager::finished,
            this, &GammaApiClient::onReplyFinished);

    // Poll Timer konfigurieren
    m_pollTimer->setSingleShot(false);
    connect(m_pollTimer, &QTimer::timeout, this, &GammaApiClient::onPollTimerTimeout);
}

GammaApiClient::~GammaApiClient()
{
    stopPolling();
    // QNetworkAccessManager wird automatisch gelöscht (parent-child)
}

void GammaApiClient::setBaseUrl(const QString& url)
{
    if (m_baseUrl != url)
    {
        m_baseUrl = url;
        // Reset connection status on URL change
        setConnectionStatus(false, -1);
    }
}

void GammaApiClient::setApiKey(const QString& key)
{
    m_apiKey = key;
}

void GammaApiClient::requestStatus()
{
    sendGet("/api/status", "status");
}

void GammaApiClient::requestPipeline(const QString& pipelineId)
{
    QString endpoint = "/api/pipeline";
    if (!pipelineId.isEmpty())
    {
        endpoint += "/" + pipelineId;
    }
    sendGet(endpoint, "pipeline");
}

void GammaApiClient::requestAssets()
{
    sendGet("/api/assets", "assets");
}

void GammaApiClient::requestLayoutAudit()
{
    sendGet("/api/layout/audit", "layout_audit");
}

void GammaApiClient::startPipeline(const QString& pipelineId)
{
    if (pipelineId.isEmpty())
    {
        emit errorOccurred("Pipeline ID is required", 400);
        return;
    }

    QJsonObject payload;
    payload["pipeline_id"] = pipelineId;

    QJsonDocument doc(payload);
    QByteArray data = doc.toJson(QJsonDocument::Compact);

    sendPost(QString("/api/pipeline/%1/start").arg(pipelineId), data, "pipeline_start");
}

void GammaApiClient::stopPipeline(const QString& pipelineId)
{
    if (pipelineId.isEmpty())
    {
        emit errorOccurred("Pipeline ID is required", 400);
        return;
    }

    QJsonObject payload;
    payload["pipeline_id"] = pipelineId;

    QJsonDocument doc(payload);
    QByteArray data = doc.toJson(QJsonDocument::Compact);

    sendPost(QString("/api/pipeline/%1/stop").arg(pipelineId), data, "pipeline_stop");
}

void GammaApiClient::startPolling(int intervalMs)
{
    if (intervalMs < 100)
        intervalMs = 100; // Minimum 100ms

    m_pollTimer->setInterval(intervalMs);
    if (!m_pollTimer->isActive())
    {
        m_pollTimer->start();
        // Sofort ersten Request senden
        requestStatus();
    }
}

void GammaApiClient::stopPolling()
{
    if (m_pollTimer)
        m_pollTimer->stop();
}

QNetworkReply* GammaApiClient::sendGet(const QString& endpoint, const QString& tag)
{
    if (!m_networkManager)
        return nullptr;

    QUrl url = buildUrl(endpoint);
    QNetworkRequest request(url);
    
    // Headers setzen
    request.setHeader(QNetworkRequest::ContentTypeHeader, "application/json");
    
    // Authentifizierung
    if (!m_apiKey.isEmpty())
    {
        // Versuche zuerst X-API-Key, dann Bearer Token
        request.setRawHeader("X-API-Key", m_apiKey.toUtf8());
        request.setRawHeader("Authorization", QByteArray("Bearer ") + m_apiKey.toUtf8());
    }

    QNetworkReply* reply = m_networkManager->get(request);
    if (reply)
    {
        m_replyTags.insert(reply, tag);
    }

    return reply;
}

QNetworkReply* GammaApiClient::sendPost(const QString& endpoint, const QByteArray& payload, const QString& tag)
{
    if (!m_networkManager)
        return nullptr;

    QUrl url = buildUrl(endpoint);
    QNetworkRequest request(url);
    
    // Headers setzen
    request.setHeader(QNetworkRequest::ContentTypeHeader, "application/json");
    
    // Authentifizierung
    if (!m_apiKey.isEmpty())
    {
        request.setRawHeader("X-API-Key", m_apiKey.toUtf8());
        request.setRawHeader("Authorization", QByteArray("Bearer ") + m_apiKey.toUtf8());
    }

    QNetworkReply* reply = m_networkManager->post(request, payload);
    if (reply)
    {
        m_replyTags.insert(reply, tag);
    }

    return reply;
}

void GammaApiClient::onReplyFinished(QNetworkReply* reply)
{
    if (!reply)
        return;

    const QString tag = m_replyTags.take(reply);
    const QByteArray data = reply->readAll();
    const int statusCode = reply->attribute(QNetworkRequest::HttpStatusCodeAttribute).toInt();
    
    // Latenz berechnen (falls möglich)
    int latency = calculateLatency(reply);

    // Error-Handling
    if (reply->error() != QNetworkReply::NoError)
    {
        handleErrorResponse(reply);
        reply->deleteLater();
        return;
    }

    // HTTP-Status-Code prüfen
    if (statusCode < 200 || statusCode >= 300)
    {
        QString errorMsg = QString("HTTP Error %1: %2").arg(statusCode).arg(QString::fromUtf8(data));
        emit errorOccurred(errorMsg, statusCode);
        
        if (statusCode == 401)
        {
            setConnectionStatus(false, -1);
        }
        
        reply->deleteLater();
        return;
    }

    // JSON-Parsing
    QJsonParseError parseError;
    QJsonDocument doc = QJsonDocument::fromJson(data, &parseError);
    
    if (parseError.error != QJsonParseError::NoError)
    {
        emit errorOccurred(QString("JSON Parse Error: %1").arg(parseError.errorString()), 0);
        reply->deleteLater();
        return;
    }

    if (!doc.isObject() && !doc.isArray())
    {
        emit errorOccurred("Invalid JSON response format", 0);
        reply->deleteLater();
        return;
    }

    // Response handler based on tag
    if (tag == "status")
    {
        if (doc.isObject())
            handleStatusResponse(doc.object());
        
        // Bei erfolgreichem Status-Request Verbindung als connected markieren
        setConnectionStatus(true, latency);
    }
    else if (tag == "pipeline")
    {
        if (doc.isObject())
            handlePipelineResponse(doc.object());
        else if (doc.isArray())
        {
            // Array von Pipelines - in Objekt konvertieren
            QJsonObject obj;
            obj["pipelines"] = doc.array();
            handlePipelineResponse(obj);
        }
    }
    else if (tag == "assets")
    {
        if (doc.isObject())
            handleAssetsResponse(doc.object());
    }
    else if (tag == "layout_audit")
    {
        if (doc.isObject())
            handleLayoutAuditResponse(doc.object());
    }
    else if (tag == "pipeline_start")
    {
        bool success = doc.isObject() && doc.object().value("success").toBool(false);
        QString message = doc.isObject() ? doc.object().value("message").toString("Pipeline started") : "Unknown";
        emit pipelineStartResult(success, message);
    }
    else if (tag == "pipeline_stop")
    {
        bool success = doc.isObject() && doc.object().value("success").toBool(false);
        QString message = doc.isObject() ? doc.object().value("message").toString("Pipeline stopped") : "Unknown";
        emit pipelineStopResult(success, message);
    }

    reply->deleteLater();
}

void GammaApiClient::onPollTimerTimeout()
{
    // Polling-Intervall: Status aktualisieren
    requestStatus();
}

void GammaApiClient::handleStatusResponse(const QJsonObject& obj)
{
    // Process status response
    // Format: { "status": "connected", "latency_ms": 42, "version": "1.0.0", "timestamp": "..." }
    
    QString statusStr = obj.value("status").toString("unknown");
    int latency = obj.value("latency_ms").toInt(-1);
    
    bool connected = (statusStr == "connected" || statusStr == "ok");
    
    setConnectionStatus(connected, latency);
    
    // Signal emitieren
    emit statusReceived(obj);
}

void GammaApiClient::handlePipelineResponse(const QJsonObject& obj)
{
    emit pipelineReceived(obj);
}

void GammaApiClient::handleAssetsResponse(const QJsonObject& obj)
{
    emit assetsReceived(obj);
}

void GammaApiClient::handleLayoutAuditResponse(const QJsonObject& obj)
{
    emit layoutAuditReceived(obj);
}

void GammaApiClient::handleErrorResponse(QNetworkReply* reply)
{
    QString errorString = reply->errorString();
    int statusCode = reply->attribute(QNetworkRequest::HttpStatusCodeAttribute).toInt();
    
    // Network-Fehler (kein HTTP-Status-Code)
    if (statusCode == 0)
    {
        // Connection-Errors
        if (reply->error() == QNetworkReply::ConnectionRefusedError ||
            reply->error() == QNetworkReply::HostNotFoundError ||
            reply->error() == QNetworkReply::TimeoutError)
        {
            setConnectionStatus(false, -1);
        }
        
        emit errorOccurred(errorString, 0);
    }
    else
    {
        // HTTP-Errors
        QByteArray data = reply->readAll();
        QString errorMsg = QString("HTTP %1: %2").arg(statusCode).arg(QString::fromUtf8(data));
        
        if (statusCode == 401)
        {
            setConnectionStatus(false, -1);
        }
        
        emit errorOccurred(errorMsg, statusCode);
    }
}

QString GammaApiClient::buildUrl(const QString& endpoint) const
{
    QString base = m_baseUrl;
    if (!base.endsWith('/') && !endpoint.startsWith('/'))
        base += '/';
    else if (base.endsWith('/') && endpoint.startsWith('/'))
        base.chop(1);
    
    return base + endpoint;
}

void GammaApiClient::setConnectionStatus(bool connected, int latencyMs)
{
    if (m_connected != connected || m_latencyMs != latencyMs)
    {
        m_connected = connected;
        m_latencyMs = latencyMs;
        emit connectionStatusChanged(connected, latencyMs);
    }
}

qint64 GammaApiClient::calculateLatency(QNetworkReply* reply) const
{
    // Try to extract latency from response if available
    // Alternatively, we could use QElapsedTimer, but that requires request tracking
    // For now, we use the latency from the response if available
    return -1; // Will be overridden by response
}

