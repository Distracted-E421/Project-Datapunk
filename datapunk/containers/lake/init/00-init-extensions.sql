-- Lake Service Extensions and Security Configuration
-- Sets up core database capabilities and access control

-- Enable required extensions for multi-modal data handling
-- NOTE: Order matters due to extension dependencies
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";  -- For UUID generation
CREATE EXTENSION IF NOT EXISTS "pgvector";   -- For ML embeddings storage
CREATE EXTENSION IF NOT EXISTS "postgis";    -- For spatial data
CREATE EXTENSION IF NOT EXISTS "timescaledb"; -- For time series optimization

-- Create logical data separation
-- Each schema serves a specific data domain:
-- core: Basic user and system data
-- vector: ML model embeddings and similarity search
-- timeseries: Time-based analytics and metrics
-- spatial: Location and mapping data
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS vector;
CREATE SCHEMA IF NOT EXISTS timeseries;
CREATE SCHEMA IF NOT EXISTS spatial;

-- Set up roles and permissions
-- Implements principle of least privilege with separate read/write roles
-- TODO: Add additional roles for specific data domains
DO $$
BEGIN
    -- Create roles if they don't exist
    -- NOTE: These roles are assigned to service accounts, not end users
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'lake_read') THEN
        CREATE ROLE lake_read;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'lake_write') THEN
        CREATE ROLE lake_write;
    END IF;
    
    -- Grant schema usage permissions
    -- FIXME: Consider more granular permissions per data domain
    GRANT USAGE ON SCHEMA core TO lake_read, lake_write;
    GRANT USAGE ON SCHEMA vector TO lake_read, lake_write;
    GRANT USAGE ON SCHEMA timeseries TO lake_read, lake_write;
    GRANT USAGE ON SCHEMA spatial TO lake_read, lake_write;
    
    -- Set default privileges for new objects
    -- Ensures consistent permissions for future table creation
    -- NOTE: Write role gets full CRUD permissions
    ALTER DEFAULT PRIVILEGES IN SCHEMA core 
        GRANT SELECT ON TABLES TO lake_read;
    ALTER DEFAULT PRIVILEGES IN SCHEMA core 
        GRANT INSERT, UPDATE, DELETE ON TABLES TO lake_write;
END
$$; 