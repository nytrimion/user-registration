"""
Integration tests for PostgresConnectionFactory.

These tests validate the connection pool behavior with a real PostgreSQL
database. They ensure proper connection acquisition, release, and cleanup.

Test Strategy:
    - Real PostgreSQL database (Docker service)
    - Test connection lifecycle (getconn, putconn, closeall)
    - Test context manager cleanup (even on exception)
    - Test connection reuse from pool
    - No mocking (full integration test)

Database:
    - Uses DATABASE_* environment variables (same as application)
    - Tests run against real PostgreSQL instance
    - Each test is independent (no shared state)
"""

import pytest

from src.shared.infrastructure.database.connection import (
    DatabaseConnectionFactory,
    PostgresConnectionFactory,
)


def test_postgres_connection_factory_can_acquire_connection() -> None:
    """
    PostgresConnectionFactory should successfully acquire a connection from pool.

    Validates:
        - Factory initializes without error
        - connection() context manager returns valid connection
        - Connection can execute simple query
        - Connection is returned to pool after use
    """
    # Arrange
    factory = PostgresConnectionFactory()

    # Act & Assert
    with factory.connection() as conn:
        # Connection should be valid psycopg2 connection
        assert conn is not None
        assert not conn.closed

        # Should be able to execute query
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 AS test_value")
            result = cursor.fetchone()
            assert result == (1,)

    # Connection should be returned to pool (can't verify directly, but no exception)
    factory.close()


def test_postgres_connection_factory_returns_connection_on_exception() -> None:
    """
    PostgresConnectionFactory should return connection to pool even if exception occurs.

    This test validates that the context manager's finally block correctly
    returns the connection to the pool, preventing connection leaks.

    Validates:
        - Exception propagates correctly
        - Connection still returned to pool (putconn called)
        - No connection leak (pool remains healthy)
    """
    # Arrange
    factory = PostgresConnectionFactory()

    # Act & Assert
    with pytest.raises(RuntimeError, match="Simulated error"):
        with factory.connection() as conn:
            assert not conn.closed

            # Simulate an error during repository operation
            raise RuntimeError("Simulated error")

    # Pool should still be healthy - acquire another connection to verify
    with factory.connection() as conn:
        assert conn is not None
        assert not conn.closed

    factory.close()


def test_postgres_connection_factory_reuses_connections() -> None:
    """
    PostgresConnectionFactory should reuse connections from pool.

    Validates:
        - Multiple connection() calls acquire from same pool
        - Connections are reused (not creating new connections each time)
        - Pool manages minconn/maxconn correctly
    """
    # Arrange
    factory = PostgresConnectionFactory()

    # Act: Acquire and release connection multiple times
    connection_ids = []

    for _ in range(3):
        with factory.connection() as conn:
            # Track connection object id (Python object identity)
            connection_ids.append(id(conn))

    # Assert: Some connections should be reused (same object id appears twice)
    # With minconn=2, we expect at most 2 unique connections for 3 requests
    unique_connections = len(set(connection_ids))
    assert (
        unique_connections <= 2
    ), f"Expected connection reuse (max 2 unique), got {unique_connections}"

    factory.close()


def test_postgres_connection_factory_connection_is_not_auto_committed() -> None:
    """
    PostgresConnectionFactory connections should NOT auto-commit transactions.

    This test validates that the repository layer must explicitly call commit()
    for changes to persist. This prevents accidental commits and gives
    repositories full control over transaction boundaries.

    Validates:
        - Changes are NOT committed automatically
        - Explicit commit() is required
        - Rollback works as expected
    """
    # Arrange
    factory = PostgresConnectionFactory()

    # Act: Insert without commit in first connection
    with factory.connection() as conn:
        with conn.cursor() as cursor:
            # Create temporary test table
            cursor.execute(
                """
                CREATE TEMP TABLE test_autocommit (
                    id INTEGER PRIMARY KEY,
                    value TEXT
                )
                """
            )
            conn.commit()  # Commit table creation

            # Insert without commit
            cursor.execute("INSERT INTO test_autocommit (id, value) VALUES (1, 'test')")
            # NO conn.commit() here - changes should not persist

    # Assert: Changes should NOT be visible in new connection (no auto-commit)
    with factory.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM test_autocommit WHERE id = 1")
            result = cursor.fetchone()
            # Should be None because previous insert was not committed
            assert result is None

    factory.close()


def test_postgres_connection_factory_explicit_commit_persists_changes() -> None:
    """
    PostgresConnectionFactory connections should persist changes after commit().

    Validates:
        - Explicit commit() makes changes permanent
        - Changes visible in subsequent connections
        - Transaction boundaries work correctly
    """
    # Arrange
    factory = PostgresConnectionFactory()

    # Act: Insert WITH commit
    with factory.connection() as conn:
        with conn.cursor() as cursor:
            # Create temporary test table
            cursor.execute(
                """
                CREATE TEMP TABLE test_commit (
                    id INTEGER PRIMARY KEY,
                    value TEXT
                ) ON COMMIT PRESERVE ROWS
                """
            )
            cursor.execute("INSERT INTO test_commit (id, value) VALUES (1, 'test')")
            conn.commit()  # Explicit commit

    # Assert: Changes should be visible in new connection
    with factory.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT value FROM test_commit WHERE id = 1")
            result = cursor.fetchone()
            assert result == ("test",)

    factory.close()


def test_postgres_connection_factory_implements_interface() -> None:
    """
    PostgresConnectionFactory should implement DatabaseConnectionFactory interface.

    Validates:
        - Factory is instance of DatabaseConnectionFactory
        - Can be used polymorphically (for DI)
    """
    # Arrange & Act
    factory = PostgresConnectionFactory()

    # Assert
    assert isinstance(factory, DatabaseConnectionFactory)

    # Should have connection() method
    assert hasattr(factory, "connection")
    assert callable(factory.connection)

    factory.close()
