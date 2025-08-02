-- Clean installation script for CAPE GPT database schema
-- Run this if you encounter function conflicts

-- Step 1: Drop all existing functions (run first if you get type conflicts)
DO $$ 
DECLARE
    r RECORD;
BEGIN
    -- Drop all existing functions that might conflict
    FOR r IN (SELECT proname, oidvectortypes(proargtypes) as argtypes 
              FROM pg_proc p JOIN pg_namespace n ON p.pronamespace = n.oid 
              WHERE n.nspname = 'public' 
              AND proname IN ('match_syllabus_sections', 'match_question_chunks', 'hybrid_search', 'get_topic_probability_stats', 'refresh_topic_stats', 'update_updated_at_column')) 
    LOOP
        EXECUTE 'DROP FUNCTION IF EXISTS ' || r.proname || '(' || r.argtypes || ') CASCADE';
    END LOOP;
END $$;

-- Step 2: Drop existing tables and views
DROP MATERIALIZED VIEW IF EXISTS topic_stats CASCADE;
DROP VIEW IF EXISTS question_stats CASCADE; 
DROP VIEW IF EXISTS syllabus_stats CASCADE;
DROP TABLE IF EXISTS question_topic_mappings CASCADE;
DROP TABLE IF EXISTS syllabus_chunks CASCADE;
DROP TABLE IF EXISTS question_chunks CASCADE;

-- Step 3: Enable extensions
CREATE EXTENSION IF NOT EXISTS vector;

-- Step 4: Create tables (same as main script)
CREATE TABLE question_chunks (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding VECTOR(384) NOT NULL,
    source TEXT DEFAULT 'CAPE',
    year INTEGER,
    paper TEXT,
    question_id TEXT,
    subject TEXT NOT NULL,
    topic TEXT,
    sub_topic TEXT,
    syllabus_section TEXT,
    specific_objective_id INTEGER,
    images JSONB DEFAULT '[]'::JSONB,
    equations JSONB DEFAULT '[]'::JSONB,
    confidence_score FLOAT DEFAULT 1.0,
    is_math_heavy BOOLEAN DEFAULT FALSE,
    processing_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE syllabus_chunks (
    id SERIAL PRIMARY KEY,
    subject TEXT NOT NULL,
    module TEXT,
    topic_title TEXT NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding VECTOR(384) NOT NULL,
    difficulty_level TEXT,
    learning_objectives TEXT[],
    keywords TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE question_topic_mappings (
    id SERIAL PRIMARY KEY,
    question_id INTEGER NOT NULL REFERENCES question_chunks(id) ON DELETE CASCADE,
    topic_id INTEGER NOT NULL REFERENCES syllabus_chunks(id) ON DELETE CASCADE,
    confidence_score FLOAT DEFAULT 1.0,
    mapping_type TEXT DEFAULT 'semantic',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (question_id, topic_id)
);

-- Step 5: Create basic functions only
CREATE OR REPLACE FUNCTION match_syllabus_sections(
    query_embedding vector(384), 
    query_subject text, 
    match_threshold float, 
    match_count int
)
RETURNS TABLE(
    id int, 
    module text, 
    topic_title text, 
    chunk_text text, 
    similarity float
) AS $$
SELECT 
    sc.id, 
    sc.module, 
    sc.topic_title, 
    sc.chunk_text, 
    1 - (sc.embedding <=> query_embedding) AS similarity
FROM syllabus_chunks sc
WHERE sc.subject = query_subject 
    AND (sc.embedding <=> query_embedding) < (1 - match_threshold)
ORDER BY sc.embedding <=> query_embedding
LIMIT match_count;
$$ LANGUAGE sql STABLE;

CREATE OR REPLACE FUNCTION match_question_chunks(
    query_embedding vector(384), 
    query_subject text, 
    match_threshold float, 
    match_count int
)
RETURNS TABLE(
    id int, 
    content text, 
    year int, 
    paper text, 
    question_id text, 
    subject text, 
    topic text,
    similarity float
) AS $$
SELECT 
    qc.id, 
    qc.content, 
    qc.year, 
    qc.paper, 
    qc.question_id, 
    qc.subject, 
    qc.topic,
    1 - (qc.embedding <=> query_embedding) AS similarity
FROM question_chunks qc
WHERE qc.subject = query_subject 
    AND (qc.embedding <=> query_embedding) < (1 - match_threshold)
ORDER BY qc.embedding <=> query_embedding
LIMIT match_count;
$$ LANGUAGE sql STABLE;

-- Step 6: Create basic indexes
CREATE INDEX question_chunks_embedding_idx ON question_chunks
USING hnsw (embedding vector_cosine_ops);

CREATE INDEX syllabus_chunks_embedding_idx ON syllabus_chunks
USING hnsw (embedding vector_cosine_ops);

CREATE INDEX question_chunks_subject_year_idx ON question_chunks (subject, year);
CREATE INDEX syllabus_chunks_subject_module_idx ON syllabus_chunks (subject, module);

-- Step 7: Create materialized view
CREATE MATERIALIZED VIEW topic_stats AS
SELECT
    qc.subject,
    sc.module,
    sc.topic_title,
    qc.year,
    COUNT(DISTINCT qc.id) AS occurrence_ct
FROM
    question_chunks qc
JOIN question_topic_mappings qtm ON qc.id = qtm.question_id
JOIN syllabus_chunks sc ON qtm.topic_id = sc.id
WHERE qc.year IS NOT NULL
GROUP BY
    qc.subject, sc.module, sc.topic_title, qc.year;

-- Success message
SELECT 'CAPE GPT database schema created successfully!' AS status;