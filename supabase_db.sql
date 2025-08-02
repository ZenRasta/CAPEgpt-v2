-- Drop existing materialized view and tables (destructive! All data will be lost)
DROP MATERIALIZED VIEW IF EXISTS topic_stats CASCADE;
DROP VIEW IF EXISTS question_stats CASCADE;
DROP VIEW IF EXISTS syllabus_stats CASCADE;
DROP TABLE IF EXISTS question_topic_mappings CASCADE;
DROP TABLE IF EXISTS syllabus_chunks CASCADE;
DROP TABLE IF EXISTS question_chunks CASCADE;

-- Drop existing functions to avoid type conflicts
-- Handle different vector dimensions and parameter types
DROP FUNCTION IF EXISTS match_syllabus_sections(vector(1536), text, double precision, integer) CASCADE;
DROP FUNCTION IF EXISTS match_syllabus_sections(vector(384), text, double precision, integer) CASCADE;
DROP FUNCTION IF EXISTS match_syllabus_sections(vector, text, double precision, integer) CASCADE;
DROP FUNCTION IF EXISTS match_question_chunks(vector(1536), text, double precision, integer) CASCADE;
DROP FUNCTION IF EXISTS match_question_chunks(vector(384), text, double precision, integer) CASCADE;
DROP FUNCTION IF EXISTS match_question_chunks(vector, text, double precision, integer) CASCADE;
DROP FUNCTION IF EXISTS hybrid_search CASCADE;
DROP FUNCTION IF EXISTS get_topic_probability_stats CASCADE;
DROP FUNCTION IF EXISTS refresh_topic_stats CASCADE;
DROP FUNCTION IF EXISTS update_updated_at_column CASCADE;
DROP FUNCTION IF EXISTS refresh_materialized_view CASCADE;

-- Enable the pgvector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the question_chunks table
-- This table stores vectorized chunks of past-paper questions.
-- Chunking strategy: One row per full question or sub-question to preserve context,
-- especially for math-heavy content where splitting mid-equation could lead to
-- loss of meaning or poor embedding quality. Chunks should be self-contained,
-- including any diagrams described in text or LaTeX math notation.
-- This avoids issues like incomplete formulas, mismatched variables, or fragmented
-- problem statements that could degrade similarity search accuracy.
-- Enhanced with JSONB for images/equations and OCR metadata.
CREATE TABLE question_chunks (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,                  -- Main extracted text (cleaned/OCR/Vision)
    embedding VECTOR(384) NOT NULL,         -- Embedding from all-MiniLM-L6-v2 (384 dimensions)
    source TEXT DEFAULT 'CAPE',             -- e.g., 'CAPE', 'User Upload'
    year INTEGER,                           -- e.g., 2023
    paper TEXT,                             -- e.g., 'Unit 1 Paper 2', 'Paper 1'
    question_id TEXT,                       -- e.g., '1a', '2bii'
    subject TEXT NOT NULL,                  -- e.g., 'Pure Mathematics', 'Physics'
    topic TEXT,                             -- Inferred topic (e.g., 'Differentiation')
    sub_topic TEXT,                         -- Finer sub-topic (e.g., 'Polynomial Functions')
    syllabus_section TEXT,                  -- Mapped syllabus text snippet
    specific_objective_id INTEGER,          -- FK to syllabus_chunks.id (optional)
    -- Enhanced image storage with OCR metadata
    images JSONB DEFAULT '[]'::JSONB,       -- Array of image objects: 
                                           -- [{"page": 1, "index": 0, "base64_data": "...", "ocr_text": "...", 
                                           --   "is_math_heavy": true, "extension": "png"}]
    -- Enhanced equation storage with LaTeX and metadata  
    equations JSONB DEFAULT '[]'::JSONB,    -- Array of equation objects:
                                           -- [{"latex": "x^2 + 2x + 1", "text": "$x^2 + 2x + 1$", 
                                           --   "type": "inline|display"}]
    -- Processing metadata
    confidence_score FLOAT DEFAULT 1.0,    -- Confidence in OCR/extraction quality
    is_math_heavy BOOLEAN DEFAULT FALSE,    -- Flag for mathematical content
    processing_notes TEXT,                  -- Notes about OCR processing
    created_at TIMESTAMP DEFAULT NOW(),     -- When the chunk was created
    updated_at TIMESTAMP DEFAULT NOW()      -- When the chunk was last updated
);

