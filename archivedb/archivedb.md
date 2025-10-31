# DuPrez Archive Database - Drop & Recreate Script

This document provides the complete SQL script to drop and recreate the DuPrez Audio Archive database structure.

## Database Information

- **Database Name**: archivedb.db
- **Database Type**: DuckDB
- **Location**: `./achivedb/archivedb.db`
- **Primary Table**: audio_files


## Complete Drop & Recreate Script

```sql
-- ============================================================================
-- DuPrez Audio Archive Database Schema v2.0
-- Drop & Recreate Script
-- ============================================================================

-- WARNING: This will delete all existing data!
-- Always backup your database before running this script.

-- ============================================================================
-- 1. DROP EXISTING OBJECTS
-- ============================================================================

-- Drop table (this will also drop associated constraints)
DROP TABLE IF EXISTS audio_files;

-- Drop sequence
DROP SEQUENCE IF EXISTS audio_files_id_seq;

-- ============================================================================
-- 2. CREATE SEQUENCE FOR AUTO-INCREMENT ID
-- ============================================================================

CREATE SEQUENCE audio_files_id_seq START 1;

-- ============================================================================
-- 3. CREATE MAIN TABLE: audio_files
-- ============================================================================

CREATE TABLE audio_files (

    id INTEGER PRIMARY KEY DEFAULT nextval('audio_files_id_seq'),
    -- Core Metadata (from folder/filename/XML parsing)
    -- ========================================================================
    author VARCHAR,                    -- Author/creator (for audiobooks)
    title VARCHAR NOT NULL,            -- Title of programme or audiobook
    episode_chapter VARCHAR,           -- Episode/chapter identifier (e.g., "01/10")
    recording_date DATE,               -- Date recorded or broadcast (YYYY-MM-DD)
    description TEXT,                  -- Synopsis or description
    content_type VARCHAR,              -- "radio_program", "audiobook", etc.
    channel VARCHAR,                   -- Broadcast channel (e.g., "BBC Radio 4")
    genre VARCHAR,                     -- Genre/category (e.g., "Drama", "Comedy")
    series_length INTEGER,             -- Total number of episodes in series
    year INTEGER,                      -- Recording year
    -- Embedded Metadata (from ID3/M4A audio file tags)

    album VARCHAR,                     -- Album/series name from audio tags
    track_number VARCHAR(20),          -- Track number in format "N/Total"
    publisher VARCHAR,                 -- Publisher or label
    language VARCHAR(10),              -- ISO language code (e.g., "en", "en-GB")
    -- Audio Properties (from file analysis)
    duration_seconds DECIMAL(10,2),    -- Duration in seconds
    bitrate_kbps INTEGER,              -- Bitrate in kbps
    sample_rate_hz INTEGER,            -- Sample rate in Hz
    audio_channels INTEGER,            -- Number of audio channels (1=mono, 2=stereo)
    -- File Properties
    file_path VARCHAR NOT NULL UNIQUE, -- Full path to audio file (unique constraint)
    file_name VARCHAR NOT NULL,        -- Filename only
    file_size_bytes BIGINT,            -- File size in bytes
    audio_format VARCHAR(10),          -- Audio format ("MP3", "M4A", "MP4")
    -- Metadata Tracking
    metadata_source VARCHAR,           -- Source of metadata ("embedded", "xml", "hybrid")
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- Record creation timestamp
);

-- ============================================================================
-- 4. CREATE INDEXES FOR QUERY OPTIMIZATION
-- ============================================================================

-- Index on author for searches like "Find all works by author X"
CREATE INDEX idx_author ON audio_files(author);

-- Index on title for searches like "Find series by title"
CREATE INDEX idx_title ON audio_files(title);

-- Index on recording_date for date range queries
CREATE INDEX idx_recording_date ON audio_files(recording_date);

-- Index on content_type for filtering by content type
CREATE INDEX idx_content_type ON audio_files(content_type);

-- Index on channel for filtering by broadcast channel
CREATE INDEX idx_channel ON audio_files(channel);

-- Index on album for searches using embedded metadata
CREATE INDEX idx_album ON audio_files(album);

-- ============================================================================
-- 5. VERIFICATION QUERIES
-- ============================================================================

-- Verify table structure
DESCRIBE audio_files;

-- Verify indexes
SELECT * FROM duckdb_indexes() WHERE table_name = 'audio_files';

-- Check record count (should be 0 for new database)
SELECT COUNT(*) FROM audio_files;

-- ============================================================================
-- END OF SCRIPT
-- ============================================================================
```

## Column Definitions

### Primary Key
- **id**: Auto-incrementing unique identifier for each record

### Core Metadata Fields
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| author | VARCHAR | Yes | Author/creator of the content |
| title | VARCHAR | No | Title of the programme or audiobook |
| episode_chapter | VARCHAR | Yes | Episode or chapter identifier |
| recording_date | DATE | Yes | Date of recording or broadcast |
| description | TEXT | Yes | Synopsis or description of content |
| content_type | VARCHAR | Yes | Type of content (radio_program, audiobook) |
| channel | VARCHAR | Yes | Broadcast channel (BBC Radio 4, etc.) |
| genre | VARCHAR | Yes | Genre/category (Drama, Comedy, Crime, etc.) |
| series_length | INTEGER | Yes | Total episodes in the series |
| year | INTEGER | Yes | Year of recording |

### Embedded Metadata Fields (from audio tags)
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| album | VARCHAR | Yes | Album/series name from audio file tags |
| track_number | VARCHAR(20) | Yes | Track number in "N/Total" format |
| publisher | VARCHAR | Yes | Publisher or label information |
| language | VARCHAR(10) | Yes | ISO language code |

### Audio Properties
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| duration_seconds | DECIMAL(10,2) | Yes | Duration of audio in seconds |
| bitrate_kbps | INTEGER | Yes | Audio bitrate in kilobits per second |
| sample_rate_hz | INTEGER | Yes | Sample rate in Hertz |
| audio_channels | INTEGER | Yes | Number of audio channels (1=mono, 2=stereo) |

### File Properties
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| file_path | VARCHAR | No | Full path to audio file (UNIQUE) |
| file_name | VARCHAR | No | Filename only |
| file_size_bytes | BIGINT | Yes | File size in bytes |
| audio_format | VARCHAR(10) | Yes | Audio format (MP3, M4A, MP4) |

### Metadata Tracking
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| metadata_source | VARCHAR | Yes | Source of metadata extraction |
| created_at | TIMESTAMP | No | Record creation timestamp (auto-set) |

## Indexes

The following indexes are created for query performance optimization:

1. **idx_author** - On `author` column
2. **idx_title** - On `title` column
3. **idx_recording_date** - On `recording_date` column
4. **idx_content_type** - On `content_type` column
5. **idx_channel** - On `channel` column
6. **idx_album** - On `album` column

