import duckdb
import os
import sys
import logging
from datetime import datetime
from tabulate import tabulate

"""Example showing lifespan support for startup/shutdown with strong typing - stdio transport for VS Code."""

# Remove unused imports
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from mcp.server.fastmcp import FastMCP
from mcp.server.session import ServerSession

# Set up logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f'mcp_server_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

# Check for --quiet flag from environment variable or command line
MCP_SERVER_PARAMS = os.getenv("MCP_SERVER_PARAMS", "")
CONSOLE_LOGGING = '--quiet' not in sys.argv and '--quiet' not in MCP_SERVER_PARAMS

handlers = [logging.FileHandler(log_file)]
if CONSOLE_LOGGING:
    handlers.append(logging.StreamHandler(sys.stderr))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=handlers
)
logger = logging.getLogger(__name__)


# Business glossary for the DuPrez Audio Archive
BUSINESS_GLOSSARY = {
    "author": {
        "definition": "The creator or writer of an audiobook or radio programme",
        "db_column": "author",
        "data_type": "VARCHAR",
        "usage_examples": [
            "Find all works by author 'Agatha Christie'",
            "SELECT * FROM audio_files WHERE author = 'Agatha Christie'"
        ],
        "synonyms": ["writer", "creator"],
        "related_terms": ["title", "content_type"]
    },
    "episode": {
        "definition": "A single installment in a series of radio programmes or audiobook chapters",
        "db_column": "episode_chapter",
        "data_type": "VARCHAR",
        "usage_examples": [
            "Find episode 5 of a series",
            "SELECT * FROM audio_files WHERE episode_chapter LIKE '%05/%'"
        ],
        "synonyms": ["chapter", "part", "installment"],
        "related_terms": ["series_length", "title"]
    },
    "genre": {
        "definition": "The category or type of content (e.g., Drama, Comedy, Crime, Documentary)",
        "db_column": "genre",
        "data_type": "VARCHAR",
        "usage_examples": [
            "Find all crime dramas",
            "SELECT * FROM audio_files WHERE genre = 'Crime'"
        ],
        "valid_values": ["Drama", "Comedy", "Crime", "Documentary", "Science Fiction", "Mystery"],
        "synonyms": ["category", "type"],
        "related_terms": ["content_type"]
    },
    "broadcast_date": {
        "definition": "The date when a radio programme was originally broadcast or an audiobook was recorded",
        "db_column": "recording_date",
        "data_type": "DATE",
        "usage_examples": [
            "Find programmes broadcast in 2020",
            "SELECT * FROM audio_files WHERE YEAR(recording_date) = 2020"
        ],
        "synonyms": ["air date", "recording date"],
        "related_terms": ["year", "channel"]
    },
    "channel": {
        "definition": "The BBC radio station that broadcast the programme",
        "db_column": "channel",
        "data_type": "VARCHAR",
        "usage_examples": [
            "Find all BBC Radio 4 programmes",
            "SELECT * FROM audio_files WHERE channel = 'BBC Radio 4'"
        ],
        "valid_values": ["BBC Radio 4", "BBC Radio 4 Extra", "BBC7", "BBC World Service"],
        "synonyms": ["station", "broadcaster"],
        "related_terms": ["content_type"]
    },
        "Clue": {
        "definition": "Clue is a common nickname for the radio program I am Sorry I Havent A Clue",
        "db_column": "title",
        "data_type": "VARCHAR",
        "usage_examples": [
            "How many episodes of Clue are in the archive?",
        ],
        "synonyms": ["I am Sorry I Havent A Clue", "ISIHAC"],
        "related_terms": ["Panel Show", "Comedy"]
    },
        "Wizarding World": {
        "definition": "The Wizarding World referencing all the titles in the Harry Potter series.",
        "db_column": "title",
        "data_type": "VARCHAR",
        "usage_examples": [
            "How many episodes of Wizarding World are in the archive?",
        ],
        "synonyms": ["Harry Potter", "Wizarding World"],
        "related_terms": ["Fantasy", "Adventure"]
    },
        "DLS": {
        "definition": "A shorthand for Dorothy L Sayers, a prolific author of detective fiction whose works are featured in the archive.",
        "db_column": "author",
        "data_type": "VARCHAR",
        "usage_examples": [
            "How many titles by DLS are in the archive?",
        ],
        "synonyms": ["Dorothy L Sayers", "Dorothy Sayers", "Dorothy L. Sayers"],
        "related_terms": ["Golden Age of Crime", "Crime Fiction"]
    }
    # Add more terms here following the same structure
}


# Pass lifespan to server (no database context needed - using direct connections)
mcp = FastMCP("DuPrez Audio Archive v2.0")