-- Create the syllabus_chunks table
-- This table stores vectorized chunks of syllabus objectives.
-- Chunking strategy: One row per syllabus heading or objective to maintain topical
-- integrity. This ensures embeddings capture complete learning outcomes without
-- splitting descriptive text or example problems, which is crucial for accurate
-- matching to math/physics queries where objectives often include sample equations
-- or concepts that shouldn't be fragmented.
-- Added module for better filtering and metadata for enhanced search.
CREATE TABLE syllabus_chunks (
    id SERIAL PRIMARY KEY,
    subject TEXT NOT NULL,                  -- e.g., 'Pure Mathematics', 'Physics'
    module TEXT,                            -- e.g., 'Unit 1 Module 1: Basic Algebra'
    topic_title TEXT NOT NULL,              -- e.g., 'Differentiation'
    chunk_text TEXT NOT NULL,               -- Full text of the objective/heading, including LaTeX
    embedding VECTOR(384) NOT NULL,         -- Embedding from all-MiniLM-L6-v2 (384 dimensions)
    -- Additional metadata for better search
    difficulty_level TEXT,                  -- e.g., 'Basic', 'Intermediate', 'Advanced'
    learning_objectives TEXT[],             -- Array of specific learning objectives
    keywords TEXT[],                        -- Array of key terms for this topic
    created_at TIMESTAMP DEFAULT NOW(),     -- When the chunk was created
    updated_at TIMESTAMP DEFAULT NOW()      -- When the chunk was last updated
);

-- Create the question_topic_mappings table
-- This table maps questions to syllabus topics, enabling aggregation for stats.
-- Each row links a question_chunk to one or more syllabus_chunks.
-- Foreign keys ensure referential integrity.
CREATE TABLE question_topic_mappings (
    id SERIAL PRIMARY KEY,
    question_id INTEGER NOT NULL REFERENCES question_chunks(id) ON DELETE CASCADE,
    topic_id INTEGER NOT NULL REFERENCES syllabus_chunks(id) ON DELETE CASCADE,
    confidence_score FLOAT DEFAULT 1.0,    -- Score indicating match strength (0.0 to 1.0)
    mapping_type TEXT DEFAULT 'semantic',   -- 'semantic', 'keyword', 'manual'
    created_at TIMESTAMP DEFAULT NOW(),     -- When the mapping was created
    UNIQUE (question_id, topic_id)         -- Prevent duplicate mappings
);

-- Create indexes for question_chunks
-- HNSW index for efficient approximate nearest neighbor search on embeddings using cosine distance.
-- This is optimized for high-dimensional vector similarity in math/physics questions.
-- Updated for 384-dimensional vectors from all-MiniLM-L6-v2
CREATE INDEX question_chunks_embedding_idx ON question_chunks
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);  -- Tunable params for balance between speed and accuracy

-- B-tree indexes for common query patterns
CREATE INDEX question_chunks_subject_year_idx ON question_chunks (subject, year);
CREATE INDEX question_chunks_subject_topic_idx ON question_chunks (subject, topic);
CREATE INDEX question_chunks_is_math_heavy_idx ON question_chunks (is_math_heavy);
CREATE INDEX question_chunks_confidence_score_idx ON question_chunks (confidence_score);

-- GIN indexes for JSONB arrays (efficient contains/searches)
CREATE INDEX question_chunks_images_gin ON question_chunks USING GIN (images);
CREATE INDEX question_chunks_equations_gin ON question_chunks USING GIN (equations);

