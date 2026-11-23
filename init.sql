-- ==============================================================================
-- Initial Database Setup Script
-- Executed by Docker entrypoint only on first-time volume creation.
-- Schema migrations are managed separately via Alembic (see Section 2).
-- ==============================================================================

-- Enable UUID extension for unique identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Log successful initialization
DO $$
BEGIN
   RAISE NOTICE 'Database % initialized successfully with extension uuid-ossp.', current_database();
END $$;
