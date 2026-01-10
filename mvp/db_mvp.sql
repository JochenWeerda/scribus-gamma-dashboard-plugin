-- MVP Database Schema für Layout-Compiler Pipeline
-- PostgreSQL Schema für Jobs, Artefakte, Logs, Pages und Assets

-- ============================================================
-- 1) JOBS - Layout-Kompilierungs-Jobs
-- ============================================================

CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
        -- Status: pending, running, completed, failed, cancelled
    job_type VARCHAR(50) NOT NULL DEFAULT 'compile',
        -- Job-Typ: compile, export_png, export_pdf, batch_export
    priority INTEGER DEFAULT 0,
        -- Höhere Zahl = höhere Priorität
    input_artifact_id UUID,
        -- FK zu artifacts (JSON-Layout-Datei)
    output_artifact_id UUID,
        -- FK zu artifacts (kompilierte SLA-Datei)
    error_message TEXT,
    error_traceback TEXT,
    metadata JSONB,
        -- Zusätzliche Metadaten (z.B. Kompilierungs-Optionen)
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    worker_id VARCHAR(255),
        -- ID des Workers, der den Job bearbeitet
    CONSTRAINT jobs_status_check CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled'))
);

CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX idx_jobs_priority_status ON jobs(priority DESC, status);

-- ============================================================
-- 2) ARTIFACTS - Speicherung von Dateien (MinIO/S3 URIs)
-- ============================================================

CREATE TABLE IF NOT EXISTS artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    artifact_type VARCHAR(50) NOT NULL,
        -- Typ: layout_json, sla, png, pdf, asset_image, etc.
    storage_type VARCHAR(20) NOT NULL DEFAULT 's3',
        -- Storage: s3, minio, local, inline
    storage_uri TEXT NOT NULL,
        -- URI/Pfad zum Artefakt (z.B. s3://bucket/path/file.sla)
    storage_key TEXT,
        -- Optional: Storage-Schlüssel (für S3/MinIO)
    file_name TEXT NOT NULL,
    file_size BIGINT,
        -- Dateigröße in Bytes
    mime_type VARCHAR(100),
        -- MIME-Typ (z.B. application/json, image/png, application/pdf)
    checksum_md5 VARCHAR(32),
        -- MD5-Checksumme für Integritätsprüfung
    metadata JSONB,
        -- Zusätzliche Metadaten (z.B. DPI, Dimensionen, etc.)
    expires_at TIMESTAMP WITH TIME ZONE,
        -- Optional: Ablaufzeitpunkt (für temporäre Artefakte)
    CONSTRAINT artifacts_storage_type_check CHECK (storage_type IN ('s3', 'minio', 'local', 'inline'))
);

CREATE INDEX idx_artifacts_type ON artifacts(artifact_type);
CREATE INDEX idx_artifacts_created_at ON artifacts(created_at DESC);
CREATE INDEX idx_artifacts_storage_uri ON artifacts(storage_uri);

-- Foreign Keys für Jobs
ALTER TABLE jobs
    ADD CONSTRAINT fk_jobs_input_artifact FOREIGN KEY (input_artifact_id) REFERENCES artifacts(id) ON DELETE SET NULL,
    ADD CONSTRAINT fk_jobs_output_artifact FOREIGN KEY (output_artifact_id) REFERENCES artifacts(id) ON DELETE SET NULL;

-- ============================================================
-- 3) JOB_LOGS - Logging für Jobs
-- ============================================================

CREATE TABLE IF NOT EXISTS job_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    log_level VARCHAR(10) NOT NULL,
        -- Level: DEBUG, INFO, WARN, ERROR, CRITICAL
    message TEXT NOT NULL,
    context JSONB,
        -- Zusätzlicher Kontext (z.B. Stack-Trace, Objekt-ID, etc.)
    CONSTRAINT job_logs_level_check CHECK (log_level IN ('DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'))
);

CREATE INDEX idx_job_logs_job_id ON job_logs(job_id);
CREATE INDEX idx_job_logs_created_at ON job_logs(created_at DESC);
CREATE INDEX idx_job_logs_level ON job_logs(log_level);

ALTER TABLE job_logs
    ADD CONSTRAINT fk_job_logs_job FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE;

-- ============================================================
-- 4) PAGES - Seiten-Metadaten (aus Layout-JSON extrahiert)
-- ============================================================