-- Text search indexes for content
CREATE INDEX question_chunks_content_gin ON question_chunks USING GIN (to_tsvector('english', content));

-- Create indexes for syllabus_chunks
-- HNSW index similar to above, for syllabus embedding searches
-- Updated for 384-dimensional vectors
CREATE INDEX syllabus_chunks_embedding_idx ON syllabus_chunks
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- B-tree indexes for quick syllabus filtering
CREATE INDEX syllabus_chunks_subject_module_idx ON syllabus_chunks (subject, module);
CREATE INDEX syllabus_chunks_subject_topic_idx ON syllabus_chunks (subject, topic_title);

-- GIN indexes for array fields
CREATE INDEX syllabus_chunks_keywords_gin ON syllabus_chunks USING GIN (keywords);
CREATE INDEX syllabus_chunks_learning_objectives_gin ON syllabus_chunks USING GIN (learning_objectives);

-- Text search index for syllabus content
CREATE INDEX syllabus_chunks_text_gin ON syllabus_chunks USING GIN (to_tsvector('english', chunk_text));

-- Create indexes for question_topic_mappings
CREATE INDEX question_topic_mappings_question_id_idx ON question_topic_mappings (question_id);
CREATE INDEX question_topic_mappings_topic_id_idx ON question_topic_mappings (topic_id);
CREATE INDEX question_topic_mappings_confidence_idx ON question_topic_mappings (confidence_score);
CREATE INDEX question_topic_mappings_type_idx ON question_topic_mappings (mapping_type);

-- Create the topic_stats materialized view
-- This view pre-computes topic appearances per year for fast probability calculations.
-- It aggregates from question_chunks joined through question_topic_mappings to syllabus_chunks.
-- Counts occurrences of topics per year based on mappings.
-- Enhanced with additional statistical metrics.
-- NOTE: If this view is empty, the backend automatically falls back to direct calculation
-- from the underlying tables, so the system remains functional.
CREATE MATERIALIZED VIEW topic_stats AS
SELECT
    qc.subject,
    sc.module,
    sc.topic_title,
    qc.year,
    COUNT(DISTINCT qc.id) AS occurrence_ct,                    -- Count unique questions linked to the topic
    AVG(qtm.confidence_score) AS avg_confidence,              -- Average mapping confidence
    COUNT(DISTINCT qc.paper) AS papers_appeared,              -- Number of different papers topic appeared in
    COUNT(CASE WHEN qc.is_math_heavy THEN 1 END) AS math_heavy_count, -- Count of math-heavy questions
    MAX(qc.created_at) AS last_updated                        -- When data was last updated
FROM
    question_chunks qc
JOIN question_topic_mappings qtm ON qc.id = qtm.question_id
JOIN syllabus_chunks sc ON qtm.topic_id = sc.id
WHERE qc.year IS NOT NULL  -- Only include questions with known years
GROUP BY
    qc.subject, sc.module, sc.topic_title, qc.year;

-- Indexes on the materialized view for faster queries
CREATE INDEX topic_stats_subject_year_idx ON topic_stats (subject, year);
CREATE INDEX topic_stats_topic_occurrence_idx ON topic_stats (topic_title, occurrence_ct DESC);
CREATE INDEX topic_stats_subject_topic_idx ON topic_stats (subject, topic_title);

-- Add unique index to support concurrent refresh
-- This enables REFRESH MATERIALIZED VIEW CONCURRENTLY
CREATE UNIQUE INDEX topic_stats_unique_idx ON topic_stats (subject, module, topic_title, year);

-- Initial population of the materialized view
-- This ensures the view has data immediately after creation
-- Run this after topic mappings are created
-- REFRESH MATERIALIZED VIEW topic_stats;

