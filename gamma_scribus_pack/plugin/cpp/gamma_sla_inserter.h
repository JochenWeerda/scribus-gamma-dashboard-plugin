#pragma once

#include <QObject>
#include <QString>
#include <QByteArray>

class ScribusDoc;

/**
 * GammaSLAInserter
 * 
 * Hilfsklasse zum Einfügen von SLA XML in Scribus-Dokumente.
 */
class GammaSLAInserter : public QObject
{
    Q_OBJECT

public:
    explicit GammaSLAInserter(QObject* parent = nullptr);

    /**
     * Fügt SLA XML als neue Seite in Scribus-Dokument ein.
     * 
     * @param doc Scribus-Dokument
     * @param slaXml SLA XML als Bytes
     * @param pageNumber Seitenzahl (optional, -1 = am Ende einfügen)
     * @return true bei Erfolg
     */
    bool insertSLAAsPage(ScribusDoc* doc, const QByteArray& slaXml, int pageNumber = -1);

    /**
     * Lädt SLA XML in temporäre Datei und öffnet sie.
     * 
     * @param slaXml SLA XML als Bytes
     * @return true bei Erfolg
     */
    bool loadSLATempFile(const QByteArray& slaXml);

signals:
    void slaInserted(bool success, const QString& message);
    void errorOccurred(const QString& error);

private:
    QString createTempSLAPath() const;
};

