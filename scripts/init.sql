CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE question_chunks (
    id SERIAL PRIMARY KEY,
    subject TEXT NOT NULL,
    year INTEGER,
    paper TEXT,
    question_id TEXT,
    chunk_text TEXT NOT NULL,
    embedding VECTOR(1536)
);

CREATE TABLE syllabus_chunks (
    id SERIAL PRIMARY KEY,
    subject TEXT NOT NULL,
    topic_title TEXT,
    chunk_text TEXT NOT NULL,
    embedding VECTOR(1536)
);

-- Materialized view for topic stats
CREATE MATERIALIZED VIEW topic_stats AS
SELECT subject, topic_title, year, COUNT(*) AS occurrence_ct
FROM syllabus_chunks -- Adjust based on actual relations
GROUP BY subject, topic_title, year;

-- Indices
CREATE INDEX ON question_chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ON syllabus_chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ON question_chunks (subject, year); 