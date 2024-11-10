# Datapunk Lake Architecture

## Overview

Primary data storage and processing layer, handling bulk data imports and maintaining core database infrastructure.

Referenced from:

- [Datapunk Lake Architecture](./Architecture-Lake.md)

## Build Architecture

### Build Stage

Referenced from Dockerfile:

- [Datapunk Lake Dockerfile](../../datapunk-lake/Dockerfile)

- PostgreSQL 16 base image
- Build tools: build-essential, git
- Extension compilation:
  - pgvector (v0.5.1)
  - pg_partman
  - Custom optimizations

### Runtime Stage

- PostgreSQL 16 base
- Runtime extensions:
  - PostGIS
  - pg_cron
  - postgresql-contrib packages

## Core Components

### PostgreSQL Extensions

- Built from source:
  - pgvector: Vector embeddings
  - pg_partman: Partition management
- Package installations:
  - PostGIS: Spatial data
  - pg_cron: Task scheduling
- Contrib packages:
  - pg_stat_statements
  - hstore
  - pg_trgm

### Storage Configuration

Referenced from: [Datapunk Lake Architecture](./Architecture-Lake.md)
