#!/usr/bin/env python3
import os
import json
import re
from pathlib import Path
from datetime import datetime
import yaml
import xmltodict
from mutagen import File as MutagenFile

def extract_from_folder(file_path, archive_root):
    """Extract metadata from folder structure"""
    rel_path = os.path.relpath(file_path, archive_root)
    parts = rel_path.split(os.sep)
    
    metadata = {}
    # For nested structures, use the last folder as title (before the filename)
    # and second-to-last as potential series/collection name
    if len(parts) >= 2:
        # Author is typically the first folder after the archive root
        if parts[0]:
            metadata['author'] = parts[0]
        # Title is the folder immediately containing the file (last folder)
        metadata['title'] = parts[-2] if len(parts) >= 2 else parts[0]
    if len(parts) >= 3 and parts[2].isdigit():
        metadata['year'] = parts[2]
    
    return metadata

def extract_from_filename(filename):
    """Extract metadata from filename using patterns"""
    metadata = {}
    
    # Try date pattern: YYYY-MM-DD_Title.mp3
    match = re.match(r'(\d{4}-\d{2}-\d{2})_([^.]+)\.mp3', filename, re.IGNORECASE)
    if match:
        metadata['recording_date'] = match.group(1)
        metadata['episode_chapter'] = match.group(2)
        return metadata
    
    # Try date pattern: YYYY-MM-DD - Title.mp3
    match = re.match(r'(\d{4}-\d{2}-\d{2})\s*-\s*(.+)\.mp3', filename, re.IGNORECASE)
    if match:
        metadata['recording_date'] = match.group(1)
        metadata['episode_chapter'] = match.group(2).strip()
        return metadata
    
    # Try date with dots pattern: YYYY.MM.DD sXXeYY - Title.mp3
    match = re.match(r'(.+?)\s+(\d{4})\.(\d{2})\.(\d{2})\s+(s\d+e\d+|s\d+esp)\s*-\s*(.+)\.mp3', filename, re.IGNORECASE)
    if match:
        title = match.group(1)
        year = match.group(2)
        month = match.group(3)
        day = match.group(4)
        episode = match.group(5).upper()
        subtitle = match.group(6).strip()
        metadata['title'] = title
        metadata['recording_date'] = f"{year}-{month}-{day}"
        metadata['episode_chapter'] = f"{episode} - {subtitle}"
        return metadata
    
    # Try Title YYYY-MM-DD.mp3 or Title YYYY-MM-DD Subtitle.mp3
    match = re.match(r'(.+?)\s+(\d{4}-\d{2}-\d{2})(?:\s+(.+))?\.mp3', filename, re.IGNORECASE)
    if match:
        title = match.group(1).strip()
        date = match.group(2)
        subtitle = match.group(3).strip() if match.group(3) else None
        metadata['title'] = title
        metadata['recording_date'] = date
        if subtitle:
            metadata['episode_chapter'] = subtitle
        return metadata
    
    # Try Title YYYY-MM Location, Guest.mp3
    match = re.match(r'(.+?)\s+(\d{4})-(\d{2})\s+(.+?)(?:,\s*(.+))?\.mp3', filename, re.IGNORECASE)
    if match:
        title = match.group(1).strip()
        year = match.group(2)
        month = match.group(3)
        location = match.group(4).strip()
        guest = match.group(5).strip() if match.group(5) else None
        metadata['title'] = title
        metadata['recording_date'] = f"{year}-{month}-01"
        episode_info = location
        if guest:
            episode_info += f", {guest}"
        metadata['episode_chapter'] = episode_info
        return metadata
    
    # Try series/episode pattern: Title - SSEE - YYYY-MM-DD.mp3 or Title - SSEEYY - YYYY-MM-DD.mp3
    match = re.match(r'(.+?)\s*-\s*(\d{4,6})\s*-\s*(\d{4}-\d{2}-\d{2})\.mp3', filename, re.IGNORECASE)
    if match:
        title = match.group(1).strip()
        episode_code = match.group(2)
        date = match.group(3)
        # Parse episode code (e.g., 6501 = S65E01)
        if len(episode_code) == 4:
            series = episode_code[:2]
            episode = episode_code[2:]
            metadata['title'] = title
            metadata['episode_chapter'] = f"S{series}E{episode}"
            metadata['recording_date'] = date
            return metadata
    
    # Try short series/episode pattern: SS-EE SSSEE.mp3
    match = re.match(r'(\d{2})-(\d{2})\s+S(\d+)E(\d+)\.mp3', filename, re.IGNORECASE)
    if match:
        series = match.group(1)
        episode = match.group(2)
        metadata['episode_chapter'] = f"S{series}E{episode}"
        return metadata
    
    # Try series/episode in brackets: Title sXXeYY - Subtitle [channel].mp3
    match = re.match(r'(.+?)\s+(s\d+e\d+)\s*-\s*([^\[]+)(?:\[([^\]]+)\])?\.mp3', filename, re.IGNORECASE)
    if match:
        title = match.group(1).strip()
        episode = match.group(2).upper()
        subtitle = match.group(3).strip()
        channel = match.group(4).strip() if match.group(4) else None
        metadata['title'] = title
        metadata['episode_chapter'] = f"{episode} - {subtitle}"
        if channel:
            metadata['genre'] = channel
        return metadata
    
    # Try underscore date pattern: Title_YYYYMMDD.mp3
    match = re.match(r'(.+)_(\d{8})\.mp3', filename, re.IGNORECASE)
    if match:
        title = match.group(1).replace('_', ' ')
        date_str = match.group(2)
        year = date_str[0:4]
        month = date_str[4:6]
        day = date_str[6:8]
        metadata['title'] = title
        metadata['recording_date'] = f"{year}-{month}-{day}"
        return metadata
    
    # Try chapter pattern: Chapter NN.mp3
    match = re.match(r'Chapter (\d+)\.mp3', filename, re.IGNORECASE)
    if match:
        metadata['episode_chapter'] = f"Chapter {match.group(1)}"
        metadata['content_type'] = 'audiobook'
        return metadata
    
    return metadata