@mcp.resource("duprez://overview")
def get_duprez_overview() -> str:
    """Get an overview of the DuPrez archive and its history"""
    return """The DuPrez Audio Archive is a collection of radio programmes
    and audio books recorded between the years 2000 and the present day.
    """

@mcp.resource("db://schema")
def get_database_schema() -> str:
    """Get database schema information"""
    return """Database Schema v2.0:
    - Table: audio_files
    - Primary Key: id (INTEGER)
    - Core Fields: author, title, episode_chapter, recording_date, description, content_type, channel, genre, series_length, year
    - Embedded Metadata: album, track_number, publisher, language
    - Audio Properties: duration_seconds, bitrate_kbps, sample_rate_hz, audio_channels
    - File Properties: file_path, file_name, file_size_bytes, audio_format
    - Tracking: metadata_source, created_at
    
    For full schema details, see archivedb.md
    """

@mcp.tool()
def search_glossary(search_term: str) -> str:
    """Search the business glossary for terms matching the search query.
    
    This helps translate business language into database queries by finding
    relevant business terms, their definitions, database mappings, and usage examples.
    
    Args:
        search_term: The term or keyword to search for (case-insensitive, partial matches supported)
    
    Returns:
        Formatted information about matching terms including:
        - Business term name
        - Definition
        - Database column mapping
        - Data type
        - Usage examples with SQL
        - Valid values (if applicable)
        - Synonyms and related terms
    """
    logger.info("=" * 80)
    logger.info("TOOL CALLED: search_glossary")
    logger.info(f"INPUT search_term: {search_term}")
    
    search_lower = search_term.lower()
    matches = []
    
    # Search through glossary entries
    for term, details in BUSINESS_GLOSSARY.items():
        # Check if search term matches the term name, definition, or synonyms
        if (search_lower in term.lower() or
            search_lower in details["definition"].lower() or
            any(search_lower in syn.lower() for syn in details.get("synonyms", []))):
            matches.append((term, details))
    
    if not matches:
        result = f"No glossary entries found matching '{search_term}'.\n\nAvailable terms: {', '.join(BUSINESS_GLOSSARY.keys())}"
        logger.info(f"OUTPUT: No matches found")
        return result
    
    # Format the results
    output_lines = [f"Found {len(matches)} matching term(s) for '{search_term}':\n"]
    
    for term, details in matches:
        output_lines.append(f"\n{'='*60}")
        output_lines.append(f"TERM: {term}")
        output_lines.append(f"{'='*60}")
        output_lines.append(f"Definition: {details['definition']}")
        
        if "db_column" in details:
            output_lines.append(f"Database Column: {details['db_column']}")
        if "data_type" in details:
            output_lines.append(f"Data Type: {details['data_type']}")
        
        if "valid_values" in details:
            output_lines.append(f"Valid Values: {', '.join(details['valid_values'])}")
        
        if "synonyms" in details:
            output_lines.append(f"Synonyms: {', '.join(details['synonyms'])}")
        
        if "related_terms" in details:
            output_lines.append(f"Related Terms: {', '.join(details['related_terms'])}")
        
        output_lines.append("\nUsage Examples:")
        for i, example in enumerate(details.get("usage_examples", []), 1):
            output_lines.append(f"  {i}. {example}")
    
    result = "\n".join(output_lines)
    logger.info(f"OUTPUT: Found {len(matches)} matches")
    logger.info(f"Matching terms: {[term for term, _ in matches]}")
    
    return result

