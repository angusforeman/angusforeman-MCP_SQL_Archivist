# DuPrez Archive Database - Drop & Recreate Script

## Recreating the DB 
See the readme.db

## Database Information

- **Database Name**: archivedb.db
- **Database Type**: DuckDB
- **Location**: `./achivedb/archivedb.db`
- **Primary Table**: audio_files

## Schema Overview

### Table: audio_files

The main table storing metadata for all archived audio files.

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique identifier for each audio file |
| filename | VARCHAR | NOT NULL | Original filename of the audio file |
| filepath | VARCHAR | NOT NULL | Full path to the audio file |
| file_size | BIGINT | | File size in bytes |
| duration | DOUBLE | | Duration of audio in seconds |
| sample_rate | INTEGER | | Audio sample rate (e.g., 44100, 48000) |
| channels | INTEGER | | Number of audio channels (1=mono, 2=stereo) |
| bit_depth | INTEGER | | Bit depth of the audio (e.g., 16, 24) |
| format | VARCHAR | | Audio file format (e.g., WAV, MP3, FLAC) |
| codec | VARCHAR | | Audio codec used |
| artist | VARCHAR | | Artist or performer name |
| title | VARCHAR | | Track title |
| album | VARCHAR | | Album name |
| year | INTEGER | | Release year |
| genre | VARCHAR | | Music genre |
| track_number | INTEGER | | Track number in album |
| date_archived | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | When the file was added to archive |
| date_modified | TIMESTAMP | | Last modification date of the file |
| checksum | VARCHAR | | File checksum (MD5/SHA256) for integrity |
| notes | TEXT | | Additional notes or metadata |

### Indexes

- Primary key index on `id`
- Potential indexes on frequently queried columns (e.g., `artist`, `album`, `date_archived`)

### Constraints

- `id`: AUTO INCREMENT PRIMARY KEY
- `filename`: REQUIRED (NOT NULL)
- `filepath`: REQUIRED (NOT NULL), UNIQUE to prevent duplicates
- `date_archived`: Automatically set to current timestamp on insert