CREATE TABLE IF NOT EXISTS pages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL,
    page_number INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    master_page VARCHAR(100),
        -- Optional: Name der Master Page
    object_count INTEGER DEFAULT 0,
        -- Anzahl der Objekte auf dieser Seite
    metadata JSONB,
        -- Zusätzliche Metadaten (z.B. Bounding Box, Objekt-Typen, etc.)
    png_artifact_id UUID,
        -- FK zu artifacts (exportierte PNG)
    pdf_artifact_id UUID,
        -- FK zu artifacts (exportierte PDF-Seite, falls einzeln)
    CONSTRAINT pages_page_number_check CHECK (page_number >= 1)
);

CREATE INDEX idx_pages_job_id ON pages(job_id);
CREATE INDEX idx_pages_job_page ON pages(job_id, page_number);
CREATE UNIQUE INDEX idx_pages_job_page_unique ON pages(job_id, page_number);

ALTER TABLE pages
    ADD CONSTRAINT fk_pages_job FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    ADD CONSTRAINT fk_pages_png_artifact FOREIGN KEY (png_artifact_id) REFERENCES artifacts(id) ON DELETE SET NULL,
    ADD CONSTRAINT fk_pages_pdf_artifact FOREIGN KEY (pdf_artifact_id) REFERENCES artifacts(id) ON DELETE SET NULL;

-- ============================================================
-- 5) ASSETS (Optional) - Asset-Verwaltung
-- ============================================================

CREATE TABLE IF NOT EXISTS assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    asset_type VARCHAR(50) NOT NULL,
        -- Typ: image, font, template, etc.
    original_file_name TEXT NOT NULL,
    artifact_id UUID NOT NULL,
        -- FK zu artifacts (die eigentliche Datei)
    width INTEGER,
        -- Breite in px (für Bilder)
    height INTEGER,
        -- Höhe in px (für Bilder)
    mime_type VARCHAR(100),
    metadata JSONB,
        -- Zusätzliche Metadaten (z.B. EXIF, Font-Metadaten, etc.)
    CONSTRAINT assets_asset_type_check CHECK (asset_type IN ('image', 'font', 'template', 'other'))
);

CREATE INDEX idx_assets_type ON assets(asset_type);
CREATE INDEX idx_assets_artifact_id ON assets(artifact_id);

ALTER TABLE assets
    ADD CONSTRAINT fk_assets_artifact FOREIGN KEY (artifact_id) REFERENCES artifacts(id) ON DELETE CASCADE;

-- ============================================================
-- 6) HELPER FUNCTIONS
-- ============================================================

-- Automatisches Update von updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_jobs_updated_at
    BEFORE UPDATE ON jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_assets_updated_at
    BEFORE UPDATE ON assets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- 7) VIEWS (Optional - für einfachere Queries)
-- ============================================================

-- View: Jobs mit Artefakt-Informationen
CREATE OR REPLACE VIEW jobs_with_artifacts AS
SELECT
    j.*,
    input_a.storage_uri AS input_uri,
    input_a.file_name AS input_file_name,
    output_a.storage_uri AS output_uri,
    output_a.file_name AS output_file_name
FROM jobs j
LEFT JOIN artifacts input_a ON j.input_artifact_id = input_a.id
LEFT JOIN artifacts output_a ON j.output_artifact_id = output_a.id;

-- View: Pages mit Export-Artefakten
CREATE OR REPLACE VIEW pages_with_exports AS
SELECT
    p.*,
    png_a.storage_uri AS png_uri,
    pdf_a.storage_uri AS pdf_uri
FROM pages p
LEFT JOIN artifacts png_a ON p.png_artifact_id = png_a.id
LEFT JOIN artifacts pdf_a ON p.pdf_artifact_id = pdf_a.id;

-- ============================================================
-- 8) COMMENTS (Dokumentation)
-- ============================================================

COMMENT ON TABLE jobs IS 'Layout-Kompilierungs-Jobs (JSON → SLA → PNG/PDF)';
COMMENT ON TABLE artifacts IS 'Artefakte (Dateien) gespeichert in MinIO/S3';
COMMENT ON TABLE job_logs IS 'Logging für Jobs';
COMMENT ON TABLE pages IS 'Seiten-Metadaten (aus Layout-JSON)';
COMMENT ON TABLE assets IS 'Asset-Verwaltung (Bilder, Fonts, Templates)';

COMMENT ON COLUMN jobs.metadata IS 'Zusätzliche Metadaten (JSON): Kompilierungs-Optionen, DPI, etc.';
COMMENT ON COLUMN artifacts.metadata IS 'Zusätzliche Metadaten (JSON): DPI, Dimensionen, etc.';
COMMENT ON COLUMN pages.metadata IS 'Zusätzliche Metadaten (JSON): Bounding Box, Objekt-Typen, etc.';

