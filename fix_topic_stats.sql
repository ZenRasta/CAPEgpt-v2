-- Fix topic_stats materialized view to support concurrent refresh
-- Add unique index and refresh the view

-- First, refresh the materialized view normally (non-concurrent)
REFRESH MATERIALIZED VIEW topic_stats;

-- Add a unique index to support concurrent refresh in the future
-- This creates a unique constraint on the combination that should be unique
CREATE UNIQUE INDEX topic_stats_unique_idx ON topic_stats (subject, module, topic_title, year);

-- Now refresh it again concurrently to test
REFRESH MATERIALIZED VIEW CONCURRENTLY topic_stats;