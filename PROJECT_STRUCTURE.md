# Projektstruktur (Kurzüberblick)

Kanonische Struktur für GitHub (Code + kuratierte Docs; keine Assets/Secrets).

```
scribus-gamma-dashboard-plugin/
├── README.md
├── LICENSE
├── INSTALLATION.md
├── PROJECT_STRUCTURE.md
├── requirements.txt
├── requirements-dev.txt
├── docker/                       # docker compose + Dockerfiles
├── apps/                         # API-Gateway + Worker
├── packages/                     # shared libs (workflow, rag, figma, …)
├── gamma_scribus_pack/
│   └── plugin/cpp/               # C++/Qt Plugin (inkl. Cookbook)
├── docs/
│   ├── workflow/                 # Magazin-Workflow Dokumente (kanonisch)
│   └── ...                       # weitere kuratierte Dossiers
├── strategy/                     # Strategie-Dokumente (RAG/Figma/Layout)
├── tools/                        # Dev-Tools (Bundle-Builder etc.)
└── tests/                        # Tests (falls vorhanden)
```

Hinweis: Lokale Daten/Assets sind bewusst per `.gitignore` ausgeschlossen (`.env`, `.cursor/`, `media_pool/`, `assets/`, `*.pptx`, `*.png`, …).

