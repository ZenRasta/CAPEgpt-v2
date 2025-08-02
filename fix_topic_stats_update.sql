-- Fix for topic_stats materialized view issues
-- Run this to fix an existing database where topic_stats is empty

-- Add unique index to support concurrent refresh (if not exists)
CREATE UNIQUE INDEX IF NOT EXISTS topic_stats_unique_idx ON topic_stats (subject, module, topic_title, year);

-- Update the refresh function to handle both cases
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

-- Now refresh the materialized view to populate it
SELECT refresh_topic_stats();

-- Verify the refresh worked
SELECT COUNT(*) as topic_stats_count FROM topic_stats;