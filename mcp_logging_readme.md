# MCP Server Logging

## Overview

The MCP server includes comprehensive logging to track all tool calls, SQL queries, and responses. This makes it easy to debug and monitor what the Azure OpenAI model is sending to your MCP tools and what data is being returned.

## Log Configuration

### Log Locations
- **File**: `logs/mcp_server_YYYYMMDD_HHMMSS.log` (timestamped for each server instance)
- **Terminal**: Also outputs to stderr (visible in your terminal while running)

### Log Format
```
YYYY-MM-DD HH:MM:SS - module_name - LEVEL - message
```

## What Gets Logged

### Tool Calls
Every tool invocation logs:
- Tool name being called
- Input parameters (including SQL queries)
- Database connection details
- Query execution results
- Output data (with sampling for large results)
- Any errors with full context

### Specific Tool Logging

#### `run_SQLquery_duprez_archive`
Logs:
- SQL query received from the LLM
- Database path being accessed
- Column names returned
- Number of rows in result set
- First 3 rows of data (for debugging)
- First 500 characters of formatted output
- Any SQL execution errors

#### `archive_health_check`
Logs:
- Database connection status
- Record count from health check query
- Success/failure status
- Error details if health check fails

## Viewing Logs

### Watch logs in real-time
```bash
tail -f logs/mcp_server_*.log
```

### View the most recent log file
```bash
ls -t logs/ | head -1 | xargs -I {} cat logs/{}
```

### Search for specific queries
```bash
grep "INPUT SQL Query" logs/mcp_server_*.log
```

### Find errors
```bash
grep "ERROR" logs/mcp_server_*.log
```

### View only tool calls
```bash
grep "TOOL CALLED" logs/mcp_server_*.log
```

## Log Levels

- **INFO**: Normal operations, tool calls, query execution
- **ERROR**: Failures, exceptions, database connection issues

## Log Retention

Logs are stored with timestamps and are not automatically deleted. You may want to periodically clean up old log files:

```bash
# Remove logs older than 7 days
find logs/ -name "mcp_server_*.log" -mtime +7 -delete
```

## Privacy & Security Notes

⚠️ **Important**: Log files contain:
- All SQL queries executed
- Sample data from query results
- Database paths
- Error messages with technical details

**Recommendations**:
- Keep log files secure and restrict access
- Do not commit log files to version control (add `logs/` to `.gitignore`)
- Review logs before sharing for debugging
- In production environments, consider sanitizing sensitive data from logs
- The current code includes a note about avoiding raw error exposure to LLMs in production

## Troubleshooting with Logs

### Common Issues to Look For

1. **SQL Syntax Errors**
   - Search for "SQL EXECUTION ERROR"
   - Review the "Failed query was" line to see the exact SQL

2. **Database Connection Issues**
   - Look for "Health check FAILED"
   - Check database path in connection logs

3. **Empty Results**
   - Check "Rows returned: 0" entries
   - Review the SQL query to ensure it's correct

4. **Tool Not Being Called**
   - If you don't see "TOOL CALLED" entries, the LLM may not be using your tools
   - Review tool descriptions to ensure they're clear

## Example Log Output

```
2025-10-29 14:23:45 - __main__ - INFO - ================================================================================
2025-10-29 14:23:45 - __main__ - INFO - TOOL CALLED: run_SQLquery_duprez_archive
2025-10-29 14:23:45 - __main__ - INFO - INPUT SQL Query: SELECT title, broadcast_date FROM audio_files LIMIT 5
2025-10-29 14:23:45 - __main__ - INFO - Connecting to database: /home/angusf/_source/MCPLocal/DuPrezDB/archive.db
2025-10-29 14:23:45 - __main__ - INFO - Query executed successfully. Columns: ['title', 'broadcast_date']
2025-10-29 14:23:45 - __main__ - INFO - Rows returned: 5
2025-10-29 14:23:45 - __main__ - INFO - First 3 rows (if available): [('Programme A', '2020-01-15'), ('Programme B', '2020-02-20'), ('Programme C', '2020-03-10')]
2025-10-29 14:23:45 - __main__ - INFO - OUTPUT (length: 245 chars):
Query executed successfully. 5 rows returned.

+--------------+----------------+
| title        | broadcast_date |
+--------------+----------------+
| Programme A  | 2020-01-15     |
...
```
