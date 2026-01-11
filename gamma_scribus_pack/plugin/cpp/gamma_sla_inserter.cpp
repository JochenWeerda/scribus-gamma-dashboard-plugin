#include "gamma_sla_inserter.h"

// Scribus includes (forward declarations in header)
// #include "scribus.h"
// #include "scribusdoc.h"
// #include "scpage.h"

#include <QFile>
#include <QDir>
#include <QTemporaryFile>
#include <QDateTime>
#include <QDebug>
#include <QIODevice>

GammaSLAInserter::GammaSLAInserter(QObject* parent)
    : QObject(parent)
{
}

bool GammaSLAInserter::insertSLAAsPage(ScribusDoc* doc, const QByteArray& slaXml, int pageNumber)
{
    Q_UNUSED(doc);
    Q_UNUSED(pageNumber);
    
    if (!doc)
    {
        emit errorOccurred("Scribus document is null");
        return false;
    }

    if (slaXml.isEmpty())
    {
        emit errorOccurred("SLA XML is empty");
        return false;
    }

    // Erstelle temporäre SLA-Datei
    QString tempPath = createTempSLAPath();
    QFile tempFile(tempPath);
    
    if (!tempFile.open(QIODevice::WriteOnly))
    {
        emit errorOccurred(QString("Could not create temp file: %1").arg(tempPath));
        return false;
    }

    tempFile.write(slaXml);
    tempFile.close();

    // TODO: Scribus API zum Einfügen von Seiten
    // Optionen:
    // 1. ScribusDoc::loadPage() - Falls verfügbar
    // 2. ScribusMainWindow::loadDoc() - Neues Dokument öffnen
    // 3. ScribusDoc::importPage() - Seite importieren
    // 
    // Für jetzt: Temporäre Datei erstellt, manuelles Öffnen erforderlich
    // Später: Direkte API-Integration
    
    emit slaInserted(true, QString("SLA saved to: %1 (manual import required)").arg(tempPath));
    return true;
}

bool GammaSLAInserter::loadSLATempFile(const QByteArray& slaXml)
{
    if (slaXml.isEmpty())
    {
        emit errorOccurred("SLA XML is empty");
        return false;
    }

    try
    {
        QString tempPath = createTempSLAPath();
        QFile tempFile(tempPath);
        
        if (!tempFile.open(QIODevice::WriteOnly))
        {
            emit errorOccurred(QString("Could not create temp file: %1").arg(tempPath));
            return false;
        }

        tempFile.write(slaXml);
        tempFile.close();

        // TODO: Scribus API zum Öffnen der Datei
        // Optionen:
        // 1. ScCore->primaryMainWindow()->loadDoc(tempPath)
        // 2. QDesktopServices::openUrl(QUrl::fromLocalFile(tempPath))
        // 
        // Für jetzt: Datei erstellt, manuelles Öffnen erforderlich
        
        emit slaInserted(true, QString("SLA saved to: %1 (manual import required)").arg(tempPath));
        return true;
    }
    catch (...)
    {
        emit errorOccurred("Unknown error occurred");
        return false;
    }
}

QString GammaSLAInserter::createTempSLAPath() const
{
    QTemporaryFile tempFile(QDir::temp().absoluteFilePath("gamma_import_XXXXXX.sla"));
    tempFile.setAutoRemove(false);
    
    if (tempFile.open())
    {
        QString path = tempFile.fileName();
        tempFile.close();
        return path;
    }
    
    // Fallback
    return QDir::temp().absoluteFilePath(
        QString("gamma_import_%1.sla").arg(QDateTime::currentMSecsSinceEpoch())
    );
}