def extract_from_xml(xml_path, mp3_filename):
    """Extract metadata from XML manifest"""
    if not os.path.exists(xml_path):
        return {}
    
    with open(xml_path, 'r', encoding='utf-8') as f:
        xml_dict = xmltodict.parse(f.read())
    
    # Handle MP3Manifest format (BBC archive format)
    if 'MP3Manifest' in xml_dict:
        prog_details = xml_dict['MP3Manifest'].get('ProgrammeDetails', {})
        if prog_details:
            # Extract episode number from filename pattern like "[1-6]"
            episode_match = re.search(r'\[(\d+)-(\d+)\]', mp3_filename)
            episode_info = f"{episode_match.group(1)}/{episode_match.group(2)}" if episode_match else None
            
            return {
                'title': prog_details.get('@title'),
                'episode_chapter': episode_info or prog_details.get('@episode'),
                'recording_date': prog_details.get('@date'),
                'description': prog_details.get('@description'),
                'content_type': 'radio_program',
                'channel': prog_details.get('@channel').lower() if prog_details.get('@channel') else None,
                'genre': prog_details.get('@genre').lower() if prog_details.get('@genre') else None,
                'series_length': prog_details.get('@seriesLength')
            }
    
    # Handle legacy archive format (from quickstart example)
    items = xml_dict.get('archive', {}).get('item', [])
    if not isinstance(items, list):
        items = [items]
    
    for item in items:
        if item.get('file') == mp3_filename:
            metadata = {
                'title': item.get('title'),
                'content_type': item.get('type').lower() if item.get('type') else None,
                'genre': item.get('genre').lower() if item.get('genre') else None,
                'recording_date': item.get('date'),
                'description': item.get('description')
            }
            # Only add author if it exists
            if item.get('author'):
                metadata['author'] = item.get('author')
            return metadata
    
    return {}