-- Enhanced Function: Match Syllabus Sections (for RPC in backend)
-- Updated for 384-dimensional vectors and enhanced return fields
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
    similarity float,
    keywords text[],
    difficulty_level text
) AS $$
SELECT 
    sc.id, 
    sc.module, 
    sc.topic_title, 
    sc.chunk_text, 
    1 - (sc.embedding <=> query_embedding) AS similarity,
    sc.keywords,
    sc.difficulty_level
FROM syllabus_chunks sc
WHERE sc.subject = query_subject 
    AND (sc.embedding <=> query_embedding) < (1 - match_threshold)
ORDER BY sc.embedding <=> query_embedding
LIMIT match_count;
$$ LANGUAGE sql STABLE;

-- Enhanced Function: Match Question Chunks (for RPC in backend)
-- Updated for 384-dimensional vectors and enhanced return fields
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
    sub_topic text,
    similarity float,
    is_math_heavy boolean,
    confidence_score float
) AS $$
SELECT 
    qc.id, 
    qc.content, 
    qc.year, 
    qc.paper, 
    qc.question_id, 
    qc.subject, 
    qc.topic,
    qc.sub_topic,
    1 - (qc.embedding <=> query_embedding) AS similarity,
    qc.is_math_heavy,
    qc.confidence_score
FROM question_chunks qc
WHERE qc.subject = query_subject 
    AND (qc.embedding <=> query_embedding) < (1 - match_threshold)
ORDER BY qc.embedding <=> query_embedding
LIMIT match_count;
$$ LANGUAGE sql STABLE;

-- Function to refresh materialized view (for maintenance)
-- Updated to handle both initial refresh and concurrent refresh
CREATE OR REPLACE FUNCTION refresh_topic_stats()
RETURNS void AS $$
BEGIN
    -- Try concurrent refresh first (requires unique index)
    BEGIN
        REFRESH MATERIALIZED VIEW CONCURRENTLY topic_stats;
    EXCEPTION WHEN OTHERS THEN
        -- Fallback to non-concurrent refresh if concurrent fails
        -- This handles the case when the view is empty or has no unique index
        REFRESH MATERIALIZED VIEW topic_stats;
    END;
END;
$$ LANGUAGE plpgsql;

-- Function for semantic search across both tables
CREATE OR REPLACE FUNCTION hybrid_search(
    query_embedding vector(384),
    query_subject text,
    search_questions boolean DEFAULT true,
    search_syllabus boolean DEFAULT true,
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 10
)
RETURNS TABLE(
    source_table text,
    id int,
    content text,
    similarity float,
    metadata jsonb
) AS $$
BEGIN
    RETURN QUERY
    (
        -- Search questions if requested
        SELECT 
            'question_chunks'::text as source_table,
            qc.id,
            qc.content,
            1 - (qc.embedding <=> query_embedding) AS similarity,
            jsonb_build_object(
                'year', qc.year,
                'paper', qc.paper,
                'question_id', qc.question_id,
                'topic', qc.topic,
                'is_math_heavy', qc.is_math_heavy,
                'confidence_score', qc.confidence_score
            ) as metadata
        FROM question_chunks qc
        WHERE search_questions 
            AND qc.subject = query_subject 
            AND (qc.embedding <=> query_embedding) < (1 - match_threshold)
        ORDER BY qc.embedding <=> query_embedding
        LIMIT CASE WHEN search_syllabus THEN match_count / 2 ELSE match_count END
    )
    UNION ALL
    (
        -- Search syllabus if requested
        SELECT 
            'syllabus_chunks'::text as source_table,
            sc.id,
            sc.chunk_text as content,
            1 - (sc.embedding <=> query_embedding) AS similarity,
            jsonb_build_object(
                'module', sc.module,
                'topic_title', sc.topic_title,
                'keywords', sc.keywords,
                'difficulty_level', sc.difficulty_level
            ) as metadata
        FROM syllabus_chunks sc
        WHERE search_syllabus 
            AND sc.subject = query_subject 
            AND (sc.embedding <=> query_embedding) < (1 - match_threshold)
        ORDER BY sc.embedding <=> query_embedding
        LIMIT CASE WHEN search_questions THEN match_count / 2 ELSE match_count END
    )
    ORDER BY similarity DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to get topic statistics for probability calculations
