"""Tests for postgresql_remove_processed.py script."""

import json
from unittest.mock import MagicMock, mock_open, patch


# Mock psycopg2 before importing the module
import sys

sys.modules["psycopg2"] = MagicMock()
sys.modules["psycopg2.extras"] = MagicMock()

from postgresql_remove_processed import remove_unprocessed_articles  # noqa: E402


class TestRemoveUnprocessedArticles:
    """Test remove_unprocessed_articles function."""

    @patch("postgresql_remove_processed.psycopg2.connect")
    @patch("builtins.open", new_callable=mock_open)
    def test_creates_temp_table(self, mock_file, mock_connect):
        """Test that temporary table is created."""
        # Setup mocks
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Setup file mock
        articles = [{"url": "https://example.com/1"}]
        mock_file.return_value.read.return_value = json.dumps(articles)

        # Mock json.load
        with patch("postgresql_remove_processed.json.load", return_value=articles):
            remove_unprocessed_articles(
                "postgresql://user:pass@localhost/db",  # pragma: allowlist secret
                "articles.json",
                "output.json",
            )

        # Check that CREATE TEMP TABLE was called
        create_calls = [
            call
            for call in mock_cursor.execute.call_args_list
            if "CREATE TEMP TABLE" in str(call)
        ]
        assert len(create_calls) == 1

    @patch("postgresql_remove_processed.psycopg2.connect")
    @patch("postgresql_remove_processed.execute_values")
    @patch("builtins.open", new_callable=mock_open)
    def test_inserts_urls_into_temp_table(
        self, mock_file, mock_execute_values, mock_connect
    ):
        """Test that URLs are inserted into temporary table."""
        # Setup mocks
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchall.return_value = [("https://example.com/1",)]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        articles = [{"url": "https://example.com/1"}, {"url": "https://example.com/2"}]

        with patch("postgresql_remove_processed.json.load", return_value=articles):
            remove_unprocessed_articles(
                "postgresql://user:pass@localhost/db",  # pragma: allowlist secret
                "articles.json",
                "output.json",
            )

        # Check that execute_values was called with URLs
        mock_execute_values.assert_called_once()
        call_args = mock_execute_values.call_args
        assert "INSERT INTO tmp_articles" in call_args[0][1]
        urls = call_args[0][2]
        assert len(urls) == 2

    @patch("postgresql_remove_processed.psycopg2.connect")
    @patch("postgresql_remove_processed.execute_values")
    @patch("builtins.open", new_callable=mock_open)
    def test_performs_left_join(self, mock_file, mock_execute_values, mock_connect):
        """Test that LEFT JOIN is performed to find unprocessed articles."""
        # Setup mocks
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchall.return_value = [("https://example.com/1",)]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        articles = [{"url": "https://example.com/1"}]

        with patch("postgresql_remove_processed.json.load", return_value=articles):
            remove_unprocessed_articles(
                "postgresql://user:pass@localhost/db",  # pragma: allowlist secret
                "articles.json",
                "output.json",
            )

        # Check that LEFT JOIN query was executed
        select_calls = [
            call
            for call in mock_cursor.execute.call_args_list
            if "LEFT JOIN" in str(call)
        ]
        assert len(select_calls) == 1

    @patch("postgresql_remove_processed.psycopg2.connect")
    @patch("postgresql_remove_processed.execute_values")
    @patch("builtins.open", new_callable=mock_open)
    def test_writes_unprocessed_articles(
        self, mock_file, mock_execute_values, mock_connect
    ):
        """Test that unprocessed articles are written to output file."""
        # Setup mocks
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchall.return_value = [("https://example.com/1",)]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        articles = [
            {"url": "https://example.com/1", "title": "Article 1"},
            {"url": "https://example.com/2", "title": "Article 2"},
        ]

        with patch("postgresql_remove_processed.json.load", return_value=articles):
            with patch("postgresql_remove_processed.json.dump") as mock_dump:
                remove_unprocessed_articles(
                    "postgresql://user:pass@localhost/db",  # pragma: allowlist secret
                    "articles.json",
                    "output.json",
                )

                # Check that only unprocessed article was written
                mock_dump.assert_called_once()
                written_articles = mock_dump.call_args[0][0]
                assert len(written_articles) == 1
                assert written_articles[0]["url"] == "https://example.com/1"

    @patch("postgresql_remove_processed.psycopg2.connect")
    @patch("postgresql_remove_processed.execute_values")
    @patch("builtins.open", new_callable=mock_open)
    def test_handles_empty_articles_list(
        self, mock_file, mock_execute_values, mock_connect
    ):
        """Test handling of empty articles list."""
        articles = []

        with patch("postgresql_remove_processed.json.load", return_value=articles):
            remove_unprocessed_articles(
                "postgresql://user:pass@localhost/db",  # pragma: allowlist secret
                "articles.json",
                "output.json",
            )

        # Should not connect to database for empty list
        mock_connect.assert_not_called()

    @patch("postgresql_remove_processed.psycopg2.connect")
    @patch("postgresql_remove_processed.execute_values")
    @patch("builtins.open", new_callable=mock_open)
    def test_handles_all_articles_processed(
        self, mock_file, mock_execute_values, mock_connect
    ):
        """Test handling when all articles are already processed."""
        # Setup mocks
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchall.return_value = []  # No unprocessed articles
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        articles = [{"url": "https://example.com/1"}]

        with patch("postgresql_remove_processed.json.load", return_value=articles):
            with patch("postgresql_remove_processed.json.dump") as mock_dump:
                remove_unprocessed_articles(
                    "postgresql://user:pass@localhost/db",  # pragma: allowlist secret
                    "articles.json",
                    "output.json",
                )

                # Should not write anything since no unprocessed articles
                mock_dump.assert_not_called()

    @patch("postgresql_remove_processed.psycopg2.connect")
    @patch("postgresql_remove_processed.execute_values")
    @patch("builtins.open", new_callable=mock_open)
    def test_uses_connection_string(self, mock_file, mock_execute_values, mock_connect):
        """Test that connection string is used correctly."""
        # Setup mocks
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        articles = [{"url": "https://example.com/1"}]
        connection_string = (
            "postgresql://user:pass@localhost:5432/test_db"  # pragma: allowlist secret
        )

        with patch("postgresql_remove_processed.json.load", return_value=articles):
            remove_unprocessed_articles(
                connection_string, "articles.json", "output.json"
            )

        # Check that connect was called with the connection string
        mock_connect.assert_called_once_with(connection_string)