@mcp.tool()
def get_business_rules(rule_id: str = "all") -> str:
    """Get business rules that govern data quality and integrity in the DuPrez Audio Archive.
    
    Business rules define important constraints and requirements that help maintain
    archive quality, identify data issues, and guide collection management decisions.
    
    Args:
        rule_id: The ID of the specific business rule to retrieve, or "all" for all rules (default: "all")
    
    Returns:
        Detailed explanation of business rule(s) including purpose, logic, and how to check compliance
    """
    logger.info("=" * 80)
    logger.info("TOOL CALLED: get_business_rules")
    logger.info(f"INPUT rule_id: {rule_id}")
    
    # Business rules dictionary
    rules = {
        "series_quorum": {
            "name": "Series Quorum Rule",
            "description": "For an archive series to be considered quorum and complete valid, it must contain all episodes as specified in the series_length field.",
            "purpose": "Ensures the archive has complete series rather than partial collections, which is important for content completeness and user satisfaction.",
            "applies_to": "All records where series_length IS NOT NULL AND series_length > 0",
            "validation_criteria": [
                "Group records by series (using title, author, and year as series identifier)",
                "Count the number of episodes in the archive for each series",
                "Compare actual episode count against the series_length value",
                "Series is COMPLETE if: COUNT(*) >= series_length",
                "Series is INCOMPLETE if: COUNT(*) < series_length"
            ],
            "how_to_check": """To identify incomplete series, use this query:

SELECT 
    title,
    COALESCE(author, 'N/A') as author,
    year,
    series_length as expected_episodes,
    COUNT(*) as actual_episodes,
    series_length - COUNT(*) as missing_episodes
FROM audio_files
WHERE series_length IS NOT NULL AND series_length > 0
GROUP BY title, author, year, series_length
HAVING COUNT(*) < series_length
ORDER BY missing_episodes DESC;""",
            "example": "If 'The Archers' has series_length=5 but only 3 episodes exist in the archive, it violates this rule with 2 missing episodes.",
            "remediation": [
                "Identify source for missing episodes",
                "Check if episodes were never broadcast/recorded",
                "Update series_length if the value is incorrect",
                "Flag for acquisition if episodes should be obtained"
            ]
        },
        "future_rules": {
            "name": "Placeholder for Future Business Rules",
            "description": "Additional business rules can be added here as needed, such as: date validation, duplicate detection, metadata completeness, etc.",
            "purpose": "This structure allows for expandable business rule documentation"
        }
    }
    
    # Return requested rule(s)
    if rule_id.lower() == "all":
        output_lines = [f"DuPrez Audio Archive Business Rules ({len([r for r in rules.keys() if r != 'future_rules'])} active rules):\n"]
        
        for rid, rule in rules.items():
            if rid == "future_rules":
                continue
                
            output_lines.append(f"\n{'='*70}")
            output_lines.append(f"RULE ID: {rid}")
            output_lines.append(f"NAME: {rule['name']}")
            output_lines.append(f"{'='*70}")
            output_lines.append(f"\nDescription:\n{rule['description']}")
            output_lines.append(f"\nPurpose:\n{rule['purpose']}")
            
            if 'applies_to' in rule:
                output_lines.append(f"\nApplies To:\n{rule['applies_to']}")
            
            if 'validation_criteria' in rule:
                output_lines.append("\nValidation Criteria:")
                for i, criterion in enumerate(rule['validation_criteria'], 1):
                    output_lines.append(f"  {i}. {criterion}")
            
            if 'how_to_check' in rule:
                output_lines.append(f"\nHow to Check Compliance:\n{rule['how_to_check']}")
            
            if 'example' in rule:
                output_lines.append(f"\nExample:\n{rule['example']}")
            
            if 'remediation' in rule:
                output_lines.append("\nRemediation Steps:")
                for i, step in enumerate(rule['remediation'], 1):
                    output_lines.append(f"  {i}. {step}")
        
        result = "\n".join(output_lines)
        logger.info(f"OUTPUT: Returned all business rules")
        return result
        
    elif rule_id.lower() in rules:
        rule = rules[rule_id.lower()]
        output_lines = []
        output_lines.append(f"Business Rule: {rule['name']}")
        output_lines.append(f"ID: {rule_id}")
        output_lines.append(f"{'='*70}")
        output_lines.append(f"\nDescription:\n{rule['description']}")
        output_lines.append(f"\nPurpose:\n{rule['purpose']}")
        
        if 'applies_to' in rule:
            output_lines.append(f"\nApplies To:\n{rule['applies_to']}")
        
        if 'validation_criteria' in rule:
            output_lines.append("\nValidation Criteria:")
            for i, criterion in enumerate(rule['validation_criteria'], 1):
                output_lines.append(f"  {i}. {criterion}")
        
        if 'how_to_check' in rule:
            output_lines.append(f"\nHow to Check Compliance:\n{rule['how_to_check']}")
        
        if 'example' in rule:
            output_lines.append(f"\nExample:\n{rule['example']}")
        
        if 'remediation' in rule:
            output_lines.append("\nRemediation Steps:")
            for i, step in enumerate(rule['remediation'], 1):
                output_lines.append(f"  {i}. {step}")
        
        result = "\n".join(output_lines)
        logger.info(f"OUTPUT: Returned rule '{rule_id}'")
        return result
        
    else:
        available_rules = [rid for rid in rules.keys() if rid != "future_rules"]
        result = f"Unknown business rule ID: '{rule_id}'\n\nAvailable rule IDs: {', '.join(available_rules)}\n\nUse rule_id='all' to see all rules."
        logger.info(f"OUTPUT: Unknown rule ID '{rule_id}'")
        return result