def extract_from_embedded_tags(file_path):
    """Extract metadata from embedded audio tags (ID3, M4A, etc.)"""
    try:
        audio = MutagenFile(file_path)
        if audio is None:
            return {}
        
        metadata = {}
        
        # Extract ID3/M4A tags if present
        if hasattr(audio, 'tags') and audio.tags:
            tags = audio.tags
            
            # Try to extract common fields with multiple tag formats
            # Title
            if 'TIT2' in tags:  # MP3 ID3
                metadata['title'] = str(tags['TIT2'])
            elif '\xa9nam' in tags:  # M4A
                metadata['title'] = str(tags['\xa9nam'][0])
            
            # Artist (could be author for audiobooks or channel for radio)
            artist = None
            if 'TPE1' in tags:  # MP3 ID3
                artist = str(tags['TPE1'])
            elif '\xa9ART' in tags:  # M4A
                artist = str(tags['\xa9ART'][0])
            
            # For audiobooks, artist is author; for radio, it might be channel
            # We'll store it and let the logic below decide
            if artist:
                metadata['artist_tag'] = artist
            
            # Album
            if 'TALB' in tags:  # MP3 ID3
                metadata['album'] = str(tags['TALB'])
            elif '\xa9alb' in tags:  # M4A
                metadata['album'] = str(tags['\xa9alb'][0])
            
            # Track number
            if 'TRCK' in tags:  # MP3 ID3
                metadata['track_number'] = str(tags['TRCK'])
            elif 'trkn' in tags:  # M4A
                track_info = tags['trkn'][0]
                if isinstance(track_info, tuple):
                    metadata['track_number'] = f"{track_info[0]}/{track_info[1]}" if len(track_info) > 1 else str(track_info[0])
                else:
                    metadata['track_number'] = str(track_info)
            
            # Genre
            genre = None
            if 'TCON' in tags:  # MP3 ID3
                genre = str(tags['TCON'])
            elif '\xa9gen' in tags:  # M4A
                genre = str(tags['\xa9gen'][0])
            if genre:
                metadata['genre_tag'] = genre
            
            # Recording date/year
            if 'TDRC' in tags:  # MP3 ID3
                date_str = str(tags['TDRC'])
                # TDRC can be just year or full date
                if len(date_str) == 4:
                    metadata['year'] = int(date_str)
                elif len(date_str) >= 10:
                    try:
                        metadata['recording_date'] = date_str[:10]
                    except:
                        pass
            elif '\xa9day' in tags:  # M4A
                date_str = str(tags['\xa9day'][0])
                if len(date_str) == 4:
                    metadata['year'] = int(date_str)
                elif len(date_str) >= 10:
                    metadata['recording_date'] = date_str[:10]
            
            # Description/Comment
            if 'COMM' in tags:  # MP3 ID3
                comm = tags['COMM']
                if hasattr(comm, 'text'):
                    metadata['description'] = str(comm.text[0]) if comm.text else None
                else:
                    metadata['description'] = str(comm)
            elif '\xa9cmt' in tags:  # M4A
                metadata['description'] = str(tags['\xa9cmt'][0])
            
            # Publisher
            if 'TPUB' in tags:  # MP3 ID3
                metadata['publisher'] = str(tags['TPUB'])
            
            # Language
            if 'TLAN' in tags:  # MP3 ID3
                metadata['language'] = str(tags['TLAN'])
        
        # Extract audio properties (always available)
        if hasattr(audio, 'info'):
            info = audio.info
            if hasattr(info, 'length'):
                metadata['duration_seconds'] = round(info.length, 2)
            if hasattr(info, 'bitrate') and info.bitrate:
                metadata['bitrate_kbps'] = info.bitrate // 1000
            if hasattr(info, 'sample_rate'):
                metadata['sample_rate_hz'] = info.sample_rate
            if hasattr(info, 'channels'):
                metadata['audio_channels'] = info.channels
        
        # File properties
        metadata['file_size_bytes'] = os.path.getsize(file_path)
        metadata['audio_format'] = os.path.splitext(file_path)[1][1:].upper()
        
        return metadata
    except Exception as e:
        # Silently return empty dict if file can't be read
        return {}

