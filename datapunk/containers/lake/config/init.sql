-- Lake Service Database Initialization
-- This script sets up the core database structure for the Lake service,
-- enabling advanced data storage capabilities and security features.

-- Enable required extensions for multi-modal data handling
-- vector: Enables ML model embedding storage and similarity search
-- timescaledb: Optimizes time-series data storage and querying
-- postgis: Provides geospatial data support
-- pg_cron: Enables scheduled maintenance and data processing tasks
-- pg_partman: Manages table partitioning for large datasets
-- pg_trgm: Supports fuzzy text search and matching
-- hstore: Enables key-value pair storage within columns
CREATE EXTENSION IF NOT EXISTS vector;      -- For AI/ML embeddings
CREATE EXTENSION IF NOT EXISTS timescaledb; -- For time-series optimization
CREATE EXTENSION IF NOT EXISTS postgis;     -- For location data
CREATE EXTENSION IF NOT EXISTS pg_cron;     -- For scheduled tasks
CREATE EXTENSION IF NOT EXISTS pg_partman;  -- For data partitioning
CREATE EXTENSION IF NOT EXISTS pg_trgm;     -- For text similarity
CREATE EXTENSION IF NOT EXISTS hstore;      -- For flexible metadata

-- Create logical data separation for different concerns
-- user_data: Contains core user information and documents
-- imports: Manages data import jobs and their status
CREATE SCHEMA IF NOT EXISTS user_data;
CREATE SCHEMA IF NOT EXISTS imports;

-- Core user management table
-- NOTE: Consider adding OAuth provider columns for future social login support
CREATE TABLE user_data.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB  -- Stores flexible user attributes and preferences
);

-- Document storage with vector embeddings
-- TODO: Add table partitioning for improved query performance
-- TODO: Implement automatic cleanup of old/unused embeddings
CREATE TABLE user_data.documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES user_data.users(id),
    content TEXT NOT NULL,
    content_type TEXT NOT NULL,
    embedding vector(768),  -- Matches standard transformer output dimension
    metadata JSONB,        -- Flexible document attributes
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    source TEXT NOT NULL,  -- Tracks data origin for provenance
    source_timestamp TIMESTAMPTZ  -- Original creation/modification time
);

-- Import job tracking
-- FIXME: Add index on status column for faster job status queries
CREATE TABLE imports.jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES user_data.users(id),
    status TEXT NOT NULL,
    started_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    error TEXT,
    metadata JSONB  -- Stores import configuration and results
);

-- Enable row-level security for multi-tenant data isolation
-- NOTE: Policy definitions should be added in a separate migration
ALTER TABLE user_data.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_data.documents ENABLE ROW LEVEL SECURITY;
