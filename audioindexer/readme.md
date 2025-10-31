# AudioIndexer tool
This is a sample tool for creating audio content indexes
This tool comes with no guarantees

## Overview

The AudioIndexer tool scans audio archives and extracts metadata from multiple sources, creating a structured JSONL output file that can be imported into databases for querying and analysis.

## extract_metadata.py

### How It Works

The `extract_metadata.py` script extracts metadata from audio files (MP3, M4A, etc.) using a hierarchical approach with four data sources:

1. **Folder Structure** (Lowest Priority)
   - Extracts author from first-level folder
   - Extracts title from containing folder
   - Extracts year from folder names

2. **Filename Patterns** (Medium Priority)
   - Date patterns: `YYYY-MM-DD_Title.mp3`, `YYYY-MM-DD - Title.mp3`
   - Series/Episode: `Title sXXeYY - Subtitle.mp3`
   - Chapter patterns: `Chapter NN.mp3`
   - Various other formats with dates, locations, guests

3. **XML Manifests** (High Priority)
   - BBC archive format (`MP3Manifest`)
   - Legacy archive format
   - Looks for `filename.xml` or `manifest.xml` in same directory

4. **Embedded Audio Tags** (Highest Priority - Authoritative)
   - ID3 tags (MP3)
   - M4A/AAC tags
   - Extracts: title, artist/author, album, track number, genre, dates, descriptions
   - Audio properties: duration, bitrate, sample rate, channels, file size

**Priority Order**: Embedded tags > XML > Filename > Folder structure

### Features

- **Automatic Content Type Detection**
  - Identifies audiobooks based on author presence or genre tags
  - Radio programs from XML manifests
  - Chapter-based content

- **Comprehensive Metadata Extraction**
  - Core: title, author, episode/chapter, recording date, genre
  - Technical: duration, bitrate, sample rate, channels, file size, format
  - Descriptive: description, publisher, language, series length

- **Progress Tracking**
  - Shows real-time progress during scanning
  - Reports total files found and processed

### Usage

```bash
# Basic usage (outputs to metadata.jsonl)
uv run python extract_metadata.py /path/to/archive

# Specify output file
uv run python extract_metadata.py /path/to/archive output.jsonl

# With spaces in path
uv run python extract_metadata.py '/path/with spaces/archive' output.jsonl
```
The content can be imported using into a db in the ./archivedb/ folder using  import_to_db.py 
```
uv run python import_to_db.py archive_metadata.jsonl --clear
```

### Output Format

The script generates a JSONL (JSON Lines) file where each line is a JSON object containing:

```json
{
  "title": "Episode Title",
  "author": "Author Name",
  "episode_chapter": "S01E01 - Subtitle",
  "recording_date": "2024-01-15",
  "content_type": "audiobook",
  "genre": "fiction",
  "description": "Episode description",
  "duration_seconds": 3600.5,
  "bitrate_kbps": 128,
  "sample_rate_hz": 44100,
  "audio_channels": 2,
  "file_size_bytes": 57600000,
  "audio_format": "MP3",
  "file_path": "/archive/Author/Book/Chapter 01.mp3",
  "file_name": "Chapter 01.mp3",
  "metadata_source": "embedded"
}
```

### Requirements

- Python 3.6+
- Dependencies: `mutagen`, `xmltodict`, `pyyaml`
- Install: `pip install mutagen xmltodict pyyaml`

### Supported Formats

- MP3 (with ID3 tags)
- M4A/AAC (with iTunes-style tags)
- Other formats supported by Mutagen library

### Next Steps

After generating the JSONL file:
1. Review the metadata for accuracy
2. Import to database using `import_to_archivedb.py`
3. Query using `run_archivedb_query.py` or MCP server

