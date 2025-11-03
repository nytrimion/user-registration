#!/usr/bin/env python3
"""
Database Migration Script

This script applies Yoyo migrations using environment variables for database
connection, ensuring consistency with docker-compose.yml configuration.

Usage:
    # Apply all pending migrations
    python scripts/migrate.py

    # Rollback last migration
    python scripts/migrate.py --rollback

    # List migration status
    python scripts/migrate.py --list

Environment Variables (same as docker-compose.yml):
    - DATABASE_HOST (default: postgres)
    - DATABASE_PORT (default: 5432)
    - DATABASE_NAME (default: user_registration)
    - DATABASE_USER (default: postgres)
    - DATABASE_PASSWORD (default: postgres)

Examples:
    # Inside Docker container
    docker-compose exec api python scripts/migrate.py

    # In CI/CD (GitHub Actions)
    python scripts/migrate.py  # Uses injected environment variables
"""

import os
import subprocess
import sys


def get_database_uri() -> str:
    """
    Build PostgreSQL connection URI from environment variables.

    Uses the same environment variable names and defaults as docker-compose.yml
    to ensure consistency across all environments (development, CI, production).

    Returns:
        PostgreSQL connection URI string
    """
    host = os.getenv("DATABASE_HOST", "postgres")
    port = os.getenv("DATABASE_PORT", "5432")
    database = os.getenv("DATABASE_NAME", "user_registration")
    user = os.getenv("DATABASE_USER", "postgres")
    password = os.getenv("DATABASE_PASSWORD", "postgres")

    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


def run_yoyo_command(command: str, database_uri: str) -> int:
    """
    Execute Yoyo migrations command.

    Args:
        command: Yoyo command to execute (apply, rollback, list, etc.)
        database_uri: PostgreSQL connection URI

    Returns:
        Exit code from yoyo command (0 = success, non-zero = error)
    """
    # Use python -m yoyo instead of yoyo command (Poetry installs as module)
    # --batch flag: non-interactive mode (auto-confirm migrations in CI/Docker)
    yoyo_cmd = ["python", "-m", "yoyo", command, "--batch", "--database", database_uri, "migrations"]

    print(f"Running: yoyo {command}")
    print(f"Database: {database_uri.replace(os.getenv('DATABASE_PASSWORD', 'postgres'), '***')}")
    print("-" * 60)

    result = subprocess.run(yoyo_cmd)
    return result.returncode


def main() -> int:
    """
    Main entry point for migration script.

    Parses command-line arguments and executes the appropriate Yoyo command.

    Returns:
        Exit code (0 = success, 1 = error)
    """
    # Parse simple command-line arguments
    command = "apply"  # Default: apply pending migrations

    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ["--rollback", "-r"]:
            command = "rollback"
        elif arg in ["--list", "-l"]:
            command = "list"
        elif arg in ["--help", "-h"]:
            print(__doc__)
            return 0
        else:
            print(f"Unknown argument: {arg}")
            print("Use --help for usage information")
            return 1

    # Build database URI from environment variables
    database_uri = get_database_uri()

    # Execute Yoyo command
    exit_code = run_yoyo_command(command, database_uri)

    if exit_code == 0:
        print("-" * 60)
        print(f"✓ Migration {command} completed successfully")
    else:
        print("-" * 60)
        print(f"✗ Migration {command} failed with exit code {exit_code}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())