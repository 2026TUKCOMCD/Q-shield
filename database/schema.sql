-- 1. 스캔 메인 테이블
CREATE TABLE scans (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    github_url VARCHAR(500) NOT NULL,
    repo_name VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL,  -- QUEUED, IN_PROGRESS, COMPLETED, FAILED
    progress DECIMAL(3, 2) DEFAULT 0.0,  -- 0.00 ~ 1.00
    current_message TEXT,
    
    -- 기본 통계 (당신이 계산)
    total_files INTEGER DEFAULT 0,
    total_vulnerabilities INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);

-- 2. 언어별 통계
CREATE TABLE language_stats (
    id SERIAL PRIMARY KEY,
    scan_uuid UUID REFERENCES scans(uuid) ON DELETE CASCADE,
    language VARCHAR(50),
    file_count INTEGER,
    total_lines INTEGER,
    percentage DECIMAL(5, 2)
);

-- 3. 알고리즘 인벤토리
CREATE TABLE algorithm_inventory (
    id SERIAL PRIMARY KEY,
    scan_uuid UUID REFERENCES scans(uuid) ON DELETE CASCADE,
    algorithm VARCHAR(50),  -- RSA, ECC, AES, MD5, SHA1, etc.
    usage_count INTEGER,
    percentage DECIMAL(5, 2),
    risk_level VARCHAR(20)  -- HIGH, MEDIUM, LOW
);

-- 4. 알고리즘 발생 위치 (상세)
CREATE TABLE algorithm_occurrences (
    id SERIAL PRIMARY KEY,
    inventory_id INTEGER REFERENCES algorithm_inventory(id) ON DELETE CASCADE,
    file_path TEXT,
    line_number INTEGER,
    code_snippet TEXT,
    scanner_type VARCHAR(20)  -- SAST, SCA, CONFIG
);

-- 5. 파일별 위험도 (히트맵용)
CREATE TABLE file_risks (
    id SERIAL PRIMARY KEY,
    scan_uuid UUID REFERENCES scans(uuid) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    risk_score DECIMAL(5, 2),  -- 0.00 ~ 100.00
    vulnerability_count INTEGER,
    is_directory BOOLEAN DEFAULT FALSE
);

-- 인덱스
CREATE INDEX idx_scans_status ON scans(status);
CREATE INDEX idx_scans_created ON scans(created_at DESC);
CREATE INDEX idx_file_risks_scan ON file_risks(scan_uuid);
CREATE INDEX idx_algorithm_inventory_scan ON algorithm_inventory(scan_uuid);