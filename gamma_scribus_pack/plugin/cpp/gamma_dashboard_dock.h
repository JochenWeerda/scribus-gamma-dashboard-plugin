#pragma once

#include <QDockWidget>

class QLabel;
class QPushButton;
class QProgressBar;
class QLineEdit;
class QTextEdit;
class QComboBox;

/**
 * @brief Dock Widget für Gamma Dashboard
 * 
 * Native C++ Qt-Widget für Integration in Scribus-UI.
 * Inspiriert von MCP Dashboard Plugin Pattern.
 */
class GammaDashboardDock : public QDockWidget
{
    Q_OBJECT

public:
    explicit GammaDashboardDock(QWidget* parent = nullptr);

    void setStatus(bool connected, int latencyMs);
    void setPipelineProgress(int value);
    void appendLog(const QString& line);

signals:
    void pipelineStartRequested();
    void pipelineStopRequested();
    void settingsRequested();

private slots:
    void onPipelineStartClicked();
    void onPipelineStopClicked();
    void onSettingsClicked();

private:
    void setupUI();
    
    QLabel* m_statusDot;
    QLabel* m_statusText;
    QPushButton* m_settingsButton;
    QPushButton* m_pipelineStartButton;
    QPushButton* m_pipelineStopButton;
    QProgressBar* m_pipelineProgress;
    QComboBox* m_pipelineSelect;
    QTextEdit* m_logView;
    QLabel* m_configPathLabel;
};
