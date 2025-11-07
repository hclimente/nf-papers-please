"""Integration tests for unified database scripts.

These tests actually create real databases and test the full stack,
unlike the unit tests which just mock the database connections.
"""

import json
import sys
from pathlib import Path

import duckdb
import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db_create import create_articles_table, create_journal_table
from db_extract_fields import extract_fields
from db_insert_article import insert_article
from db_remove_processed import remove_unprocessed_articles
from db_update_field import update_field


class TestDuckDBIntegration:
    """Integration tests for DuckDB backend."""

    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create a temporary database path."""
        db_path = tmp_path / "test.duckdb"
        return str(db_path)

    @pytest.fixture
    def journals_tsv(self, tmp_path):
        """Create a sample journals TSV file."""
        tsv_path = tmp_path / "journals.tsv"
        tsv_path.write_text(
            "name\tfeed_url\n"
            "Nature\thttps://www.nature.com/nature.rss\n"
            "Science\thttps://www.science.org/rss/news.xml\n"
        )
        return str(tsv_path)

    @pytest.fixture
    def articles_json(self, tmp_path):
        """Create a sample articles JSON file."""
        json_path = tmp_path / "articles.json"
        articles = [
            {
                "title": "Test Article 1",
                "summary": "Summary 1",
                "url": "https://example.com/article1",
                "journal_name": "Nature",
                "date": "2025-01-01",
                "doi": "10.1234/test1",
                "tags": ["biology", "genetics"],
                "reasoning": "Relevant to research",
            },
            {
                "title": "Test Article 2",
                "summary": "Summary 2",
                "url": "https://example.com/article2",
                "journal_name": "Science",
                "date": "2025-01-02",
                "doi": "10.1234/test2",
                "tags": ["chemistry", "synthesis"],
                "reasoning": "Highly relevant",
            },
        ]
        json_path.write_text(json.dumps(articles))
        return str(json_path)

    def test_full_workflow(self, temp_db, journals_tsv, articles_json, tmp_path):
        """Test the complete workflow: create tables, insert, query, update, extract."""
        # 1. Create tables
        create_journal_table(journals_tsv, "2025-01-01", "duckdb", db_path=temp_db)
        create_articles_table("duckdb", db_path=temp_db)

        # 2. Verify tables were created
        with duckdb.connect(temp_db) as con:
            sources_count = con.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
            assert sources_count == 2

        # 3. Insert articles
        insert_article(articles_json, "duckdb", db_path=temp_db)

        # 4. Verify articles were inserted
        with duckdb.connect(temp_db) as con:
            articles_count = con.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
            assert articles_count == 2

        # 5. Update a field
        update_field(
            table="articles",
            set_clause="tags = ARRAY['updated']",
            where_clause="doi = '10.1234/test1'",
            db_type="duckdb",
            db_path=temp_db,
        )

        # 6. Verify update worked
        with duckdb.connect(temp_db) as con:
            result = con.execute(
                "SELECT tags FROM articles WHERE doi = '10.1234/test1'"
            ).fetchone()
            assert result[0] == ["updated"]

        # 7. Extract fields to TSV
        output_tsv = tmp_path / "output.tsv"
        extract_fields(
            table="articles",
            columns="title, doi",
            output_tsv=str(output_tsv),
            db_type="duckdb",
            db_path=temp_db,
        )

        # 8. Verify extraction
        content = output_tsv.read_text()
        assert "title\tdoi" in content
        assert "Test Article 1\t10.1234/test1" in content

    def test_remove_processed_articles(
        self, temp_db, journals_tsv, articles_json, tmp_path
    ):
        """Test removing already-processed articles."""
        # Create database and insert articles
        create_journal_table(journals_tsv, "2025-01-01", "duckdb", db_path=temp_db)
        create_articles_table("duckdb", db_path=temp_db)
        insert_article(articles_json, "duckdb", db_path=temp_db)

        # Create a new articles file with one new and one existing article
        new_articles_json = tmp_path / "new_articles.json"
        new_articles = [
            {
                "title": "Test Article 1",  # Already in DB
                "url": "https://example.com/article1",
            },
            {
                "title": "Test Article 3",  # New article
                "url": "https://example.com/article3",
            },
        ]
        new_articles_json.write_text(json.dumps(new_articles))

        # Remove processed articles
        output_json = tmp_path / "unprocessed.json"
        remove_unprocessed_articles(
            str(new_articles_json),
            str(output_json),
            "duckdb",
            db_path=temp_db,
        )

        # Verify only the new article remains
        with open(output_json) as f:
            unprocessed = json.load(f)
        assert len(unprocessed) == 1
        assert unprocessed[0]["url"] == "https://example.com/article3"

    def test_primary_key_constraint(self, temp_db, journals_tsv, articles_json):
        """Test that URL primary key constraint is enforced."""
        create_journal_table(journals_tsv, "2025-01-01", "duckdb", db_path=temp_db)
        create_articles_table("duckdb", db_path=temp_db)
        insert_article(articles_json, "duckdb", db_path=temp_db)

        # Try to insert duplicate (should fail due to PK constraint)
        with duckdb.connect(temp_db) as con:
            with pytest.raises(duckdb.ConstraintException):
                con.execute(
                    """
                    INSERT INTO articles (title, summary, url, journal_name, date, doi, tags, reasoning)
                    VALUES ('Duplicate', 'Summary', 'https://example.com/article1',
                            'Nature', '2025-01-01', 'doi', ARRAY['tags'], 'reasoning')
                    """
                )

    def test_special_characters_handling(self, temp_db, tmp_path):
        """Test handling of special characters in data."""
        # Create TSV with special characters
        journals_tsv = tmp_path / "journals.tsv"
        journals_tsv.write_text(
            "name\tfeed_url\n"
            "Nature & Science\thttps://example.com/feed?id=123&format=rss\n"
            "Cell (Journal)\thttps://example.com/cell.rss\n"
        )

        create_journal_table(str(journals_tsv), "2025-01-01", "duckdb", db_path=temp_db)

        with duckdb.connect(temp_db) as con:
            result = con.execute("SELECT name FROM sources ORDER BY name").fetchall()
            assert result[0][0] == "Cell (Journal)"
            assert result[1][0] == "Nature & Science"

    def test_null_values_handling(self, temp_db, journals_tsv, tmp_path):
        """Test handling of null values in articles."""
        create_journal_table(journals_tsv, "2025-01-01", "duckdb", db_path=temp_db)
        create_articles_table("duckdb", db_path=temp_db)

        # Insert article with null optional fields
        articles_json = tmp_path / "articles.json"
        articles = [
            {
                "title": "Test Article",
                "summary": "Summary",
                "url": "https://example.com/article",
                "journal_name": "Nature",
                "date": "2025-01-01",
                "doi": None,
                "tags": None,
                "reasoning": None,
            }
        ]
        articles_json.write_text(json.dumps(articles))

        insert_article(str(articles_json), "duckdb", db_path=temp_db)

        with duckdb.connect(temp_db) as con:
            result = con.execute(
                "SELECT doi, tags, reasoning FROM articles WHERE url = 'https://example.com/article'"
            ).fetchone()
            assert result[0] is None
            assert result[1] is None
            assert result[2] is None

    def test_empty_tsv_file(self, temp_db, tmp_path):
        """Test handling of empty TSV file (only header)."""
        journals_tsv = tmp_path / "empty.tsv"
        journals_tsv.write_text("name\tfeed_url\n")

        # Should raise error for empty list
        with pytest.raises(duckdb.InvalidInputException):
            create_journal_table(
                str(journals_tsv), "2025-01-01", "duckdb", db_path=temp_db
            )

    def test_malformed_tsv_file(self, temp_db, tmp_path):
        """Test handling of malformed TSV (missing column)."""
        journals_tsv = tmp_path / "malformed.tsv"
        journals_tsv.write_text("name\tfeed_url\nOnlyOneColumn\n")

        with pytest.raises(ValueError):
            create_journal_table(
                str(journals_tsv), "2025-01-01", "duckdb", db_path=temp_db
            )

    def test_insert_or_ignore_duplicates(self, temp_db, journals_tsv):
        """Test that INSERT OR IGNORE prevents duplicate journal entries."""
        create_journal_table(journals_tsv, "2025-01-01", "duckdb", db_path=temp_db)
        create_journal_table(journals_tsv, "2025-06-01", "duckdb", db_path=temp_db)

        with duckdb.connect(temp_db) as con:
            count = con.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
            assert count == 2  # Not 4

            # Verify first insertion is preserved
            result = con.execute(
                "SELECT last_checked FROM sources WHERE name = 'Nature'"
            ).fetchone()
            assert result[0] == "2025-01-01"

    def test_update_multiple_records(self, temp_db, journals_tsv, articles_json):
        """Test updating multiple records at once."""
        create_journal_table(journals_tsv, "2025-01-01", "duckdb", db_path=temp_db)
        create_articles_table("duckdb", db_path=temp_db)
        insert_article(articles_json, "duckdb", db_path=temp_db)

        update_field(
            table="articles",
            set_clause="tags = ARRAY['all_updated']",
            where_clause="journal_name = 'Nature' OR journal_name = 'Science'",
            db_type="duckdb",
            db_path=temp_db,
        )

        with duckdb.connect(temp_db) as con:
            result = con.execute(
                "SELECT COUNT(*) FROM articles WHERE 'all_updated' = ANY(tags)"
            ).fetchone()
            assert result[0] == 2

    def test_extract_with_where_clause(
        self, temp_db, journals_tsv, articles_json, tmp_path
    ):
        """Test extracting fields with WHERE clause."""
        create_journal_table(journals_tsv, "2025-01-01", "duckdb", db_path=temp_db)
        create_articles_table("duckdb", db_path=temp_db)
        insert_article(articles_json, "duckdb", db_path=temp_db)

        output_tsv = tmp_path / "filtered.tsv"
        extract_fields(
            table="articles",
            columns="title, doi",
            output_tsv=str(output_tsv),
            db_type="duckdb",
            db_path=temp_db,
            where_clause="journal_name = 'Nature'",
        )

        content = output_tsv.read_text()
        lines = content.strip().split("\n")
        assert len(lines) == 2  # Header + 1 data row
        assert "Test Article 1" in content
        assert "Test Article 2" not in content

    def test_auto_increment_id(self, temp_db, journals_tsv, articles_json):
        """Test that article IDs auto-increment correctly."""
        create_journal_table(journals_tsv, "2025-01-01", "duckdb", db_path=temp_db)
        create_articles_table("duckdb", db_path=temp_db)
        insert_article(articles_json, "duckdb", db_path=temp_db)

        with duckdb.connect(temp_db) as con:
            ids = con.execute("SELECT id FROM articles ORDER BY id").fetchall()
            assert ids[0][0] == 1
            assert ids[1][0] == 2