CREATE OR REPLACE FUNCTION get_topic_probability_stats(
    topic_name text,
    subject_name text,
    years_back int DEFAULT 10
)
RETURNS TABLE(
    topic_title text,
    total_appearances int,
    years_appeared int,
    recent_appearances int,
    probability_score float,
    probability_category text
) AS $$
DECLARE
    current_year int := EXTRACT(YEAR FROM NOW());
    min_year int := current_year - years_back;
BEGIN
    RETURN QUERY
    SELECT 
        ts.topic_title,
        SUM(ts.occurrence_ct)::int as total_appearances,
        COUNT(DISTINCT ts.year)::int as years_appeared,
        SUM(CASE WHEN ts.year >= min_year THEN ts.occurrence_ct ELSE 0 END)::int as recent_appearances,
        CASE 
            WHEN COUNT(DISTINCT ts.year) > 0 THEN 
                (COUNT(DISTINCT CASE WHEN ts.year >= min_year THEN ts.year END)::float / GREATEST(years_back, 1))
            ELSE 0.0
        END as probability_score,
        CASE 
            WHEN COUNT(DISTINCT CASE WHEN ts.year >= min_year THEN ts.year END)::float / GREATEST(years_back, 1) >= 0.7 THEN 'High'
            WHEN COUNT(DISTINCT CASE WHEN ts.year >= min_year THEN ts.year END)::float / GREATEST(years_back, 1) >= 0.3 THEN 'Medium'
            ELSE 'Low'
        END as probability_category
    FROM topic_stats ts
    WHERE ts.topic_title = topic_name 
        AND ts.subject = subject_name
    GROUP BY ts.topic_title;
END;
$$ LANGUAGE plpgsql STABLE;

-- Trigger to update updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers to tables with updated_at columns
CREATE TRIGGER update_question_chunks_updated_at 
    BEFORE UPDATE ON question_chunks 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_syllabus_chunks_updated_at 
    BEFORE UPDATE ON syllabus_chunks 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create a view for easy question statistics
CREATE VIEW question_stats AS
SELECT 
    subject,
    COUNT(*) as total_questions,
    COUNT(DISTINCT year) as years_covered,
    COUNT(DISTINCT paper) as papers_covered,
    COUNT(CASE WHEN is_math_heavy THEN 1 END) as math_heavy_questions,
    AVG(confidence_score) as avg_confidence,
    MIN(year) as earliest_year,
    MAX(year) as latest_year
FROM question_chunks
WHERE year IS NOT NULL
GROUP BY subject;

-- Create a view for syllabus coverage statistics  
CREATE VIEW syllabus_stats AS
SELECT 
    subject,
    COUNT(*) as total_sections,
    COUNT(DISTINCT module) as modules_covered,
    COUNT(DISTINCT topic_title) as topics_covered,
    array_agg(DISTINCT topic_title ORDER BY topic_title) as all_topics
FROM syllabus_chunks
GROUP BY subject;

