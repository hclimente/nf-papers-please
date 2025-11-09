"""Tests for db_insert_article.py script."""

from unittest.mock import MagicMock, mock_open, patch

import pytest

# Test connection string for PostgreSQL tests
TEST_PG_CONN_STRING = "postgresql://user:pass@localhost/db"  # pragma: allowlist secret


class TestInsertArticleDuckDB:
    """Test insert_article function with DuckDB."""

    @patch("duckdb.connect")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='[{"title": "Test Article", "summary": "Test summary", "url": "https://example.com", "journal_name": "Nature", "date": "2025-01-01", "doi": "10.1234/test", "tags": "test", "reasoning": "test reason"}]',
    )
    def test_inserts_single_article(self, mock_file, mock_connect):
        """Test that a single article is inserted."""
        from db_insert_article import insert_article

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_connect.return_value = mock_conn

        insert_article("articles.json", "duckdb", db_path="test.duckdb")

        # Check that execute was called once
        assert mock_conn.execute.call_count == 1
        call_args = mock_conn.execute.call_args
        assert "INSERT" in call_args[0][0]

    @patch("duckdb.connect")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='[{"title": "Article 1", "summary": "Summary 1", "url": "https://example1.com", "journal_name": "Nature", "date": "2025-01-01", "doi": "10.1234/test1", "tags": "test", "reasoning": "reason1"}, {"title": "Article 2", "summary": "Summary 2", "url": "https://example2.com", "journal_name": "Science", "date": "2025-01-02", "doi": "10.1234/test2", "tags": "test", "reasoning": "reason2"}]',
    )
    def test_inserts_multiple_articles(self, mock_file, mock_connect):
        """Test that multiple articles are inserted."""
        from db_insert_article import insert_article

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_connect.return_value = mock_conn

        insert_article("articles.json", "duckdb", db_path="test.duckdb")

        # Check that execute was called twice (once per article)
        assert mock_conn.execute.call_count == 2

    @patch("duckdb.connect")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='[{"title": "Test", "summary": "Summary", "url": "https://example.com", "journal_name": "Nature", "date": "2025-01-01", "doi": null, "tags": null, "reasoning": null}]',
    )
    def test_handles_null_fields(self, mock_file, mock_connect):
        """Test that null fields are handled correctly."""
        from db_insert_article import insert_article

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_connect.return_value = mock_conn

        insert_article("articles.json", "duckdb", db_path="test.duckdb")

        assert mock_conn.execute.called

    @patch("duckdb.connect")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='[{"title": "Test", "summary": "Summary", "url": "https://example.com", "journal_name": "Nature", "date": "2025-01-01", "doi": "10.1234/test", "tags": "test", "reasoning": "reason"}]',
    )
    def test_error_handling(self, mock_file, mock_connect):
        """Test that errors are raised properly."""
        from db_insert_article import insert_article

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.side_effect = Exception("Database error")
        mock_connect.return_value = mock_conn

        with pytest.raises(Exception):
            insert_article("articles.json", "duckdb", db_path="test.duckdb")


class TestInsertArticlePostgreSQL:
    """Test insert_article function with PostgreSQL."""

    @patch("psycopg2.connect")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='[{"title": "Test Article", "summary": "Test summary", "url": "https://example.com", "journal_name": "Nature", "date": "2025-01-01", "doi": "10.1234/test", "tags": "test", "reasoning": "test reason"}]',
    )
    def test_inserts_single_article(self, mock_file, mock_connect):
        """Test that a single article is inserted."""
        from db_insert_article import insert_article

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        insert_article("articles.json", "pg", connection_string=TEST_PG_CONN_STRING)

        # Check that execute was called once
        assert mock_cursor.execute.call_count == 1
        call_args = mock_cursor.execute.call_args
        assert "INSERT" in call_args[0][0]

    @patch("psycopg2.connect")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='[{"title": "Article 1", "summary": "Summary 1", "url": "https://example1.com", "journal_name": "Nature", "date": "2025-01-01", "doi": "10.1234/test1", "tags": "test", "reasoning": "reason1"}, {"title": "Article 2", "summary": "Summary 2", "url": "https://example2.com", "journal_name": "Science", "date": "2025-01-02", "doi": "10.1234/test2", "tags": "test", "reasoning": "reason2"}]',
    )
    def test_inserts_multiple_articles(self, mock_file, mock_connect):
        """Test that multiple articles are inserted."""
        from db_insert_article import insert_article

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        insert_article("articles.json", "pg", connection_string=TEST_PG_CONN_STRING)

        # Check that execute was called twice (once per article)
        assert mock_cursor.execute.call_count == 2

    @patch("psycopg2.connect")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='[{"title": "Test", "summary": "Summary", "url": "https://example.com", "journal_name": "Nature", "date": "2025-01-01", "doi": "10.1234/test", "tags": "test", "reasoning": "reason"}]',
    )
    def test_commits_transaction(self, mock_file, mock_connect):
        """Test that transaction is committed."""
        from db_insert_article import insert_article

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        insert_article("articles.json", "pg", connection_string=TEST_PG_CONN_STRING)

        assert mock_conn.commit.called

    @patch("psycopg2.connect")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='[{"title": "Test", "summary": "Summary", "url": "https://example.com", "journal_name": "Nature", "date": "2025-01-01", "doi": "10.1234/test", "tags": "test", "reasoning": "reason"}]',
    )
    def test_rollback_on_error(self, mock_file, mock_connect):
        """Test that transaction is rolled back on error."""
        from db_insert_article import insert_article

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.execute.side_effect = Exception("Database error")
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        with pytest.raises(Exception):
            insert_article("articles.json", "pg", connection_string=TEST_PG_CONN_STRING)

        assert mock_conn.rollback.called
