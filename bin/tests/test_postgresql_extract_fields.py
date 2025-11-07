"""Tests for postgresql_extract_fields.py script."""

from unittest.mock import MagicMock, mock_open, patch


# Mock psycopg2 before importing the module
import sys

sys.modules["psycopg2"] = MagicMock()

from postgresql_extract_fields import extract_fields  # noqa: E402


class TestExtractFields:
    """Test extract_fields function."""

    @patch("postgresql_extract_fields.psycopg2.connect")
    @patch("builtins.open", new_callable=mock_open)
    def test_executes_select_query(self, mock_file, mock_connect):
        """Test that SELECT query is executed."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchall.return_value = [("Title 1", "URL 1"), ("Title 2", "URL 2")]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        extract_fields(
            "postgresql://user:pass@localhost/db",  # pragma: allowlist secret
            "articles",
            "title, url",
            "output.tsv",
        )

        # Check that SELECT was executed
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args[0][0]
        assert "SELECT title, url FROM articles" in call_args

    @patch("postgresql_extract_fields.psycopg2.connect")
    @patch("builtins.open", new_callable=mock_open)
    def test_includes_where_clause(self, mock_file, mock_connect):
        """Test that WHERE clause is included when provided."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        extract_fields(
            "postgresql://user:pass@localhost/db",  # pragma: allowlist secret
            "articles",
            "title, url",
            "output.tsv",
            where_clause="date > '2025-01-01'",
        )

        # Check that WHERE clause is in query
        call_args = mock_cursor.execute.call_args[0][0]
        assert "WHERE date > '2025-01-01'" in call_args

    @patch("postgresql_extract_fields.psycopg2.connect")
    @patch("builtins.open", new_callable=mock_open)
    def test_writes_header_row(self, mock_file, mock_connect):
        """Test that header row is written to TSV."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        extract_fields(
            "postgresql://user:pass@localhost/db",  # pragma: allowlist secret
            "articles",
            "title, url, doi",
            "output.tsv",
        )

        # Check that header was written
        handle = mock_file()
        written_content = "".join(call[0][0] for call in handle.write.call_args_list)
        assert "title\turl\tdoi\n" in written_content

    @patch("postgresql_extract_fields.psycopg2.connect")
    @patch("builtins.open", new_callable=mock_open)
    def test_writes_data_rows(self, mock_file, mock_connect):
        """Test that data rows are written to TSV."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchall.return_value = [
            ("Title 1", "https://example.com/1"),
            ("Title 2", "https://example.com/2"),
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        extract_fields(
            "postgresql://user:pass@localhost/db",  # pragma: allowlist secret
            "articles",
            "title, url",
            "output.tsv",
        )

        # Check that data rows were written
        handle = mock_file()
        written_content = "".join(call[0][0] for call in handle.write.call_args_list)
        assert "Title 1\thttps://example.com/1\n" in written_content
        assert "Title 2\thttps://example.com/2\n" in written_content

    @patch("postgresql_extract_fields.psycopg2.connect")
    @patch("builtins.open", new_callable=mock_open)
    def test_uses_custom_separator(self, mock_file, mock_connect):
        """Test that custom separator is used."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchall.return_value = [("Title", "URL")]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        extract_fields(
            "postgresql://user:pass@localhost/db",  # pragma: allowlist secret
            "articles",
            "title, url",
            "output.csv",
            sep=",",
        )

        # Check that comma separator was used
        handle = mock_file()
        written_content = "".join(call[0][0] for call in handle.write.call_args_list)
        assert "title,url\n" in written_content
        assert "Title,URL\n" in written_content

    @patch("postgresql_extract_fields.psycopg2.connect")
    @patch("builtins.open", new_callable=mock_open)
    def test_handles_connection_string(self, mock_file, mock_connect):
        """Test that connection string is used correctly."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        connection_string = (
            "postgresql://user:pass@localhost:5432/test_db"  # pragma: allowlist secret
        )
        extract_fields(connection_string, "articles", "title", "output.tsv")

        # Check that connect was called with the connection string
        mock_connect.assert_called_once_with(connection_string)
