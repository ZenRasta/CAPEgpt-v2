-- Migration: Create questions table with storage and full-text search
-- This migration creates a comprehensive question storage system that preserves
-- layout fidelity while remaining searchable and lightweight.

-- Create storage bucket for question images and files
INSERT INTO storage.buckets (id, name, public)
VALUES ('questions', 'questions', false)
ON CONFLICT (id) DO NOTHING;

-- Create questions table
CREATE TABLE IF NOT EXISTS questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL DEFAULT auth.uid(), -- Links to auth.users
    
    -- Original file information
    original_filename TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    file_type TEXT NOT NULL, -- e.g., 'image/png', 'application/pdf'
    storage_path TEXT NOT NULL, -- Path in storage bucket
    signed_url TEXT, -- Temporary signed URL (regenerated as needed)
    
    -- Mathpix processing results
    mathpix_markdown TEXT, -- Full Mathpix markdown output
    mathpix_svg TEXT, -- SVG snapshot from Mathpix (if available)
    mathpix_confidence REAL DEFAULT 0.0, -- Overall confidence score from Mathpix
    ocr_fallback_text TEXT, -- Fallback text from Google Vision if Mathpix fails
    
    -- Rendering decision flags
    uses_svg BOOLEAN DEFAULT FALSE, -- Whether to use SVG or Markdown rendering
    processing_status TEXT DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    processing_error TEXT, -- Error message if processing failed
    
    -- Metadata for search and classification
    subject TEXT, -- e.g., 'Pure Mathematics', 'Physics'
    estimated_year INTEGER, -- Estimated year if detectable from content
    question_type TEXT, -- e.g., 'multiple_choice', 'short_answer', 'essay'
    difficulty_level TEXT, -- e.g., 'basic', 'intermediate', 'advanced'
    topics TEXT[], -- Array of detected topics
    
    -- Full-text search
    search_vector TSVECTOR GENERATED ALWAYS AS (
        setweight(to_tsvector('english', COALESCE(original_filename, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(mathpix_markdown, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(ocr_fallback_text, '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(subject, '')), 'A') ||
        setweight(to_tsvector('english', array_to_string(COALESCE(topics, ARRAY[]::TEXT[]), ' ')), 'B')
    ) STORED,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS questions_user_id_idx ON questions (user_id);
CREATE INDEX IF NOT EXISTS questions_created_at_idx ON questions (created_at DESC);
CREATE INDEX IF NOT EXISTS questions_subject_idx ON questions (subject);
CREATE INDEX IF NOT EXISTS questions_processing_status_idx ON questions (processing_status);
CREATE INDEX IF NOT EXISTS questions_uses_svg_idx ON questions (uses_svg);
CREATE INDEX IF NOT EXISTS questions_search_vector_idx ON questions USING GIN (search_vector);
CREATE INDEX IF NOT EXISTS questions_topics_idx ON questions USING GIN (topics);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_questions_updated_at 
    BEFORE UPDATE ON questions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) policies
ALTER TABLE questions ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own questions
CREATE POLICY questions_select_own ON questions
    FOR SELECT USING (auth.uid() = user_id);

-- Policy: Users can only insert their own questions
CREATE POLICY questions_insert_own ON questions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Policy: Users can only update their own questions
CREATE POLICY questions_update_own ON questions
    FOR UPDATE USING (auth.uid() = user_id);

-- Policy: Users can only delete their own questions
CREATE POLICY questions_delete_own ON questions
    FOR DELETE USING (auth.uid() = user_id);

-- Storage policies for the questions bucket
CREATE POLICY questions_storage_select ON storage.objects
    FOR SELECT USING (
        bucket_id = 'questions' AND 
        auth.uid()::text = (storage.foldername(name))[1]
    );

CREATE POLICY questions_storage_insert ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'questions' AND 
        auth.uid()::text = (storage.foldername(name))[1]
    );

CREATE POLICY questions_storage_update ON storage.objects
    FOR UPDATE USING (
        bucket_id = 'questions' AND 
        auth.uid()::text = (storage.foldername(name))[1]
    );

CREATE POLICY questions_storage_delete ON storage.objects
    FOR DELETE USING (
        bucket_id = 'questions' AND 
        auth.uid()::text = (storage.foldername(name))[1]
    );

-- Function to search questions with full-text search
CREATE OR REPLACE FUNCTION search_questions(
    search_query TEXT,
    user_filter UUID DEFAULT NULL,
    subject_filter TEXT DEFAULT NULL,
    limit_count INTEGER DEFAULT 20
)
RETURNS TABLE(
    id UUID,
    original_filename TEXT,
    mathpix_markdown TEXT,
    uses_svg BOOLEAN,
    subject TEXT,
    topics TEXT[],
    created_at TIMESTAMPTZ,
    rank REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        q.id,
        q.original_filename,
        q.mathpix_markdown,
        q.uses_svg,
        q.subject,
        q.topics,
        q.created_at,
        ts_rank(q.search_vector, plainto_tsquery('english', search_query)) as rank
    FROM questions q
    WHERE 
        (user_filter IS NULL OR q.user_id = user_filter) AND
        (subject_filter IS NULL OR q.subject = subject_filter) AND
        q.search_vector @@ plainto_tsquery('english', search_query) AND
        q.processing_status = 'completed'
    ORDER BY rank DESC, q.created_at DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get user's recent questions
CREATE OR REPLACE FUNCTION get_user_recent_questions(
    target_user_id UUID,
    limit_count INTEGER DEFAULT 10
)
RETURNS TABLE(
    id UUID,
    original_filename TEXT,
    mathpix_markdown TEXT,
    uses_svg BOOLEAN,
    subject TEXT,
    topics TEXT[],
    created_at TIMESTAMPTZ,
    processing_status TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        q.id,
        q.original_filename,
        q.mathpix_markdown,
        q.uses_svg,
        q.subject,
        q.topics,
        q.created_at,
        q.processing_status
    FROM questions q
    WHERE 
        q.user_id = target_user_id
    ORDER BY q.created_at DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Comments for documentation
COMMENT ON TABLE questions IS 'Stores uploaded exam questions with Mathpix processing results and full-text search capabilities';
COMMENT ON COLUMN questions.uses_svg IS 'Boolean flag indicating whether to render SVG (pixel-perfect) or Markdown/KaTeX (quick-load)';
COMMENT ON COLUMN questions.search_vector IS 'Generated tsvector column for full-text search across filename, content, subject, and topics';
COMMENT ON COLUMN questions.storage_path IS 'Path to original file in Supabase storage bucket';
COMMENT ON COLUMN questions.mathpix_confidence IS 'Confidence score from Mathpix API (0.0 to 1.0)';