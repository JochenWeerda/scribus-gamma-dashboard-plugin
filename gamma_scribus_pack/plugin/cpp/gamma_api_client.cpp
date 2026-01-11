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
#include <QHttpMultiPart>
#include <QFile>
#include <QFileInfo>

GammaApiClient::GammaApiClient(QObject* parent)
    : QObject(parent)
    , m_networkManager(new QNetworkAccessManager(this))
    , m_pollTimer(new QTimer(this))
    , m_baseUrl("http://localhost:8003")
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

void GammaApiClient::requestRAGLLMContext(const QString& prompt, int topKLayouts, int topKTexts, int topKImages)
{
    QJsonObject payload;
    payload["prompt"] = prompt;
    payload["top_k_layouts"] = topKLayouts;
    payload["top_k_texts"] = topKTexts;
    payload["top_k_images"] = topKImages;

    QJsonDocument doc(payload);
    QByteArray data = doc.toJson(QJsonDocument::Compact);

    sendPost("/api/rag/llm-context", data, "rag_llm_context");
}

void GammaApiClient::requestFindImagesForText(const QString& text, int topK)
{
    QJsonObject payload;
    payload["text"] = text;
    payload["top_k"] = topK;

    QJsonDocument doc(payload);
    QByteArray data = doc.toJson(QJsonDocument::Compact);

    sendPost("/api/rag/images/for-text", data, "rag_images_for_text");
}

void GammaApiClient::requestFindTextsForImage(const QString& imagePath, int topK)
{
    QJsonObject payload;
    payload["image_path"] = imagePath;
    payload["top_k"] = topK;

    QJsonDocument doc(payload);
    QByteArray data = doc.toJson(QJsonDocument::Compact);

    sendPost("/api/rag/texts/for-image", data, "rag_texts_for_image");
}

void GammaApiClient::requestSuggestTextImagePairs(const QJsonObject& layoutJson)
{
    QJsonObject payload;
    payload["layout_json"] = layoutJson;

    QJsonDocument doc(payload);
    QByteArray data = doc.toJson(QJsonDocument::Compact);

    sendPost("/api/rag/suggest-pairs", data, "rag_suggest_pairs");
}

void GammaApiClient::requestFigmaFiles()
{
    sendGet("/api/figma/files", "figma_files");
}

void GammaApiClient::requestFigmaFrames(const QString& fileKey)
{
    sendGet(QString("/api/figma/files/%1/frames").arg(fileKey), QString("figma_frames:%1").arg(fileKey));
}

void GammaApiClient::requestFigmaFrameImport(const QString& fileKey, const QString& frameId, int dpi, int pageNumber)
{
    QJsonObject payload;
    payload["file_key"] = fileKey;
    payload["frame_id"] = frameId;
    payload["dpi"] = dpi;
    payload["page_number"] = pageNumber;

    QJsonDocument doc(payload);
    QByteArray data = doc.toJson(QJsonDocument::Compact);

    sendPost("/api/figma/frames/import", data, "figma_frame_import");
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

void GammaApiClient::requestWorkflowRun(const QString& bundleZipPath, const QJsonObject& options)
{
    QFileInfo fi(bundleZipPath);
    if (!fi.exists() || !fi.isFile())
    {
        emit errorOccurred(QString("Workflow bundle not found: %1").arg(bundleZipPath), 400);
        return;
    }

    QHttpMultiPart* multi = new QHttpMultiPart(QHttpMultiPart::FormDataType);

    // options_json form field
    QJsonObject opts = options;
    if (opts.isEmpty())
    {
        // Recommended defaults
        opts["generate_variants"] = true;
        opts["gamma_sync"] = true;
        opts["gamma_crop_kinds"] = QJsonArray{ "infobox" };
        opts["gamma_attach_to_variants"] = false;
        opts["quality_check"] = true;
        opts["quality_on_variants"] = true;
        opts["quality_checks"] = QJsonArray{ "preflight", "amazon" };
        opts["publish_artifacts"] = true;
        opts["force"] = false;
    }
    QHttpPart optionsPart;
    optionsPart.setHeader(QNetworkRequest::ContentDispositionHeader, QVariant("form-data; name=\"options_json\""));
    optionsPart.setBody(QJsonDocument(opts).toJson(QJsonDocument::Compact));
    multi->append(optionsPart);

    // bundle file part
    QFile* file = new QFile(bundleZipPath, multi);
    if (!file->open(QIODevice::ReadOnly))
    {
        emit errorOccurred(QString("Cannot open workflow bundle: %1").arg(bundleZipPath), 400);
        multi->deleteLater();
        return;
    }

    QHttpPart filePart;
    filePart.setHeader(QNetworkRequest::ContentTypeHeader, QVariant("application/zip"));
    filePart.setHeader(QNetworkRequest::ContentDispositionHeader, QVariant(QString("form-data; name=\"bundle\"; filename=\"%1\"").arg(fi.fileName())));
    filePart.setBodyDevice(file);
    file->setParent(multi);
    multi->append(filePart);

    sendMultipart("/v1/workflow/run", multi, "workflow_run");
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
    else if (tag == "rag_llm_context")
    {
        if (doc.isObject())
        {
            QJsonObject obj = doc.object();
            QString context = obj.value("context").toString();
            QJsonObject contextData = obj; // Enthält context, sources, stats
            emit ragLLMContextReceived(context, contextData);
        }
    }
    else if (tag == "rag_images_for_text")
    {
        if (doc.isObject())
        {
            QJsonArray images = doc.object().value("images").toArray();
            emit ragImagesForTextReceived(images);
        }
    }
    else if (tag == "rag_texts_for_image")
    {
        if (doc.isObject())
        {
            QJsonArray texts = doc.object().value("texts").toArray();
            emit ragTextsForImageReceived(texts);
        }
    }
    else if (tag == "rag_suggest_pairs")
    {
        if (doc.isObject())
        {
            QJsonArray suggestions = doc.object().value("suggestions").toArray();
            emit ragSuggestPairsReceived(suggestions);
        }
    }
    else if (tag == "figma_files")
    {
        if (doc.isObject())
        {
            QJsonArray files = doc.object().value("files").toArray();
            emit figmaFilesReceived(files);
        }
    }
    else if (tag == "figma_frames")
    {
        if (doc.isObject())
        {
            QString fileKey = m_replyTags.value(reply, "").split(":").last(); // Extract fileKey from tag
            QJsonArray frames = doc.object().value("frames").toArray();
            emit figmaFramesReceived(fileKey, frames);
        }
    }
    else if (tag == "figma_frame_import")
    {
        if (doc.isObject())
        {
            emit figmaFrameImportReceived(doc.object());
        }
    }
    else if (tag == "workflow_run")
    {
        if (doc.isObject())
        {
            emit workflowJobCreated(doc.object());
        }
    }

    reply->deleteLater();
}

QNetworkReply* GammaApiClient::sendMultipart(const QString& endpoint, QHttpMultiPart* multiPart, const QString& tag)
{
    QUrl url(buildUrl(endpoint));
    QNetworkRequest request(url);
    request.setRawHeader("Accept", "application/json");

    if (!m_apiKey.isEmpty())
        request.setRawHeader("X-API-Key", m_apiKey.toUtf8());

    QNetworkReply* reply = m_networkManager->post(request, multiPart);
    multiPart->setParent(reply);
    m_replyTags.insert(reply, tag);
    return reply;
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

