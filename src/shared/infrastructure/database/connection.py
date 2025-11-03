"""
PostgreSQL connection pool management with dependency injection.

This module provides a connection factory abstraction for PostgreSQL using
psycopg2. The factory is injectable and testable, following Clean Architecture
principles.

Design Decisions:
    - Factory pattern: DatabaseConnectionFactory interface for DI
    - Context manager: Automatic connection cleanup (putconn on exit)
    - ThreadedConnectionPool: Thread-safe for FastAPI workers
    - Environment variables: Same configuration as docker-compose.yml

Architecture:
    - Interface: DatabaseConnectionFactory (can be mocked in tests)
    - Implementation: PostgresConnectionFactory (uses psycopg2.pool)
    - Injection: Repository receives DatabaseConnectionFactory via @inject

Usage Example:
    ```python
    # In repository
    class PostgresAccountRepository:
        def __init__(self, db: DatabaseConnectionFactory):
            self._db = db

        def create(self, account: Account) -> None:
            with self._db.connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("INSERT INTO account ...")
                    conn.commit()
    ```
"""

import os
from abc import ABC, abstractmethod
from collections.abc import Generator
from contextlib import contextmanager

from psycopg2 import pool
from psycopg2.extensions import connection as Connection  # noqa: N812


class DatabaseConnectionFactory(ABC):
    """
    Abstract factory for database connections.

    This interface allows repositories to remain independent of the concrete
    connection pool implementation. It can be mocked in unit tests or replaced
    with a different implementation (e.g., async connections, different DBMS).

    Dependency Injection:
        - Repositories receive this interface via constructor injection
        - Concrete implementation (PostgresConnectionFactory) bound in DI container
        - Unit tests can provide FakeDatabaseConnectionFactory
    """

    @abstractmethod
    @contextmanager
    def connection(self) -> Generator[Connection]:
        """
        Provide a database connection context manager.

        Yields:
            psycopg2 connection object

        Usage:
            ```python
            with factory.connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM account")
            # Connection automatically returned to pool
            ```

        Transaction Management:
            - Connections are NOT auto-committed
            - Call conn.commit() explicitly after modifications
            - Call conn.rollback() to abort transaction
        """
        pass


def _get_database_config() -> dict[str, str | int]:
    """
    Read database configuration from environment variables.

    Uses the same environment variable names and defaults as docker-compose.yml
    to ensure consistency across all environments (development, CI, production).

    Returns:
        Dictionary with database connection parameters

    Environment Variables:
        DATABASE_HOST: PostgreSQL host (default: postgres)
        DATABASE_PORT: PostgreSQL port (default: 5432)
        DATABASE_NAME: Database name (default: user_registration)
        DATABASE_USER: Database user (default: postgres)
        DATABASE_PASSWORD: Database password (default: postgres)
    """
    return {
        "host": os.getenv("DATABASE_HOST", "postgres"),
        "port": int(os.getenv("DATABASE_PORT", "5432")),
        "database": os.getenv("DATABASE_NAME", "user_registration"),
        "user": os.getenv("DATABASE_USER", "postgres"),
        "password": os.getenv("DATABASE_PASSWORD", "postgres"),
    }


class PostgresConnectionFactory(DatabaseConnectionFactory):
    """
    PostgreSQL connection factory using psycopg2 connection pool.

    Creates and manages a thread-safe connection pool for efficient database
    access. The pool is initialized once during factory construction and reused
    for all connection requests.

    Connection Pool Configuration:
        - minconn=2: Always keep 2 connections alive (reduces latency)
        - maxconn=10: Limit to 10 concurrent connections (prevents DB overload)
        - connect_timeout=10: Fail fast if database unreachable
        - statement_timeout=30s: Kill long-running queries

    Thread Safety:
        - ThreadedConnectionPool is thread-safe for multi-threaded applications
        - Safe to use with FastAPI workers (multiple threads/processes)

    Lifecycle:
        - Pool created during __init__ (lazy initialization in DI container)
        - Connections acquired via getconn() in connection() context manager
        - Connections returned via putconn() automatically (finally block)
        - Pool closed via close() method (application shutdown)
    """

    def __init__(self) -> None:
        """
        Initialize PostgreSQL connection pool.

        Reads configuration from environment variables and creates a
        ThreadedConnectionPool instance.

        Raises:
            psycopg2.OperationalError: If database connection fails
                (wrong credentials, host unreachable, etc.)
        """
        config = _get_database_config()

        self._pool: pool.ThreadedConnectionPool = pool.ThreadedConnectionPool(
            minconn=2,
            maxconn=10,
            host=config["host"],
            port=config["port"],
            database=config["database"],
            user=config["user"],
            password=config["password"],
            # Connection options for better reliability
            connect_timeout=10,  # Timeout after 10 seconds if DB unreachable
            options="-c statement_timeout=30000",  # Kill queries after 30 seconds
        )

    @contextmanager
    def connection(self) -> Generator[Connection]:
        """
        Provide a database connection from the pool.

        Acquires a connection from the pool and ensures it is returned even if
        an exception occurs. This prevents connection leaks.

        Yields:
            psycopg2 connection object

        Raises:
            psycopg2.OperationalError: If no connections available in pool
            psycopg2.DatabaseError: If database operation fails

        Example:
            ```python
            with factory.connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM account")
                    rows = cursor.fetchall()
                conn.commit()
            # Connection automatically returned to pool here
            ```

        Transaction Management:
            - Caller is responsible for commit()/rollback()
            - Connection is NOT committed automatically
            - Repository layer handles transaction boundaries
        """
        conn = self._pool.getconn()

        try:
            yield conn
        finally:
            # Always return connection to pool, even if exception occurred
            # This is critical to prevent connection leaks
            self._pool.putconn(conn)

    def close(self) -> None:
        """
        Close all connections in the pool and release resources.

        Should be called on application shutdown to gracefully close all
        database connections.

        Usage:
            ```python
            # In FastAPI shutdown event
            @app.on_event("shutdown")
            async def shutdown_event():
                connection_factory.close()
            ```
        """
        self._pool.closeall()
