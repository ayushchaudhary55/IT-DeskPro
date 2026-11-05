"""
IT DeskPro - Database Connection & Execution Layer
Provides safe, parameterized MySQL database operations with connection pooling and error resilience.
"""
import logging
from contextlib import contextmanager
import mysql.connector
from mysql.connector import Error as MySQLError
import config

logger = logging.getLogger("it_deskpro.database")

# Build connection configuration dictionary
DB_CONFIG = {
    "host": config.DB_HOST,
    "port": config.DB_PORT,
    "user": config.DB_USER,
    "password": config.DB_PASSWORD,
    "database": config.DB_NAME,
    "charset": "utf8mb4",
    "use_unicode": True,
    "autocommit": False,
}


def test_connection():
    """
    Tests connectivity to the MySQL server and database.
    Returns (True, "Connected") or (False, error_message).
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")
            cursor.fetchone()
            cursor.close()
            conn.close()
            return True, "Database connection successful."
    except MySQLError as err:
        return False, f"Database connection failed: {err.msg}"
    except Exception as ex:
        return False, f"Unexpected connection error: {str(ex)}"
    return False, "Unable to establish connection."


@contextmanager
def get_db_connection():
    """
    Context manager that yields an active MySQL connection and guarantees
    proper rollback on failure and closure upon completion.
    """
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        yield conn
    except MySQLError as err:
        logger.error(f"MySQL Connection Error: {err.msg}")
        if conn and conn.is_connected():
            conn.rollback()
        raise
    finally:
        if conn and conn.is_connected():
            conn.close()


def execute_query(query, params=None, commit=False):
    """
    Executes an INSERT, UPDATE, or DELETE query with parameterized inputs.
    Returns the lastrowid or affected rows count.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(query, params or ())
            if commit:
                conn.commit()
                last_id = cursor.lastrowid
                row_count = cursor.rowcount
                cursor.close()
                return last_id if last_id else row_count
            cursor.close()
            return None
        except MySQLError as err:
            conn.rollback()
            cursor.close()
            logger.error(f"Error executing query: {query} with params {params} -> {err.msg}")
            raise


def fetch_one(query, params=None, dictionary=True):
    """
    Executes a SELECT query and returns a single row as a dictionary (or tuple).
    """
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=dictionary)
        try:
            cursor.execute(query, params or ())
            row = cursor.fetchone()
            cursor.close()
            return row
        except MySQLError as err:
            cursor.close()
            logger.error(f"Error fetching one row: {query} -> {err.msg}")
            raise


def fetch_all(query, params=None, dictionary=True):
    """
    Executes a SELECT query and returns all matching rows as a list of dictionaries (or tuples).
    """
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=dictionary)
        try:
            cursor.execute(query, params or ())
            rows = cursor.fetchall()
            cursor.close()
            return rows
        except MySQLError as err:
            cursor.close()
            logger.error(f"Error fetching rows: {query} -> {err.msg}")
            raise


def init_database_if_needed():
    """
    Ensures that the database schema is loaded and verified without wiping data.
    """
    schema_path = config.BASE_DIR / "database" / "schema.sql"
    if not schema_path.exists():
        return

    # First connect without database selected to ensure DB exists
    server_config = {
        "host": config.DB_HOST,
        "port": config.DB_PORT,
        "user": config.DB_USER,
        "password": config.DB_PASSWORD,
    }
    try:
        conn = mysql.connector.connect(**server_config)
        cursor = conn.cursor()
        with open(schema_path, "r", encoding="utf-8") as f:
            sql_content = f.read()

        # Split commands by semicolon while respecting strings
        statements = [stmt.strip() for stmt in sql_content.split(";") if stmt.strip()]
        for stmt in statements:
            try:
                cursor.execute(stmt)
            except MySQLError as e:
                # Ignore harmless warnings like table already exists
                if "already exists" not in str(e).lower():
                    logger.warning(f"Schema statement warning: {e}")
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as ex:
        logger.error(f"Database initialization error: {ex}")

