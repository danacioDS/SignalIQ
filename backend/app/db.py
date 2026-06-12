"""Database connection pool and query helpers for SignalIQ.

Uses ``psycopg2.pool.ThreadedConnectionPool`` with automatic retries.
Initialise once at startup via ``init_pool()``, then call ``execute_query()``
or manage connections directly via ``get_connection()`` / ``put_connection()``.
"""

import os
import time
import psycopg2
import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool


_pool: ThreadedConnectionPool | None = None
_MIN_CONN = 1
_MAX_CONN = 10
_RETRIES = 3
_RETRY_DELAY = 0.5


def _parse_db_url() -> str:
    """Resolve and sanitise ``DATABASE_URL`` from the environment."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    db_url = db_url.strip()
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    return db_url


def init_pool(minconn: int = _MIN_CONN, maxconn: int = _MAX_CONN) -> None:
    """Initialise the global connection pool.

    Call once at application startup, **after** the environment is loaded.
    Safe to call multiple times (replaces any existing pool).
    """
    global _pool
    close_pool()
    db_url = _parse_db_url()
    _pool = ThreadedConnectionPool(
        minconn,
        maxconn,
        db_url,
        sslmode="require",
    )


def close_pool() -> None:
    """Close all connections in the pool, if initialised."""
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None


def get_connection() -> psycopg2.extensions.connection:
    """Get a connection from the pool with retries.

    Raises ``RuntimeError`` if the pool is not initialised or all retries
    are exhausted.
    """
    if _pool is None:
        raise RuntimeError("Database pool not initialised — call init_pool() first")

    last_error = None
    for attempt in range(_RETRIES):
        try:
            return _pool.getconn()
        except Exception as exc:
            last_error = exc
            if attempt < _RETRIES - 1:
                time.sleep(_RETRY_DELAY * (2 ** attempt))
    raise RuntimeError(f"Failed to get database connection after {_RETRIES} retries: {last_error}")


def put_connection(conn: psycopg2.extensions.connection | None) -> None:
    """Return a connection to the pool.

    Safe to call with ``None``.
    """
    if conn is not None and _pool is not None:
        _pool.putconn(conn)


def execute_query(
    query: str,
    params: tuple | None = None,
    cursor_factory=None,
    retries: int = _RETRIES,
) -> list[dict] | list[tuple]:
    """Execute *query* and return all rows.

    Parameters
    ----------
    query : str
        SQL statement.
    params : tuple or None
        Parameters for the query.
    cursor_factory : psycopg2.extensions.cursor factory or None
        Use ``psycopg2.extras.RealDictCursor`` for dict rows.
    retries : int
        Number of retry attempts.

    Returns
    -------
    list
        Rows as tuples or dicts depending on *cursor_factory*.
    """
    conn = None
    last_error = None
    for attempt in range(retries):
        try:
            conn = get_connection()
            cur = conn.cursor(cursor_factory=cursor_factory)
            cur.execute(query, params)
            rows = cur.fetchall()
            cur.close()
            return rows
        except Exception as exc:
            last_error = exc
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            if attempt < retries - 1:
                time.sleep(_RETRY_DELAY * (2 ** attempt))
        finally:
            if conn:
                put_connection(conn)
    raise RuntimeError(f"Query failed after {retries} retries: {last_error}")


def execute_query_one(
    query: str,
    params: tuple | None = None,
    cursor_factory=None,
    retries: int = _RETRIES,
):
    """Execute *query* and return the first row (or ``None``)."""
    rows = execute_query(query, params, cursor_factory, retries)
    return rows[0] if rows else None
