"""Tests for db_insert_article.py script."""

from unittest.mock import MagicMock, mock_open, patch

import pytest
from db_insert_article import (
    ARTICLE_INSERT_FIELDS,
    extract_article_fields,
    get_insert_article_sql,
)

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


class TestArticleInsertFields:
    """Test ARTICLE_INSERT_FIELDS constant."""

    def test_article_insert_fields(self):
        """Test ARTICLE_INSERT_FIELDS constant (excludes id)."""
        expected = [
            "title",
            "summary",
            "url",
            "journal_name",
            "date",
            "doi",
            "tags",
            "reasoning",
            "embedding",
        ]
        assert ARTICLE_INSERT_FIELDS == expected


class TestExtractArticleFields:
    """Test extract_article_fields function."""

    def test_extract_all_fields(self):
        """Test extracting all article fields."""
        article = {
            "title": "Test Article",
            "summary": "Test summary",
            "url": "https://example.com",
            "journal_name": "Nature",
            "date": "2025-11-07",
            "doi": "10.1234/test",
            "tags": ["tag1", "tag2"],
            "reasoning": "Test reasoning",
            "embedding": list(range(3096)),
        }

        fields = extract_article_fields(article)
        assert fields == (
            "Test Article",
            "Test summary",
            "https://example.com",
            "Nature",
            "2025-11-07",
            "10.1234/test",
            ["tag1", "tag2"],
            "Test reasoning",
            list(range(3096)),
        )

    def test_extract_optional_fields_none(self):
        """Test extracting with optional fields missing."""
        article = {
            "title": "Test Article",
            "summary": "Test summary",
            "url": "https://example.com",
            "journal_name": "Nature",
            "date": "2025-11-07",
            "doi": "10.1234/test",
        }

        fields = extract_article_fields(article)
        assert fields[6] is None  # tags
        assert fields[7] is None  # reasoning
        assert fields[8] is None  # embedding

    def test_extract_custom_fields(self):
        """Test extracting custom field list."""
        article = {
            "title": "Test Article",
            "url": "https://example.com",
            "doi": "10.1234/test",
        }

        fields = extract_article_fields(article, fields=["title", "url"])
        assert fields == ("Test Article", "https://example.com")


class TestGetInsertArticleSql:
    """Test get_insert_article_sql function."""

    def test_duckdb_uses_question_marks(self):
        """Test DuckDB uses ? placeholders."""
        sql = get_insert_article_sql(db_type="duckdb")
        assert "INSERT INTO articles" in sql
        assert (
            "(title, summary, url, journal_name, date, doi, tags, reasoning, embedding)"
            in sql
        )
        assert "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)" in sql

    def test_postgresql_uses_percent_s(self):
        """Test PostgreSQL uses %s placeholders."""
        sql = get_insert_article_sql(db_type="pg")
        assert "INSERT INTO articles" in sql
        assert (
            "(title, summary, url, journal_name, date, doi, tags, reasoning, embedding)"
            in sql
        )
        assert "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)" in sql
