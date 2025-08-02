-- Migration: Add question popularity tracking and ranking system
-- This enables "Top 10 Questions" functionality based on various metrics

-- Add popularity columns to questions table
ALTER TABLE questions ADD COLUMN IF NOT EXISTS view_count INTEGER DEFAULT 0;
ALTER TABLE questions ADD COLUMN IF NOT EXISTS last_viewed_at TIMESTAMPTZ;
ALTER TABLE questions ADD COLUMN IF NOT EXISTS share_count INTEGER DEFAULT 0;
ALTER TABLE questions ADD COLUMN IF NOT EXISTS favorite_count INTEGER DEFAULT 0;

-- Create question_interactions table for detailed tracking
CREATE TABLE IF NOT EXISTS question_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    interaction_type TEXT NOT NULL, -- 'view', 'share', 'favorite', 'search_result'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Prevent duplicate interactions within short time window
    UNIQUE(question_id, user_id, interaction_type, created_at)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS question_interactions_question_id_idx ON question_interactions(question_id);
CREATE INDEX IF NOT EXISTS question_interactions_user_id_idx ON question_interactions(user_id);
CREATE INDEX IF NOT EXISTS question_interactions_type_idx ON question_interactions(interaction_type);
CREATE INDEX IF NOT EXISTS question_interactions_created_at_idx ON question_interactions(created_at DESC);

-- Create indexes for popularity queries
CREATE INDEX IF NOT EXISTS questions_view_count_idx ON questions(view_count DESC);
CREATE INDEX IF NOT EXISTS questions_last_viewed_idx ON questions(last_viewed_at DESC);
CREATE INDEX IF NOT EXISTS questions_favorite_count_idx ON questions(favorite_count DESC);

-- Function to update question popularity counters
CREATE OR REPLACE FUNCTION update_question_popularity()
RETURNS TRIGGER AS $$
BEGIN
    -- Update counters based on interaction type
    IF NEW.interaction_type = 'view' THEN
        UPDATE questions 
        SET view_count = view_count + 1,
            last_viewed_at = NEW.created_at
        WHERE id = NEW.question_id;
        
    ELSIF NEW.interaction_type = 'share' THEN
        UPDATE questions 
        SET share_count = share_count + 1
        WHERE id = NEW.question_id;
        
    ELSIF NEW.interaction_type = 'favorite' THEN
        UPDATE questions 
        SET favorite_count = favorite_count + 1
        WHERE id = NEW.question_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update popularity
CREATE TRIGGER update_question_popularity_trigger
    AFTER INSERT ON question_interactions
    FOR EACH ROW EXECUTE FUNCTION update_question_popularity();

-- Function to get trending questions (weighted by recency)
CREATE OR REPLACE FUNCTION get_trending_questions(
    days_window INTEGER DEFAULT 7,
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
    view_count INTEGER,
    favorite_count INTEGER,
    trend_score NUMERIC
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
        q.view_count,
        q.favorite_count,
        -- Trending score: recent views + favorites, weighted by recency
        (
            COALESCE(recent_views.count, 0) * 2.0 +  -- Recent views worth more
            q.favorite_count * 3.0 +                 -- Favorites worth most
            (EXTRACT(EPOCH FROM NOW() - q.created_at) / 86400.0) * -0.1  -- Slight recency boost
        )::NUMERIC as trend_score
    FROM questions q
    LEFT JOIN (
        SELECT 
            qi.question_id,
            COUNT(*) as count
        FROM question_interactions qi
        WHERE qi.interaction_type = 'view'
          AND qi.created_at >= NOW() - INTERVAL '%s days'
        GROUP BY qi.question_id
    ) recent_views ON q.id = recent_views.question_id
    WHERE q.processing_status = 'completed'
    ORDER BY trend_score DESC, q.created_at DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get most popular questions by subject
CREATE OR REPLACE FUNCTION get_popular_questions_by_subject(
    target_subject TEXT,
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
    view_count INTEGER,
    favorite_count INTEGER,
    popularity_rank INTEGER
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
        q.view_count,
        q.favorite_count,
        ROW_NUMBER() OVER (ORDER BY q.view_count DESC, q.favorite_count DESC, q.created_at DESC)::INTEGER as popularity_rank
    FROM questions q
    WHERE q.subject = target_subject
      AND q.processing_status = 'completed'
    ORDER BY q.view_count DESC, q.favorite_count DESC, q.created_at DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get user's most popular questions
CREATE OR REPLACE FUNCTION get_user_popular_questions(
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
    view_count INTEGER,
    favorite_count INTEGER
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
        q.view_count,
        q.favorite_count
    FROM questions q
    WHERE q.user_id = target_user_id
      AND q.processing_status = 'completed'
    ORDER BY q.view_count DESC, q.favorite_count DESC, q.created_at DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Function to record question interaction
CREATE OR REPLACE FUNCTION record_question_interaction(
    question_uuid UUID,
    interaction_type_param TEXT,
    user_uuid UUID DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    actual_user_id UUID;
BEGIN
    -- Use provided user_id or current authenticated user
    actual_user_id := COALESCE(user_uuid, auth.uid());
    
    -- Insert interaction (will be ignored if duplicate within same timestamp)
    INSERT INTO question_interactions (question_id, user_id, interaction_type)
    VALUES (question_uuid, actual_user_id, interaction_type_param)
    ON CONFLICT DO NOTHING;
    
    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Comments for documentation
COMMENT ON TABLE question_interactions IS 'Tracks user interactions with questions for popularity metrics';
COMMENT ON FUNCTION get_trending_questions IS 'Returns trending questions based on recent activity and favorites';
COMMENT ON FUNCTION get_popular_questions_by_subject IS 'Returns most popular questions for a specific subject';
COMMENT ON FUNCTION record_question_interaction IS 'Records user interaction (view, share, favorite) with a question';