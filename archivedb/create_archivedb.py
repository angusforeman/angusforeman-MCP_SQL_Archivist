#!/usr/bin/env python3
"""
Create the DuPrez Archive Database schema with embedded metadata support.
This script creates the audio_files table with all required fields.
"""
import duckdb
import os
import sys

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, 'archivedb.db')

def create_schema(db_path=None, drop_existing=False):
    """Create the database schema"""
    if db_path is None:
        db_path = DB_PATH
    
    print(f"Creating database schema: {db_path}")
    print("=" * 80)
    
    conn = duckdb.connect(db_path)
    
    if drop_existing:
        print("⚠️  Dropping existing table and sequence...")
        conn.execute('DROP TABLE IF EXISTS audio_files')
        conn.execute('DROP SEQUENCE IF EXISTS audio_files_id_seq')
    
    # Create sequence for auto-incrementing ID
    conn.execute('CREATE SEQUENCE IF NOT EXISTS audio_files_id_seq START 1')
    print("✓ Created sequence: audio_files_id_seq")
    
    # Create main table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS audio_files (
            -- Primary key
            id INTEGER PRIMARY KEY DEFAULT nextval('audio_files_id_seq'),
            
            -- Core metadata (from folder/filename/XML)
            author VARCHAR,
            title VARCHAR NOT NULL,
            episode_chapter VARCHAR,
            recording_date DATE,
            description TEXT,
            content_type VARCHAR,
            channel VARCHAR,
            genre VARCHAR,
            series_length INTEGER,
            year INTEGER,
            
            -- Embedded metadata (from ID3/M4A tags)
            album VARCHAR,
            track_number VARCHAR(20),
            publisher VARCHAR,
            language VARCHAR(10),
            
            -- Audio properties (from file analysis)
            duration_seconds DECIMAL(10,2),
            bitrate_kbps INTEGER,
            sample_rate_hz INTEGER,
            audio_channels INTEGER,
            
            -- File properties
            file_path VARCHAR NOT NULL UNIQUE,
            file_name VARCHAR NOT NULL,
            file_size_bytes BIGINT,
            audio_format VARCHAR(10),
            
            -- Metadata tracking
            metadata_source VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✓ Created table: audio_files")
    
    # Create indexes for common queries
    conn.execute('CREATE INDEX IF NOT EXISTS idx_author ON audio_files(author)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_title ON audio_files(title)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_recording_date ON audio_files(recording_date)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_content_type ON audio_files(content_type)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_channel ON audio_files(channel)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_album ON audio_files(album)')
    print("✓ Created indexes")
    
    # Show the schema
    print("\n" + "=" * 80)
    print("Table Schema:")
    print("=" * 80)
    schema = conn.execute('DESCRIBE audio_files').fetchall()
    for col in schema:
        null_str = "NULL" if col[2] == "YES" else "NOT NULL"
        print(f'  {col[0]:25s} {col[1]:20s} {null_str:10s}')
    
    # Show table statistics
    print("\n" + "=" * 80)
    print("Table Statistics:")
    print("=" * 80)
    count = conn.execute('SELECT COUNT(*) FROM audio_files').fetchone()[0]
    print(f'  Total records: {count}')
    
    conn.close()
    print("\n✓ Database schema created successfully")
    return db_path

if __name__ == '__main__':
    drop_flag = '--drop' in sys.argv or '--recreate' in sys.argv
    
    if drop_flag:
        response = input("⚠️  This will drop the existing table and all data. Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            sys.exit(0)
    
    create_schema(drop_existing=drop_flag)
