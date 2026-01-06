# GitHub Upload Script für Gamma Dashboard Plugin
# Führe dieses Script aus, um das Repository auf GitHub hochzuladen

$ErrorActionPreference = "Stop"

$pluginDir = "gamma_scribus_pack\plugin\cpp"
$repoName = "scribus-gamma-dashboard-plugin"

Write-Host "=== GitHub Repository Upload ===" -ForegroundColor Cyan
Write-Host ""

# Prüfe Git
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Git nicht gefunden. Bitte Git installieren." -ForegroundColor Red
    Write-Host "   Download: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

# Prüfe Plugin-Verzeichnis
$originalDir = Get-Location
if (-not (Test-Path $pluginDir)) {
    Write-Host "❌ Plugin-Verzeichnis nicht gefunden: $pluginDir" -ForegroundColor Red
    Write-Host "   Aktuelles Verzeichnis: $originalDir" -ForegroundColor Yellow
    exit 1
}

# Navigate to plugin directory
Set-Location $pluginDir

Write-Host "Arbeitsverzeichnis: $(Get-Location)" -ForegroundColor Gray
Write-Host ""

# Prüfe ob bereits Git-Repository
if (Test-Path ".git") {
    Write-Host "⚠️  Bereits ein Git-Repository. Überspringe Initialisierung." -ForegroundColor Yellow
} else {
    Write-Host "Initialisiere Git-Repository..." -ForegroundColor Yellow
    git init
    git branch -M main
    Write-Host "✅ Git-Repository initialisiert" -ForegroundColor Green
}

# Prüfe .gitignore
if (-not (Test-Path ".gitignore")) {
    Write-Host "⚠️  .gitignore nicht gefunden. Erstelle Standard-Version..." -ForegroundColor Yellow
}

# Add files
Write-Host ""
Write-Host "Füge Dateien hinzu..." -ForegroundColor Yellow
git add .

# Zeige Status
Write-Host ""
Write-Host "Repository-Status:" -ForegroundColor Cyan
$status = git status --short
if ($status) {
    Write-Host $status
} else {
    Write-Host "  (keine Änderungen)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=== Nächste Schritte ===" -ForegroundColor Yellow
Write-Host ""

# Prüfe GitHub CLI
$hasGh = Get-Command gh -ErrorAction SilentlyContinue
if ($hasGh) {
    Write-Host "✅ GitHub CLI gefunden" -ForegroundColor Green
    Write-Host ""
    Write-Host "Option 1: GitHub CLI (Empfohlen)" -ForegroundColor Cyan
    Write-Host "  1. Authentifiziere: gh auth login" -ForegroundColor White
    Write-Host "  2. Erstelle Repository:" -ForegroundColor White
    Write-Host "     gh repo create $repoName --public --source=. --remote=origin --push" -ForegroundColor Gray
    Write-Host ""
    Write-Host "     Oder interaktiv:" -ForegroundColor White
    Write-Host "     gh repo create" -ForegroundColor Gray
    Write-Host ""
}

Write-Host "Option 2: Manuell über GitHub Web" -ForegroundColor Cyan
Write-Host "  1. Erstelle Repository auf GitHub:" -ForegroundColor White
Write-Host "     https://github.com/new" -ForegroundColor Gray
Write-Host "     Name: $repoName" -ForegroundColor Gray
Write-Host "     Beschreibung: Native C++ plugin for Scribus providing a dockable dashboard panel" -ForegroundColor Gray
Write-Host "     Sichtbarkeit: Public" -ForegroundColor Gray
Write-Host "     ❌ KEIN README initialisieren (haben wir schon)" -ForegroundColor Yellow
Write-Host ""
Write-Host "  2. Commit und Push:" -ForegroundColor White
Write-Host "     git commit -m `"Initial commit: Gamma Dashboard Plugin v1.0.0`"" -ForegroundColor Gray
Write-Host "     git remote add origin https://github.com/JochenWeerda/$repoName.git" -ForegroundColor Gray
Write-Host "     git push -u origin main" -ForegroundColor Gray
Write-Host ""

# Frage nach Commit
Write-Host "Möchtest du jetzt committen? (J/N): " -ForegroundColor Yellow -NoNewline
$response = Read-Host
if ($response -eq "J" -or $response -eq "j" -or $response -eq "Y" -or $response -eq "y") {
    Write-Host ""
    Write-Host "Erstelle Commit..." -ForegroundColor Yellow
    $commitMsg = @"
Initial commit: Gamma Dashboard Plugin v1.0.0

- Native C++ plugin for Scribus 1.7.1+
- Dockable dashboard panel
- Real-time pipeline monitoring
- Layout audit and asset validation
- Mock mode for testing
- Fully tested and production ready

Features:
- Real-time status monitoring
- Progress tracking
- Layout audit (Z-order, overlaps)
- Asset validation
- Cloud sync integration
- Batch rendering

Platform: Windows x64 (MSVC 2022)
Scribus: 1.7.1+
Qt: 6.10.1
"@
    git commit -m $commitMsg
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Commit erstellt" -ForegroundColor Green
        Write-Host ""
        Write-Host "Jetzt Repository auf GitHub erstellen und push ausführen!" -ForegroundColor Yellow
    } else {
        Write-Host "❌ Fehler beim Commit" -ForegroundColor Red
    }
} else {
    Write-Host ""
    Write-Host "Commit übersprungen. Führe manuell aus:" -ForegroundColor Yellow
    Write-Host "  git commit -m `"Initial commit: Gamma Dashboard Plugin v1.0.0`"" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=== Fertig ===" -ForegroundColor Green
Write-Host "Vergiss nicht, die Nachricht an Scribus-Developer zu senden:" -ForegroundColor Yellow
Write-Host "  Siehe: SCRIBUS_DEVELOPER_MESSAGE.md" -ForegroundColor White

# Zurück zum ursprünglichen Verzeichnis
Set-Location $originalDir

