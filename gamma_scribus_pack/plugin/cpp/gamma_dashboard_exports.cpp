#include "gamma_dashboard_plugin.h"
#include "pluginapi.h"
#include "scplugin.h"
#include "gamma_debug_log.h"
#include <QFile>
#include <QTextStream>
#include <QDateTime>

// Plugin-Export-Funktionen (von Scribus erwartet)
extern "C" PLUGIN_API int gamma_dashboard_getPluginAPIVersion()
{
    // #region agent log
    QFile logFile(gamma_dashboard::debug_log::logPath());
    if (logFile.open(QIODevice::Append | QIODevice::Text)) {
        QTextStream out(&logFile);
        out << QString("{\"id\":\"log_%1\",\"timestamp\":%2,\"location\":\"gamma_dashboard_exports.cpp:8\",\"message\":\"getPluginAPIVersion called\",\"data\":{\"version\":%3},\"sessionId\":\"debug-session\",\"runId\":\"run1\",\"hypothesisId\":\"F\"}\n")
            .arg(QDateTime::currentMSecsSinceEpoch())
            .arg(QDateTime::currentMSecsSinceEpoch())
            .arg(PLUGIN_API_VERSION);
        logFile.close();
    }
    // #endregion

    return PLUGIN_API_VERSION;
}

extern "C" PLUGIN_API ScPlugin* gamma_dashboard_getPlugin()
{
    // #region agent log
    QFile logFile(gamma_dashboard::debug_log::logPath());
    if (logFile.open(QIODevice::Append | QIODevice::Text)) {
        QTextStream out(&logFile);
        out << QString("{\"id\":\"log_%1\",\"timestamp\":%2,\"location\":\"gamma_dashboard_exports.cpp:23\",\"message\":\"getPlugin called - creating instance\",\"data\":{},\"sessionId\":\"debug-session\",\"runId\":\"run1\",\"hypothesisId\":\"G\"}\n")
            .arg(QDateTime::currentMSecsSinceEpoch())
            .arg(QDateTime::currentMSecsSinceEpoch());
        logFile.close();
    }
    // #endregion

    try {
        GammaDashboardPlugin* plugin = new GammaDashboardPlugin();
        // #region agent log
        if (logFile.open(QIODevice::Append | QIODevice::Text)) {
            QTextStream out(&logFile);
            out << QString("{\"id\":\"log_%1\",\"timestamp\":%2,\"location\":\"gamma_dashboard_exports.cpp:35\",\"message\":\"Plugin instance created\",\"data\":{\"plugin\":\"%3\"},\"sessionId\":\"debug-session\",\"runId\":\"run1\",\"hypothesisId\":\"H\"}\n")
                .arg(QDateTime::currentMSecsSinceEpoch())
                .arg(QDateTime::currentMSecsSinceEpoch())
                .arg(plugin ? "not null" : "null");
            logFile.close();
        }
        // #endregion
        return plugin;
    } catch (...) {
        // #region agent log
        if (logFile.open(QIODevice::Append | QIODevice::Text)) {
            QTextStream out(&logFile);
            out << QString("{\"id\":\"log_%1\",\"timestamp\":%2,\"location\":\"gamma_dashboard_exports.cpp:42\",\"message\":\"Exception during plugin creation\",\"data\":{},\"sessionId\":\"debug-session\",\"runId\":\"run1\",\"hypothesisId\":\"I\"}\n")
                .arg(QDateTime::currentMSecsSinceEpoch())
                .arg(QDateTime::currentMSecsSinceEpoch());
            logFile.close();
        }
        // #endregion
        // Catch any exceptions during instantiation
        return nullptr;
    }
}

extern "C" PLUGIN_API void gamma_dashboard_freePlugin(ScPlugin* plugin)
{
    delete plugin;
}

