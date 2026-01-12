import duckdb
import os
from contextlib import contextmanager

DB_PATH = "stabletrace.duckdb"
SCHEMA_PATH = "warehouse/schema.sql"

def get_db_connection(read_only=False):
    """
    Returns a DuckDB connection.
    In the real world, you might want a connection pool or careful management 
    of the single file lock if writing.
    """
    conn = duckdb.connect(DB_PATH, read_only=read_only)
    return conn

def init_db():
    """
    Idempotent initialization of the database schema.
    """
    print(f"Initializing database at {DB_PATH}...")
    conn = get_db_connection()
    
    # Read schema file
    if not os.path.exists(SCHEMA_PATH):
        # Fallback if running from a different cwd or tests
        # This is a bit hacky, but robust for a script-first MVP
        possible_paths = [
            "warehouse/schema.sql",
            "../warehouse/schema.sql",
            "../../warehouse/schema.sql"
        ]
        schema_sql = None
        for p in possible_paths:
            if os.path.exists(p):
                with open(p, "r") as f:
                    schema_sql = f.read()
                break
        
        if not schema_sql:
            raise FileNotFoundError(f"Could not find schema.sql in {possible_paths}")
    else:
        with open(SCHEMA_PATH, "r") as f:
            schema_sql = f.read()

    # Execute schema
    queries = schema_sql.split(";")
    for q in queries:
        if q.strip():
            conn.execute(q)
    
    conn.close()
    print("Database initialized.")

if __name__ == "__main__":
    init_db()
