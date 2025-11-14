#!/usr/bin/env python
"""Tests for common/db.py"""

from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.db import build_connection_string, setup_db


class TestBuildConnectionString:
    """Test suite for build_connection_string function"""

    def test_build_connection_string_simple_host(self, monkeypatch):
        """Test building connection string with simple host"""
        monkeypatch.setenv("PGPASSWORD", "testpass")

        result = build_connection_string("user", "localhost/mydb")
        assert result == "postgresql://user:testpass@localhost/mydb"  # noqa: F402 # pragma: allowlist secret

    def test_build_connection_string_with_port(self, monkeypatch):
        """Test building connection string with host and port"""
        monkeypatch.setenv("PGPASSWORD", "secret123")

        result = build_connection_string("admin", "db.example.com:5432/production")
        assert result == "postgresql://admin:secret123@db.example.com:5432/production"  # noqa: F402 # pragma: allowlist secret

    def test_build_connection_string_neon_host(self, monkeypatch):
        """Test building connection string with Neon host (starts with ep-)"""
        monkeypatch.setenv("PGPASSWORD", "neonpass")

        result = build_connection_string(
            "myuser", "ep-cool-name-123456.us-east-2.aws.neon.tech/dbname"
        )
        assert (
            result
            == "postgresql://myuser:neonpass@ep-cool-name-123456.us-east-2.aws.neon.tech/dbname"  # noqa: F402 # pragma: allowlist secret
        )

    def test_build_connection_string_with_query_params(self, monkeypatch):
        """Test building connection string with query parameters"""
        monkeypatch.setenv("PGPASSWORD", "mypass")

        result = build_connection_string(
            "user", "host.com/db?sslmode=require&connect_timeout=10"
        )
        assert (
            result
            == "postgresql://user:mypass@host.com/db?sslmode=require&connect_timeout=10"  # noqa: F402 # pragma: allowlist secret
        )

    def test_build_connection_string_no_password(self, monkeypatch):
        """Test building connection string when PGPASSWORD is not set"""
        monkeypatch.delenv("PGPASSWORD", raising=False)

        result = build_connection_string("user", "localhost/db")
        # When PGPASSWORD is missing, get_env_variable returns None
        assert result == "postgresql://user:None@localhost/db"  # noqa: F402 # pragma: allowlist secret


class TestSetupDb:
    """Test suite for setup_db function"""

    @patch("common.db.create_engine")
    @patch("common.db.SQLModel")
    def test_setup_db_postgresql(self, mock_sqlmodel, mock_create_engine):
        """Test setup_db with PostgreSQL connection string"""
        # Mock the engine and connection
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=None)
        mock_create_engine.return_value = mock_engine

        # Call setup_db
        setup_db("postgresql://user:pass@localhost/db")  # noqa: F402 # pragma: allowlist secret

        # Verify engine was created
        mock_create_engine.assert_called_once_with(
            "postgresql://user:pass@localhost/db",  # noqa: F402 # pragma: allowlist secret
            echo=True,
        )

        # Verify vector extension was created
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args[0][0]
        assert "CREATE EXTENSION IF NOT EXISTS vector" in str(call_args)

        # Verify commit was called
        mock_conn.commit.assert_called_once()

        # Verify tables were created
        mock_sqlmodel.metadata.create_all.assert_called_once_with(mock_engine)

    @patch("common.db.create_engine")
    @patch("common.db.SQLModel")
    def test_setup_db_duckdb(self, mock_sqlmodel, mock_create_engine):
        """Test setup_db with DuckDB connection string"""
        # Mock the engine
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        # Call setup_db
        setup_db("duckdb:///path/to/db.duckdb")

        # Verify engine was created
        mock_create_engine.assert_called_once_with(
            "duckdb:///path/to/db.duckdb", echo=True
        )

        # Verify vector extension was NOT created (only for PostgreSQL)
        mock_engine.connect.assert_not_called()

        # Verify tables were created
        mock_sqlmodel.metadata.create_all.assert_called_once_with(mock_engine)

    @patch("common.db.create_engine")
    @patch("common.db.SQLModel")
    def test_setup_db_idempotent(self, mock_sqlmodel, mock_create_engine):
        """Test that setup_db can be called multiple times safely"""
        # Mock the engine and connection
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=None)
        mock_create_engine.return_value = mock_engine

        connection_string = "postgresql://user:pass@localhost/db"  # noqa: F402 # pragma: allowlist secret

        # Call setup_db twice
        setup_db(connection_string)
        setup_db(connection_string)

        # Verify it was called twice (idempotent)
        assert mock_create_engine.call_count == 2
        assert mock_conn.execute.call_count == 2
        assert mock_sqlmodel.metadata.create_all.call_count == 2

    @patch("common.db.create_engine")
    @patch("common.db.SQLModel")
    def test_setup_db_with_echo_enabled(self, mock_sqlmodel, mock_create_engine):
        """Test that setup_db enables echo for SQL logging"""
        # Mock the engine
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        # Call setup_db
        setup_db("duckdb:///test.db")

        # Verify echo=True was passed to create_engine
        mock_create_engine.assert_called_once()
        call_kwargs = mock_create_engine.call_args[1]
        assert call_kwargs.get("echo") is True
