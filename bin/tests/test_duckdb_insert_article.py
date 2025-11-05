#!/usr/bin/env python
"""Tests for duckdb_insert_article.py"""

import pytest
import json
import sys
from pathlib import Path
from unittest.mock import patch
import tempfile
import duckdb

# Add the parent directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from duckdb_insert_article import insert_article


class TestInsertArticle:
    """Test suite for insert_article function"""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary DuckDB database with articles table"""
        # Create a temporary directory and database path
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "test.duckdb"

        # Create the sequence and articles table
        with duckdb.connect(str(db_path)) as con:
            con.execute("CREATE SEQUENCE article_id_seq START 1")
            con.execute(
                """
                CREATE TABLE articles (
                    id INTEGER PRIMARY KEY DEFAULT nextval('article_id_seq'),
                    title TEXT NOT NULL,
                    summary TEXT,
                    url TEXT NOT NULL,
                    journal_name TEXT NOT NULL,
                    date DATE NOT NULL,
                    doi TEXT,
                    tags TEXT[],
                    reasoning TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

        yield str(db_path)

        # Cleanup
        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)

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
                "tags": ["Other application"],
                "reasoning": "Not relevant to core interests",
            },
            {
                "title": "Third Article",
                "summary": "Third summary",
                "url": "https://example.com/article3",
                "journal_name": "Cell",
                "date": "2025-10-17",
                "doi": None,
                "tags": ["Computational Biology", "New Computational Method"],
                "reasoning": "Limited but positive impact",
            },
        ]

    def test_insert_minimal_article(self, temp_db, minimal_article_json, tmp_path):
        """Test inserting a minimal article with required fields only"""
        # Write JSON to a temporary file
        json_file = tmp_path / "articles.json"
        json_file.write_text(json.dumps(minimal_article_json))

        # Insert the article
        insert_article(temp_db, str(json_file))

        # Verify the article was inserted
        with duckdb.connect(temp_db) as con:
            result = con.execute("SELECT * FROM articles").fetchall()
            assert len(result) == 1

            article = result[0]
            # Skip id (index 0) and created_at (index 11)
            assert article[1] == "Test Article"  # title
            assert article[2] == "Test summary"  # summary
            assert article[3] == "https://example.com/article"  # url
            assert article[4] == "Nature"  # journal_name
            assert str(article[5]) == "2025-10-15"  # date
            assert article[6] is None  # doi
            assert article[7] is None  # tags
            assert article[8] is None  # reasoning

    def test_insert_full_article(self, temp_db, full_article_json, tmp_path):
        """Test inserting an article with all fields populated"""
        # Write JSON to a temporary file
        json_file = tmp_path / "articles.json"
        json_file.write_text(json.dumps(full_article_json))

        # Insert the article
        insert_article(temp_db, str(json_file))

        # Verify the article was inserted with all fields
        with duckdb.connect(temp_db) as con:
            result = con.execute("SELECT * FROM articles").fetchall()
            assert len(result) == 1

            article = result[0]
            assert article[1] == "Full Test Article"
            assert article[2] == "This is a comprehensive test summary"
            assert article[3] == "https://example.com/full-article"
            assert article[4] == "Science"
            assert str(article[5]) == "2025-10-20"
            assert article[6] == "10.1234/test.doi"
            assert article[7] == ["Network Biology", "Review"]
            assert article[8] == "Novel methodology with high relevance"

    def test_insert_multiple_articles(self, temp_db, multiple_articles_json, tmp_path):
        """Test inserting multiple articles from a single JSON file"""
        # Write JSON to a temporary file
        json_file = tmp_path / "articles.json"
        json_file.write_text(json.dumps(multiple_articles_json))

        # Insert the articles
        insert_article(temp_db, str(json_file))

        # Verify all articles were inserted
        with duckdb.connect(temp_db) as con:
            result = con.execute(
                "SELECT title, doi FROM articles ORDER BY date"
            ).fetchall()
            assert len(result) == 3
            assert result[0][0] == "First Article"
            assert result[1][0] == "Second Article"
            assert result[2][0] == "Third Article"

    def test_insert_with_optional_fields_mixed(self, temp_db, tmp_path):
        """Test inserting articles where some have optional fields and others don't"""
        articles = [
            {
                "title": "Article with tags",
                "summary": "Summary",
                "url": "https://example.com/1",
                "journal_name": "Journal",
                "date": "2025-10-15",
                "doi": "10.1234/1",
                "tags": ["Network Biology", "Drug discovery"],
                "reasoning": "Relevant to main interests",
            },
            {
                "title": "Article with different tags",
                "summary": "Summary",
                "url": "https://example.com/2",
                "journal_name": "Journal",
                "date": "2025-10-16",
                "doi": "10.1234/2",
                "tags": ["Other application"],
                "reasoning": "Not relevant subfield",
            },
        ]

        json_file = tmp_path / "articles.json"
        json_file.write_text(json.dumps(articles))

        insert_article(temp_db, str(json_file))

        with duckdb.connect(temp_db) as con:
            # Check first article
            result1 = con.execute(
                "SELECT tags, reasoning FROM articles WHERE doi = '10.1234/1'"
            ).fetchone()
            assert result1[0] == ["Network Biology", "Drug discovery"]
            assert result1[1] == "Relevant to main interests"

            # Check second article
            result2 = con.execute(
                "SELECT tags, reasoning FROM articles WHERE doi = '10.1234/2'"
            ).fetchone()
            assert result2[0] == ["Other application"]
            assert result2[1] == "Not relevant subfield"

    def test_insert_article_with_none_doi(self, temp_db, tmp_path):
        """Test inserting an article with None DOI"""
        articles = [
            {
                "title": "Article without DOI",
                "summary": "Summary",
                "url": "https://example.com/no-doi",
                "journal_name": "Journal",
                "date": "2025-10-15",
                "doi": None,
            }
        ]

        json_file = tmp_path / "articles.json"
        json_file.write_text(json.dumps(articles))

        insert_article(temp_db, str(json_file))

        with duckdb.connect(temp_db) as con:
            result = con.execute("SELECT doi FROM articles").fetchone()
            assert result[0] is None

    def test_insert_article_empty_json(self, temp_db, tmp_path):
        """Test inserting from an empty JSON array"""
        json_file = tmp_path / "articles.json"
        json_file.write_text("[]")

        # Should complete without error
        insert_article(temp_db, str(json_file))

        # Verify no articles were inserted
        with duckdb.connect(temp_db) as con:
            result = con.execute("SELECT COUNT(*) FROM articles").fetchone()
            assert result[0] == 0

    def test_insert_article_missing_required_field(self, temp_db, tmp_path):
        """Test that missing required fields raise an appropriate error"""
        articles = [
            {
                "title": "Missing URL",
                "summary": "Summary",
                # Missing 'url'
                "journal_name": "Journal",
                "date": "2025-10-15",
                "doi": None,
            }
        ]

        json_file = tmp_path / "articles.json"
        json_file.write_text(json.dumps(articles))

        # Should raise an exception due to missing required field
        with pytest.raises(Exception):
            insert_article(temp_db, str(json_file))

    def test_insert_article_invalid_database_path(self, tmp_path):
        """Test that invalid database path raises an error"""
        articles = [
            {
                "title": "Test",
                "summary": "Summary",
                "url": "https://example.com",
                "journal_name": "Journal",
                "date": "2025-10-15",
                "doi": None,
            }
        ]

        json_file = tmp_path / "articles.json"
        json_file.write_text(json.dumps(articles))

        # Use a path that doesn't exist and can't be created
        invalid_db = "/nonexistent/path/to/database.duckdb"

        with pytest.raises(Exception):
            insert_article(invalid_db, str(json_file))

    def test_insert_article_duplicate_not_prevented(
        self, temp_db, minimal_article_json, tmp_path
    ):
        """Test that duplicate articles can be inserted (no unique constraint)"""
        json_file = tmp_path / "articles.json"
        json_file.write_text(json.dumps(minimal_article_json))

        # Insert the same article twice
        insert_article(temp_db, str(json_file))
        insert_article(temp_db, str(json_file))

        # Verify both were inserted (no unique constraint exists)
        with duckdb.connect(temp_db) as con:
            result = con.execute("SELECT COUNT(*) FROM articles").fetchone()
            assert result[0] == 2

    def test_insert_article_with_special_characters(self, temp_db, tmp_path):
        """Test inserting articles with special characters in text fields"""
        articles = [
            {
                "title": "Article with 'quotes' and \"double quotes\" and émojis 🔬",
                "summary": "Summary with\nnewlines\nand\ttabs",
                "url": "https://example.com/special",
                "journal_name": "Journal of Special Characters™",
                "date": "2025-10-15",
                "doi": "10.1234/special-chars",
            }
        ]

        json_file = tmp_path / "articles.json"
        json_file.write_text(json.dumps(articles))

        insert_article(temp_db, str(json_file))

        with duckdb.connect(temp_db) as con:
            result = con.execute(
                "SELECT title, summary, journal_name FROM articles"
            ).fetchone()
            assert "quotes" in result[0]
            assert "émojis 🔬" in result[0]
            assert "\n" in result[1]
            assert "\t" in result[1]
            assert "™" in result[2]

    def test_insert_article_with_long_text(self, temp_db, tmp_path):
        """Test inserting articles with very long text fields"""
        long_text = "A" * 10000  # 10,000 characters

        articles = [
            {
                "title": long_text,
                "summary": long_text,
                "url": "https://example.com/long",
                "journal_name": "Journal",
                "date": "2025-10-15",
                "doi": "10.1234/long",
                "screening_reasoning": long_text,
                "priority_reasoning": long_text,
            }
        ]

        json_file = tmp_path / "articles.json"
        json_file.write_text(json.dumps(articles))

        insert_article(temp_db, str(json_file))

        with duckdb.connect(temp_db) as con:
            result = con.execute(
                "SELECT LENGTH(title), LENGTH(summary) FROM articles"
            ).fetchone()
            assert result[0] == 10000
            assert result[1] == 10000

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_insert_article_json_file_not_found(self, mock_file, temp_db):
        """Test that a missing JSON file raises FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            insert_article(temp_db, "nonexistent.json")

    @patch("json.load")
    def test_insert_article_invalid_json(self, mock_json_load, temp_db, tmp_path):
        """Test that invalid JSON raises an error"""
        mock_json_load.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

        json_file = tmp_path / "invalid.json"
        json_file.write_text("not valid json")

        with pytest.raises(json.JSONDecodeError):
            insert_article(temp_db, str(json_file))

    def test_insert_article_logs_info(
        self, temp_db, minimal_article_json, tmp_path, caplog
    ):
        """Test that appropriate log messages are generated"""
        import logging

        caplog.set_level(logging.INFO)

        json_file = tmp_path / "articles.json"
        json_file.write_text(json.dumps(minimal_article_json))

        insert_article(temp_db, str(json_file))

        # Check log messages
        assert "Loaded 1 articles" in caplog.text
        assert "Inserting article: Test Article" in caplog.text
        assert "✅ Article inserted successfully" in caplog.text

    def test_insert_article_logs_error_on_failure(self, temp_db, tmp_path, caplog):
        """Test that errors are logged when insertion fails"""
        import logging

        caplog.set_level(logging.ERROR)

        # Create an article with invalid data type for date
        articles = [
            {
                "title": "Invalid Date Article",
                "summary": "Summary",
                "url": "https://example.com",
                "journal_name": "Journal",
                "date": "not-a-date",  # Invalid date format
                "doi": None,
            }
        ]

        json_file = tmp_path / "articles.json"
        json_file.write_text(json.dumps(articles))

        # Should raise an exception and log an error
        with pytest.raises(Exception):
            insert_article(temp_db, str(json_file))

        assert "❌ Failed to insert article" in caplog.text
