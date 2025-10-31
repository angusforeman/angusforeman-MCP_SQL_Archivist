#!/usr/bin/env python3
import duckdb
import json
import os

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, 'archivedb.db')

def import_jsonl(conn, jsonl_path, clear_existing=False):
    """Import JSONL file to database"""
    if clear_existing:
        conn.execute('DELETE FROM audio_files')
        print("✓ Cleared existing data")
    
    records = []
    with open(jsonl_path, 'r') as f:
        for line in f:
            record = json.loads(line)
            
            # Convert series_length to integer if present
            series_length = None
            if record.get('series_length'):
                try:
                    series_length = int(record['series_length'])
                except (ValueError, TypeError):
                    series_length = None
            
            # Convert year to integer if present
            year = None
            if record.get('year'):
                try:
                    year = int(record['year'])
                except (ValueError, TypeError):
                    year = None
            
            # Validate and clean recording_date
            recording_date = record.get('recording_date')
            if recording_date:
                # Check for invalid dates (e.g., month 00, day 00)
                try:
                    from datetime import datetime
                    datetime.strptime(recording_date, '%Y-%m-%d')
                except (ValueError, TypeError):
                    # Invalid date format or values, set to None
                    recording_date = None
            
            records.append((
                record.get('author'),
                record.get('title'),
                record.get('episode_chapter'),
                recording_date,
                record.get('description'),
                record.get('content_type'),
                record.get('channel'),
                record.get('genre'),
                series_length,
                year,
                record.get('file_path'),
                record.get('file_name'),
                record.get('metadata_source', 'unknown'),
                record.get('duration_seconds'),
                record.get('file_size_bytes'),
                record.get('audio_format'),
                record.get('bitrate_kbps'),
                record.get('album'),
                record.get('track_number'),
                record.get('publisher'),
                record.get('language'),
                record.get('sample_rate_hz'),
                record.get('audio_channels')
            ))
    
    # Use INSERT OR REPLACE to handle duplicates based on file_path
    conn.executemany('''
        INSERT INTO audio_files 
        (author, title, episode_chapter, recording_date, description, 
         content_type, channel, genre, series_length, year,
         file_path, file_name, metadata_source,
         duration_seconds, file_size_bytes, audio_format, bitrate_kbps,
         album, track_number, publisher, language, sample_rate_hz, audio_channels)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (file_path) DO UPDATE SET
            author = EXCLUDED.author,
            title = EXCLUDED.title,
            episode_chapter = EXCLUDED.episode_chapter,
            recording_date = EXCLUDED.recording_date,
            description = EXCLUDED.description,
            content_type = EXCLUDED.content_type,
            channel = EXCLUDED.channel,
            genre = EXCLUDED.genre,
            series_length = EXCLUDED.series_length,
            year = EXCLUDED.year,
            file_name = EXCLUDED.file_name,
            metadata_source = EXCLUDED.metadata_source,
            duration_seconds = EXCLUDED.duration_seconds,
            file_size_bytes = EXCLUDED.file_size_bytes,
            audio_format = EXCLUDED.audio_format,
            bitrate_kbps = EXCLUDED.bitrate_kbps,
            album = EXCLUDED.album,
            track_number = EXCLUDED.track_number,
            publisher = EXCLUDED.publisher,
            language = EXCLUDED.language,
            sample_rate_hz = EXCLUDED.sample_rate_hz,
            audio_channels = EXCLUDED.audio_channels
    ''', records)
    
    print(f"✓ Imported {len(records)} records")
    return len(records)

if __name__ == '__main__':
    import sys
    
    # Check for command line arguments
    jsonl_file = sys.argv[1] if len(sys.argv) > 1 else os.path.join(SCRIPT_DIR, 'archive_metadata.jsonl')
    clear_flag = '--clear' in sys.argv
    
    print(f"Using database: {DB_PATH}")
    print(f"Using metadata file: {jsonl_file}\n")
    
    conn = duckdb.connect(DB_PATH)
    count = import_jsonl(conn, jsonl_file, clear_existing=clear_flag)
    conn.close()
    print(f"\n✓ Database ready: {DB_PATH} ({count} files indexed)")