-- Create the question_queries table for popularity tracking
-- This table tracks each query submission to analyze popular questions
CREATE TABLE question_queries (
    id SERIAL PRIMARY KEY,
    query_text TEXT NOT NULL,
    query_hash VARCHAR(64) NOT NULL,
    subject TEXT NOT NULL,
    matched_question_ids INTEGER[],
    user_session_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for question_queries
CREATE INDEX question_queries_hash_idx ON question_queries (query_hash);
CREATE INDEX question_queries_subject_idx ON question_queries (subject);
CREATE INDEX question_queries_created_at_idx ON question_queries (created_at);
CREATE INDEX question_queries_session_idx ON question_queries (user_session_id);

-- Comments for documentation
COMMENT ON TABLE question_chunks IS 'Stores vectorized chunks of past-paper questions with OCR and equation extraction';
COMMENT ON TABLE syllabus_chunks IS 'Stores vectorized chunks of syllabus objectives and learning outcomes';
COMMENT ON TABLE question_topic_mappings IS 'Maps questions to relevant syllabus topics for statistical analysis';
COMMENT ON TABLE question_queries IS 'Tracks query submissions for popularity analytics and trending analysis';
COMMENT ON MATERIALIZED VIEW topic_stats IS 'Pre-computed statistics for topic appearance frequency and probability calculations';

COMMENT ON COLUMN question_chunks.embedding IS 'Vector embedding from all-MiniLM-L6-v2 model (384 dimensions)';
COMMENT ON COLUMN question_chunks.images IS 'JSONB array of extracted images with OCR metadata';
COMMENT ON COLUMN question_chunks.equations IS 'JSONB array of mathematical equations in LaTeX format';
COMMENT ON COLUMN question_chunks.is_math_heavy IS 'Boolean flag indicating if question contains significant mathematical content';

COMMENT ON FUNCTION match_question_chunks IS 'Performs vector similarity search on question chunks with enhanced metadata';
COMMENT ON FUNCTION match_syllabus_sections IS 'Performs vector similarity search on syllabus chunks with keywords';
COMMENT ON FUNCTION hybrid_search IS 'Combined semantic search across questions and syllabus with unified results';
COMMENT ON FUNCTION get_topic_probability_stats IS 'Calculates probability statistics for topic reappearance prediction';

-- Create the popular_questions materialized view
-- This view pre-computes popularity statistics for trending questions
CREATE MATERIALIZED VIEW popular_questions AS
SELECT 
    unnest(matched_question_ids) as question_id,
    subject,
    COUNT(*) as query_count,
    COUNT(DISTINCT user_session_id) as unique_users,
    MAX(created_at) as last_queried,
    RANK() OVER (PARTITION BY subject ORDER BY COUNT(*) DESC) as popularity_rank
FROM question_queries 
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY unnest(matched_question_ids), subject;

-- Indexes on the popular_questions materialized view
CREATE INDEX popular_questions_subject_idx ON popular_questions (subject);
CREATE INDEX popular_questions_rank_idx ON popular_questions (popularity_rank);
CREATE INDEX popular_questions_count_idx ON popular_questions (query_count DESC);

-- Add unique index to support concurrent refresh
CREATE UNIQUE INDEX popular_questions_unique_idx ON popular_questions (question_id, subject);

-- Function to get popular questions (for RPC in backend)
CREATE OR REPLACE FUNCTION get_popular_questions(
    query_subject text,
    result_limit int DEFAULT 10
)
RETURNS TABLE(
    question_id int,
    content text,
    year int,
    paper text,
    question_text text,
    topic text,
    query_count bigint,
    unique_users bigint,
    popularity_rank bigint,
    last_queried timestamp
) AS $$
SELECT 
    pq.question_id,
    qc.content,
    qc.year,
    qc.paper,
    qc.question_id as question_text,
    qc.topic,
    pq.query_count,
    pq.unique_users,
    pq.popularity_rank,
    pq.last_queried
FROM popular_questions pq
JOIN question_chunks qc ON pq.question_id = qc.id
WHERE pq.subject = query_subject
ORDER BY pq.popularity_rank
LIMIT result_limit;
$$ LANGUAGE sql STABLE;

-- Function to refresh popular_questions materialized view
CREATE OR REPLACE FUNCTION refresh_popular_questions()
RETURNS void AS $$
BEGIN
    -- Try concurrent refresh first (requires unique index)
    BEGIN
        REFRESH MATERIALIZED VIEW CONCURRENTLY popular_questions;
    EXCEPTION WHEN OTHERS THEN
        -- Fallback to non-concurrent refresh if concurrent fails
        REFRESH MATERIALIZED VIEW popular_questions;
    END;
END;
$$ LANGUAGE plpgsql;