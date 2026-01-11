#pragma once

#include <QDateTime>
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QStandardPaths>
#include <QString>
#include <QTextStream>
#include <QtGlobal>

namespace gamma_dashboard::debug_log {

inline QString logPath()
{
    const QString v = qEnvironmentVariable("GAMMA_DASHBOARD_DEBUG_LOG");
    if (v.isEmpty())
        return QString();

    const QString vl = v.toLower();
    if (vl == "1" || vl == "true" || vl == "yes" || vl == "on")
    {
        const QString dir = QStandardPaths::writableLocation(QStandardPaths::TempLocation);
        return QDir(dir).filePath("gamma_dashboard_debug.log");
    }

    return v;
}

inline void appendLine(const QString& line)
{
    const QString path = logPath();
    if (path.isEmpty())
        return;

    const QFileInfo fi(path);
    QDir().mkpath(fi.absolutePath());

    QFile f(path);
    if (!f.open(QIODevice::Append | QIODevice::Text))
        return;

    QTextStream out(&f);
    out << line;
}

inline void appendJson(const QString& location, const QString& message, const QString& dataJson)
{
    const qint64 ts = QDateTime::currentMSecsSinceEpoch();
    appendLine(QString("{\"id\":\"log_%1\",\"timestamp\":%2,\"location\":\"%3\",\"message\":\"%4\",\"data\":%5}\n")
                   .arg(ts)
                   .arg(ts)
                   .arg(location)
                   .arg(message)
                   .arg(dataJson.isEmpty() ? "{}" : dataJson));
}

} // namespace gamma_dashboard::debug_log