def scan_archive(archive_path, output_jsonl):
    """Scan archive and extract metadata"""
    archive_root = Path(archive_path)
    results = []
    
    # Find all MP3 files (case-insensitive)
    mp3_files = list(archive_root.rglob('*.mp3')) + list(archive_root.rglob('*.MP3'))
    
    total_files = len(mp3_files)
    print(f"Found {total_files} audio files to process\n")
    
    for idx, mp3_file in enumerate(mp3_files, 1):
        # Print progress
        print(f"[{idx}/{total_files}] Processing: {mp3_file.name}")
        
        # Extract from all sources
        folder_meta = extract_from_folder(str(mp3_file), str(archive_root))
        filename_meta = extract_from_filename(mp3_file.name)
        
        # Check for XML manifest - try both formats:
        # 1. Same filename with .xml extension (e.g., "file.mp3" -> "file.xml")
        xml_path_same = mp3_file.with_suffix('.xml')
        # 2. Legacy format with manifest.xml in same directory
        xml_path_legacy = mp3_file.parent / 'manifest.xml'
        
        xml_meta = {}
        if xml_path_same.exists():
            xml_meta = extract_from_xml(str(xml_path_same), mp3_file.name)
        elif xml_path_legacy.exists():
            xml_meta = extract_from_xml(str(xml_path_legacy), mp3_file.name)
        
        # Extract embedded metadata (AUTHORITATIVE)
        embedded_meta = extract_from_embedded_tags(str(mp3_file))
        
        # Merge metadata with hierarchical priority: EMBEDDED > XML > Filename > Folder
        # Start with folder (lowest priority)
        metadata = {**folder_meta}
        
        # Add filename parsing
        metadata.update({k: v for k, v in filename_meta.items() if v is not None})
        
        # Add XML metadata
        metadata.update({k: v for k, v in xml_meta.items() if v is not None})
        
        # Add embedded metadata (HIGHEST PRIORITY - overwrites all previous)
        metadata.update({k: v for k, v in embedded_meta.items() if v is not None})
        
        # Handle special mapping from embedded tags
        # If artist_tag exists and no author, use it for audiobooks
        if 'artist_tag' in metadata and not metadata.get('author'):
            # If genre suggests audiobook, use artist as author
            genre_tag = metadata.get('genre_tag', '').lower()
            if 'audiobook' in genre_tag or 'book' in genre_tag:
                metadata['author'] = metadata['artist_tag']
        
        # Map genre_tag to genre if genre not already set (convert to lowercase)
        if 'genre_tag' in metadata and not metadata.get('genre'):
            metadata['genre'] = metadata['genre_tag'].lower() if metadata['genre_tag'] else None
        
        # Clean up temporary fields
        metadata.pop('artist_tag', None)
        metadata.pop('genre_tag', None)
        
        metadata['file_path'] = str(mp3_file)
        metadata['file_name'] = mp3_file.name
        
        # Update metadata_source to reflect embedded tags
        if embedded_meta:
            metadata['metadata_source'] = 'embedded'
        elif xml_meta:
            metadata['metadata_source'] = 'xml'
        elif filename_meta:
            metadata['metadata_source'] = 'filename'
        else:
            metadata['metadata_source'] = 'folder'
        
        # Classify .m4a files as audiobooks if not already classified
        if '.m4a' in mp3_file.name.lower() and not metadata.get('content_type'):
            metadata['content_type'] = 'audiobook'
        
        # If there's an author, set content_type to audiobook (unless already set by XML)
        if metadata.get('author') and not metadata.get('content_type'):
            metadata['content_type'] = 'audiobook'
        
        # Ensure content_type, channel, and genre are lowercase
        if metadata.get('content_type'):
            metadata['content_type'] = metadata['content_type'].lower()
        if metadata.get('channel'):
            metadata['channel'] = metadata['channel'].lower()
        if metadata.get('genre'):
            genre = metadata['genre'].lower()
            # Normalize 'audio book' and 'audiobooks' to 'audiobook'
            if genre in ('audio book', 'audiobooks'):
                genre = 'audiobook'
            metadata['genre'] = genre
        
        results.append(metadata)
    
    # Write to JSONL
    with open(output_jsonl, 'w') as f:
        for record in results:
            f.write(json.dumps(record) + '\n')
    
    print(f"\n✓ Extracted metadata from {len(results)} files")
    print(f"Output: {output_jsonl}")
    return len(results)

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) == 3:
        archive_path = sys.argv[1]
        output_file = sys.argv[2]
    elif len(sys.argv) == 2:
        archive_path = sys.argv[1]
        output_file = 'metadata.jsonl'
    else:
        print("Usage: python3 extract_metadata.py <archive_path> [output_file]")
        print("Example: python3 extract_metadata.py '/path/with spaces/archive' output.jsonl")
        sys.exit(1)
    
    # Verify the path exists
    if not os.path.exists(archive_path):
        print(f"❌ Error: Archive path does not exist: {archive_path}")
        sys.exit(1)
    
    if not os.path.isdir(archive_path):
        print(f"❌ Error: Path is not a directory: {archive_path}")
        sys.exit(1)
    
    print(f"📁 Scanning archive: {archive_path}")
    print(f"📝 Output file: {output_file}")
    
    count = scan_archive(archive_path, output_file)
    print(f"\n✓ Part B Complete: {count} files processed")
