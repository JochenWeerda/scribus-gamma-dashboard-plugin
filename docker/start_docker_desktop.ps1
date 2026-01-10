# Startet Docker Desktop (PowerShell)

Write-Host "=== Docker Desktop starten ===" -ForegroundColor Cyan
Write-Host ""

# Prüfe ob Docker Desktop bereits läuft
$dockerProcess = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
if ($dockerProcess) {
    Write-Host "✅ Docker Desktop läuft bereits (PID: $($dockerProcess.Id))" -ForegroundColor Green
    Write-Host ""
    
    # Prüfe ob Docker daemon verfügbar ist
    try {
        docker info | Out-Null
        Write-Host "✅ Docker Daemon ist bereit" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ Docker Desktop läuft, aber Daemon ist noch nicht bereit. Warte..." -ForegroundColor Yellow
        $maxWait = 60
        $waited = 0
        while ($waited -lt $maxWait) {
            Start-Sleep -Seconds 2
            $waited += 2
            try {
                docker info | Out-Null
                Write-Host "✅ Docker Daemon ist jetzt bereit (nach $waited Sekunden)" -ForegroundColor Green
                break
            } catch {
                Write-Host "   Warte auf Docker Daemon... ($waited/$maxWait s)" -ForegroundColor Gray
            }
        }
        if ($waited -ge $maxWait) {
            Write-Host "❌ Docker Daemon ist nach $maxWait Sekunden nicht bereit" -ForegroundColor Red
            exit 1
        }
    }
} else {
    Write-Host "🚀 Starte Docker Desktop..." -ForegroundColor Yellow
    
    # Versuche Docker Desktop zu starten
    $dockerDesktopPath = "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe"
    if (Test-Path $dockerDesktopPath) {
        Start-Process -FilePath $dockerDesktopPath
        Write-Host "✅ Docker Desktop gestartet" -ForegroundColor Green
        Write-Host ""
        Write-Host "⏳ Warte auf Docker Daemon..." -ForegroundColor Yellow
        
        # Warte auf Docker Daemon
        $maxWait = 120
        $waited = 0
        while ($waited -lt $maxWait) {
            Start-Sleep -Seconds 3
            $waited += 3
            try {
                docker info | Out-Null
                Write-Host "✅ Docker Daemon ist bereit (nach $waited Sekunden)" -ForegroundColor Green
                break
            } catch {
                Write-Host "   Warte auf Docker Daemon... ($waited/$maxWait s)" -ForegroundColor Gray
            }
        }
        if ($waited -ge $maxWait) {
            Write-Host "❌ Docker Daemon ist nach $maxWait Sekunden nicht bereit" -ForegroundColor Red
            Write-Host "   Bitte starte Docker Desktop manuell und warte bis es bereit ist." -ForegroundColor Yellow
            exit 1
        }
    } else {
        Write-Host "❌ Docker Desktop nicht gefunden unter: $dockerDesktopPath" -ForegroundColor Red
        Write-Host "   Bitte installiere Docker Desktop oder starte es manuell." -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""
Write-Host "=== ✅ Docker Desktop ist bereit ===" -ForegroundColor Green
Write-Host ""

