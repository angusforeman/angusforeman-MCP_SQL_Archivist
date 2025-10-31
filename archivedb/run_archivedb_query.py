#!/usr/bin/env python3
import duckdb
import os
import sys
from tabulate import tabulate

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, 'archivedb.db')

def run_query(db_path, query):
    """Execute SQL query and display results"""
    try:
        conn = duckdb.connect(db_path, read_only=False)
        result = conn.execute(query).fetchall()
        columns = [desc[0] for desc in conn.description]
        conn.close()
        
        if result:
            print(tabulate(result, headers=columns, tablefmt='grid'))
            print(f"\n{len(result)} rows returned")
        else:
            print("No results found")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Using database: {DB_PATH}\n")
        print("Usage: python3 run_query.py 'SQL QUERY'")
        print("\nExample:")
        print("  python3 run_query.py 'SELECT * FROM audio_files LIMIT 5'")
        sys.exit(1)
    
    query = sys.argv[1]
    print(f"Using database: {DB_PATH}\n")
    run_query(DB_PATH, query)
