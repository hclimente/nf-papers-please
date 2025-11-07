"""Tests for postgresql_update_field.py script."""

from unittest.mock import MagicMock, patch


# Mock psycopg2 before importing the module
import sys

sys.modules["psycopg2"] = MagicMock()

from postgresql_update_field import update_postgresql_field  # noqa: E402


class TestUpdatePostgresqlField:
    """Test update_postgresql_field function."""

    @patch("postgresql_update_field.psycopg2.connect")
    def test_executes_update_query(self, mock_connect):
        """Test that UPDATE query is executed."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        update_postgresql_field(
            "postgresql://user:pass@localhost/db",  # pragma: allowlist secret
            "articles",
            "title = 'New Title'",
            "id = 1",
        )

        # Check that UPDATE was executed
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args[0][0]
        assert "UPDATE articles" in call_args
        assert "SET title = 'New Title'" in call_args
        assert "WHERE id = 1" in call_args

    @patch("postgresql_update_field.psycopg2.connect")
    def test_commits_transaction(self, mock_connect):
        """Test that transaction is committed."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        update_postgresql_field(
            "postgresql://user:pass@localhost/db",  # pragma: allowlist secret
            "articles",
            "tags = ARRAY['tag1']",
            "doi = '10.1234/test'",
        )

        # Check that commit was called
        mock_conn.commit.assert_called_once()

    @patch("postgresql_update_field.psycopg2.connect")
    def test_handles_connection_string(self, mock_connect):
        """Test that connection string is used correctly."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        connection_string = (
            "postgresql://user:pass@localhost:5432/test_db"  # pragma: allowlist secret
        )
        update_postgresql_field(
            connection_string,
            "sources",
            "last_checked = '2025-11-07'",
            "name = 'Nature'",
        )

        # Check that connect was called with the connection string
        mock_connect.assert_called_once_with(connection_string)

    @patch("postgresql_update_field.psycopg2.connect")
    def test_uses_context_managers(self, mock_connect):
        """Test that context managers are used for connection and cursor."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        update_postgresql_field(
            "postgresql://user:pass@localhost/db",  # pragma: allowlist secret
            "articles",
            "reasoning = 'Updated reasoning'",
            "url = 'https://example.com'",
        )

        # Check that context managers were entered
        mock_conn.__enter__.assert_called_once()
        mock_cursor.__enter__.assert_called_once()
