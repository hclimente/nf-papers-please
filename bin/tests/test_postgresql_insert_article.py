#!/usr/bin/env python
"""Tests for postgresql_insert_article.py"""

import pytest
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

# Check if psycopg2 is available
try:
    import psycopg2  # noqa: F401

    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False


@pytest.mark.skipif(not POSTGRESQL_AVAILABLE, reason="psycopg2 not installed")
class TestInsertArticle:
    """Test suite for insert_article function"""

    @pytest.fixture
    def minimal_article_json(self):
        """Create a minimal article JSON structure"""
        return [
            {
                "title": "Test Article",
                "summary": "Test summary",
                "url": "https://example.com/article",
                "journal_name": "Nature",
                "date": "2025-10-15",
                "doi": None,
            }
        ]

    @pytest.fixture
    def full_article_json(self):
        """Create a full article JSON structure with all fields"""
        return [
            {
                "title": "Full Test Article",
                "summary": "This is a comprehensive test summary",
                "url": "https://example.com/full-article",
                "journal_name": "Science",
                "date": "2025-10-20",
                "doi": "10.1234/test.doi",
                "tags": ["Network Biology", "Review"],
                "reasoning": "Novel methodology with high relevance",
            }
        ]

    @pytest.fixture
    def multiple_articles_json(self):
        """Create multiple articles JSON structure"""
        return [
            {
                "title": "First Article",
                "summary": "First summary",
                "url": "https://example.com/article1",
                "journal_name": "Nature",
                "date": "2025-10-15",
                "doi": "10.1234/first",
            },
            {
                "title": "Second Article",
                "summary": "Second summary",
                "url": "https://example.com/article2",
                "journal_name": "Science",
                "date": "2025-10-16",
                "doi": "10.1234/second",
                "tags": ["Machine Learning"],
            },
            {
                "title": "Third Article",
                "summary": "Third summary",
                "url": "https://example.com/article3",
                "journal_name": "Cell",
                "date": "2025-10-17",
                "doi": None,
                "reasoning": "Important findings",
            },
        ]

    def test_insert_minimal_article(self, minimal_article_json, tmp_path):
        """Test inserting a minimal article with only required fields"""
        from postgresql_insert_article import insert_article

        json_file = tmp_path / "articles.json"
        json_file.write_text(json.dumps(minimal_article_json))

        # Mock psycopg2 connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn

        with patch("psycopg2.connect", return_value=mock_conn):
            insert_article(
                "postgresql://user:pass@localhost/db",  # pragma: allowlist secret
                str(json_file),
            )

            # Verify execute was called with correct SQL
            assert mock_cursor.execute.called
            call_args = mock_cursor.execute.call_args[0]
            assert "INSERT INTO articles" in call_args[0]
            assert "VALUES" in call_args[0]

            # Verify the article data was passed
            article_data = call_args[1]
            assert article_data[0] == "Test Article"
            assert article_data[2] == "https://example.com/article"

            # Verify commit was called
            assert mock_conn.commit.called

    def test_insert_full_article(self, full_article_json, tmp_path):
        """Test inserting a full article with all optional fields"""
        from postgresql_insert_article import insert_article

        json_file = tmp_path / "articles.json"
        json_file.write_text(json.dumps(full_article_json))

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn

        with patch("psycopg2.connect", return_value=mock_conn):
            insert_article(
                "postgresql://user:pass@localhost/db",  # pragma: allowlist secret
                str(json_file),
            )

            # Verify execute was called
            assert mock_cursor.execute.called
            call_args = mock_cursor.execute.call_args[0]
            article_data = call_args[1]

            # Check all fields
            assert article_data[0] == "Full Test Article"
            assert article_data[1] == "This is a comprehensive test summary"
            assert article_data[5] == "10.1234/test.doi"
            assert article_data[6] == ["Network Biology", "Review"]
            assert article_data[7] == "Novel methodology with high relevance"

    def test_insert_multiple_articles(self, multiple_articles_json, tmp_path):
        """Test inserting multiple articles"""
        from postgresql_insert_article import insert_article

        json_file = tmp_path / "articles.json"
        json_file.write_text(json.dumps(multiple_articles_json))

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn

        with patch("psycopg2.connect", return_value=mock_conn):
            insert_article(
                "postgresql://user:pass@localhost/db",  # pragma: allowlist secret
                str(json_file),
            )

            # Verify execute was called 3 times (once per article)
            assert mock_cursor.execute.call_count == 3
            # Verify commit was called 3 times
            assert mock_conn.commit.call_count == 3

    def test_insert_article_with_optional_fields_mixed(self, tmp_path):
        """Test inserting articles with mixed optional fields"""
        from postgresql_insert_article import insert_article

        articles = [
            {
                "title": "Article with tags",
                "summary": "Summary",
                "url": "https://example.com/1",
                "journal_name": "Nature",
                "date": "2025-10-15",
                "doi": "10.1234/test",
                "tags": ["Tag1", "Tag2"],
            },
            {
                "title": "Article with reasoning",
                "summary": "Summary",
                "url": "https://example.com/2",
                "journal_name": "Science",
                "date": "2025-10-16",
                "doi": None,
                "reasoning": "Important work",
            },
        ]

        json_file = tmp_path / "articles.json"
        json_file.write_text(json.dumps(articles))

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn

        with patch("psycopg2.connect", return_value=mock_conn):
            insert_article(
                "postgresql://user:pass@localhost/db",  # pragma: allowlist secret
                str(json_file),
            )

            assert mock_cursor.execute.call_count == 2

    def test_insert_article_with_none_doi(self, tmp_path):
        """Test inserting an article with None doi"""
        from postgresql_insert_article import insert_article

        articles = [
            {
                "title": "No DOI Article",
                "summary": "Summary",
                "url": "https://example.com/article",
                "journal_name": "Nature",
                "date": "2025-10-15",
                "doi": None,
            }
        ]

        json_file = tmp_path / "articles.json"
        json_file.write_text(json.dumps(articles))

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn

        with patch("psycopg2.connect", return_value=mock_conn):
            insert_article(
                "postgresql://user:pass@localhost/db",  # pragma: allowlist secret
                str(json_file),
            )

            call_args = mock_cursor.execute.call_args[0]
            article_data = call_args[1]
            assert article_data[5] is None  # doi should be None

    def test_insert_article_empty_json(self, tmp_path):
        """Test inserting from an empty JSON array"""
        from postgresql_insert_article import insert_article

        json_file = tmp_path / "empty.json"
        json_file.write_text("[]")

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn

        with patch("psycopg2.connect", return_value=mock_conn):
            insert_article(
                "postgresql://user:pass@localhost/db",  # pragma: allowlist secret
                str(json_file),
            )

            # No execute calls should be made
            assert mock_cursor.execute.call_count == 0

    def test_insert_article_missing_required_field(self, tmp_path):
        """Test that missing required fields cause an error"""
        from postgresql_insert_article import insert_article

        articles = [
            {
                "title": "Incomplete Article",
                "url": "https://example.com/article",
                # Missing summary, journal_name, date
            }
        ]

        json_file = tmp_path / "articles.json"
        json_file.write_text(json.dumps(articles))

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn

        with patch("psycopg2.connect", return_value=mock_conn):
            with pytest.raises(KeyError):
                insert_article(
                    "postgresql://user:pass@localhost/db",  # pragma: allowlist secret
                    str(json_file),
                )

    def test_insert_article_rollback_on_database_error(
        self, minimal_article_json, tmp_path
    ):
        """Test that database errors trigger rollback"""
        from postgresql_insert_article import insert_article

        json_file = tmp_path / "articles.json"
        json_file.write_text(json.dumps(minimal_article_json))

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # Simulate database error
        mock_cursor.execute.side_effect = Exception("Database constraint violation")
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn

        with patch("psycopg2.connect", return_value=mock_conn):
            with pytest.raises(Exception, match="Database constraint violation"):
                insert_article(
                    "postgresql://user:pass@localhost/db",  # pragma: allowlist secret
                    str(json_file),
                )

            # Verify rollback was called
            assert mock_conn.rollback.called

    def test_insert_article_with_special_characters(self, tmp_path):
        """Test inserting articles with special characters"""
        from postgresql_insert_article import insert_article

        articles = [
            {
                "title": "Article with special chars: €, ñ, 中文",
                "summary": "Summary with 'quotes' and \"double quotes\"",
                "url": "https://example.com/article",
                "journal_name": "Nature™",
                "date": "2025-10-15",
                "doi": "10.1234/test",
            }
        ]

        json_file = tmp_path / "articles.json"
        json_file.write_text(json.dumps(articles))

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn

        with patch("psycopg2.connect", return_value=mock_conn):
            insert_article(
                "postgresql://user:pass@localhost/db",  # pragma: allowlist secret
                str(json_file),
            )

            assert mock_cursor.execute.called

    def test_insert_article_with_long_text(self, tmp_path):
        """Test inserting articles with very long text fields"""
        from postgresql_insert_article import insert_article

        long_summary = "A" * 10000
        articles = [
            {
                "title": "Article with long summary",
                "summary": long_summary,
                "url": "https://example.com/article",
                "journal_name": "Nature",
                "date": "2025-10-15",
                "doi": "10.1234/test",
            }
        ]

        json_file = tmp_path / "articles.json"
        json_file.write_text(json.dumps(articles))

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn

        with patch("psycopg2.connect", return_value=mock_conn):
            insert_article(
                "postgresql://user:pass@localhost/db",  # pragma: allowlist secret
                str(json_file),
            )

            call_args = mock_cursor.execute.call_args[0]
            article_data = call_args[1]
            assert len(article_data[1]) == 10000

    def test_insert_article_json_file_not_found(self):
        """Test that missing JSON file raises FileNotFoundError"""
        from postgresql_insert_article import insert_article

        with pytest.raises(FileNotFoundError):
            insert_article(
                "postgresql://user:pass@localhost/db",  # pragma: allowlist secret
                "/nonexistent/file.json",
            )

    def test_insert_article_invalid_json(self, tmp_path):
        """Test that invalid JSON raises an error"""
        from postgresql_insert_article import insert_article

        json_file = tmp_path / "invalid.json"
        json_file.write_text("not valid json")

        with pytest.raises(json.JSONDecodeError):
            insert_article(
                "postgresql://user:pass@localhost/db",  # pragma: allowlist secret
                str(json_file),
            )

    def test_insert_article_logs_info(self, minimal_article_json, tmp_path, caplog):
        """Test that appropriate log messages are generated"""
        from postgresql_insert_article import insert_article
        import logging

        caplog.set_level(logging.INFO)

        json_file = tmp_path / "articles.json"
        json_file.write_text(json.dumps(minimal_article_json))

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn

        with patch("psycopg2.connect", return_value=mock_conn):
            insert_article(
                "postgresql://user:pass@localhost/db",  # pragma: allowlist secret
                str(json_file),
            )

            # Check log messages
            assert "Loaded 1 articles" in caplog.text
            assert "Inserting article: Test Article" in caplog.text
            assert "✅ Article inserted successfully" in caplog.text

    def test_insert_article_logs_error_on_failure(
        self, minimal_article_json, tmp_path, caplog
    ):
        """Test that errors are logged when insertion fails"""
        from postgresql_insert_article import insert_article
        import logging

        caplog.set_level(logging.ERROR)

        json_file = tmp_path / "articles.json"
        json_file.write_text(json.dumps(minimal_article_json))

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("Connection error")
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn

        with patch("psycopg2.connect", return_value=mock_conn):
            with pytest.raises(Exception):
                insert_article(
                    "postgresql://user:pass@localhost/db",  # pragma: allowlist secret
                    str(json_file),
                )

            assert "❌ Failed to insert article" in caplog.text

    def test_insert_article_uses_placeholders(self, minimal_article_json, tmp_path):
        """Test that PostgreSQL placeholders (%s) are used, not DuckDB (?)"""
        from postgresql_insert_article import insert_article

        json_file = tmp_path / "articles.json"
        json_file.write_text(json.dumps(minimal_article_json))

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn

        with patch("psycopg2.connect", return_value=mock_conn):
            insert_article(
                "postgresql://user:pass@localhost/db",  # pragma: allowlist secret
                str(json_file),
            )

            call_args = mock_cursor.execute.call_args[0]
            sql = call_args[0]
            # PostgreSQL uses %s, not ?
            assert "%s" in sql
            assert "?" not in sql

    def test_insert_article_connection_string_format(
        self, minimal_article_json, tmp_path
    ):
        """Test various connection string formats"""
        from postgresql_insert_article import insert_article

        json_file = tmp_path / "articles.json"
        json_file.write_text(json.dumps(minimal_article_json))

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn

        connection_strings = [
            "postgresql://user:pass@localhost/db",  # pragma: allowlist secret
            "postgresql://user@localhost/db",
            "postgresql://localhost/db",
            "postgresql://host:5432/database",
        ]

        for conn_str in connection_strings:
            with patch("psycopg2.connect", return_value=mock_conn) as mock_connect:
                insert_article(conn_str, str(json_file))
                mock_connect.assert_called_with(conn_str)


class TestImportError:
    """Test suite for import error handling"""

    def test_import_error_message(self):
        """Test that helpful error message is shown when psycopg2 is not installed"""
        # This test verifies the module has proper import error handling
        # Since we mock psycopg2 for testing, we just verify the module can be imported
        # In production, if psycopg2 is missing, the ImportError will be raised
        try:
            import postgresql_insert_article

            # If import succeeds (with or without psycopg2), that's fine
            assert hasattr(postgresql_insert_article, "insert_article")
        except ImportError as e:
            # If import fails, verify it's about psycopg2
            assert "psycopg2" in str(e)
