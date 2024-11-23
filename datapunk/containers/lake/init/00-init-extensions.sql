-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";
CREATE EXTENSION IF NOT EXISTS "postgis";
CREATE EXTENSION IF NOT EXISTS "timescaledb";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS vector;
CREATE SCHEMA IF NOT EXISTS timeseries;
CREATE SCHEMA IF NOT EXISTS spatial;

-- Set up roles and permissions
DO $$
BEGIN
    -- Create roles if they don't exist
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'lake_read') THEN
        CREATE ROLE lake_read;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'lake_write') THEN
        CREATE ROLE lake_write;
    END IF;
    
    -- Grant permissions
    GRANT USAGE ON SCHEMA core TO lake_read, lake_write;
    GRANT USAGE ON SCHEMA vector TO lake_read, lake_write;
    GRANT USAGE ON SCHEMA timeseries TO lake_read, lake_write;
    GRANT USAGE ON SCHEMA spatial TO lake_read, lake_write;
    
    -- Default privileges
    ALTER DEFAULT PRIVILEGES IN SCHEMA core 
        GRANT SELECT ON TABLES TO lake_read;
    ALTER DEFAULT PRIVILEGES IN SCHEMA core 
        GRANT INSERT, UPDATE, DELETE ON TABLES TO lake_write;
END
$$; 