@mcp.tool()
def run_SQLquery_duprez_archive(sql_query: str) -> str:
    """Execute a read-only SQL query against the Audio Archive database.
    
    Database: audio_files table (archivedb.db)
    
    Core Metadata Columns:
    - id (INTEGER): Unique identifier
    - author (VARCHAR): Author/creator (for audiobooks)
    - title (VARCHAR): Title of the programme or audiobook
    - episode_chapter (VARCHAR): Episode/chapter identifier (e.g., "01/10", "S01E05")
    - recording_date (DATE): Date recorded or broadcast (YYYY-MM-DD)
    - description (TEXT): Synopsis or description
    - content_type (VARCHAR): "radio_program", "audiobook", etc.
    - channel (VARCHAR): Broadcast channel (e.g., "BBC Radio 4", "BBC7")
    - genre (VARCHAR): Genre/category (e.g., "Drama", "Comedy", "Crime")
    - series_length (INTEGER): Total episodes in series
    - year (INTEGER): Recording year
    
    Embedded Metadata (from audio tags):
    - album (VARCHAR): Album/series name
    - track_number (VARCHAR): Track number in format "N/Total"
    - publisher (VARCHAR): Publisher or label
    - language (VARCHAR): ISO language code
    
    Audio Properties:
    - duration_seconds (DECIMAL): Duration in seconds
    - bitrate_kbps (INTEGER): Bitrate in kbps
    - sample_rate_hz (INTEGER): Sample rate in Hz
    - audio_channels (INTEGER): 1=mono, 2=stereo
    
    File Properties:
    - file_size_bytes (BIGINT): File size in bytes
    - audio_format (VARCHAR): "MP3", "M4A", "MP4"
    
    Args:
        sql_query: A SELECT SQL query to execute against the database
    
    Returns:
        Query results formatted as a table string, or error message if query fails.
        If the Query fails to find any results based on Author or Title, offer to run a LIKE query instead.
    """
    logger.info("=" * 80)
    logger.info("TOOL CALLED: run_SQLquery_duprez_archive")
    logger.info(f"INPUT SQL Query: {sql_query}")
    
    try:
        # Get the database path relative to this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(script_dir, 'archivedb', 'archivedb.db')
        
        logger.info(f"Connecting to database: {db_path}")
        
        # Connect to the database in read-only mode
        conn = duckdb.connect(db_path, read_only=True)
        
        # Execute the query
        result = conn.execute(sql_query).fetchall()
        
        # Get column names
        columns = [desc[0] for desc in conn.description] if conn.description else []
        
        logger.info(f"Query executed successfully. Columns: {columns}")
        logger.info(f"Rows returned: {len(result)}")
        logger.info(f"First 3 rows (if available): {result[:3]}")
        
        conn.close()
        
        # Format results as a table
        if result:
            table_output = tabulate(result, headers=columns, tablefmt="grid")
            output = f"Query executed successfully. {len(result)} rows returned.\n\n{table_output}"
            logger.info(f"OUTPUT (length: {len(output)} chars):\n{output[:500]}...")  # Log first 500 chars
            return output
        else:
            output = "Query executed successfully. No rows returned."
            logger.info(f"OUTPUT: {output}")
            return output
            
    except Exception as e:
        error_msg = f"Error executing query: {str(e)}"
        logger.error(f"SQL EXECUTION ERROR: {error_msg}")
        logger.error(f"Failed query was: {sql_query}")
        return error_msg


# Optional: Add a custom ping handler for health checks
@mcp.tool()
def archive_health_check() -> dict:
    """Check if the server and database are healthy by querying the record count."""
    logger.info("=" * 80)
    logger.info("TOOL CALLED: archive_health_check")
    
    try:
        # Get the database path relative to this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(script_dir, 'archivedb', 'archivedb.db')
        
        logger.info(f"Health check connecting to: {db_path}")
        
        # Connect to the database and query record count
        conn = duckdb.connect(db_path, read_only=True)
        result = conn.execute("SELECT COUNT(*) FROM audio_files").fetchone()
        record_count = result[0] if result else 0
        conn.close()
        
        response = {
            "status": "healthy",
            "service": "DuPrez Audio Archive",
            "database": "connected",
            "record_count": record_count
        }
        logger.info(f"Health check OUTPUT: {response}")
        return response
        
    except Exception as e:
        error_response = {
            "status": "unhealthy",
            "service": "DuPrez Audio Archive",
            "database": "error",
            "error": str(e) #NOTE: In production, avoid exposing raw error messages as the LLM may pass this on to the user etc 
        }
        logger.error(f"Health check FAILED: {error_response}")
        return error_response


# Run server with stdio transport for VS Code integration
if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("MCP Server starting...")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Console logging: {'disabled' if not CONSOLE_LOGGING else 'enabled'}")
    logger.info("=" * 80)
    mcp.run(transport="stdio")
