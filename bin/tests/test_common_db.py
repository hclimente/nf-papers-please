"""Tests for common/db.py module."""

import pytest
from common.db import (
    ARTICLES_TABLE_COLUMNS,
    ARTICLE_INSERT_FIELDS,
    SOURCES_TABLE_COLUMNS,
    extract_article_fields,
    get_articles_table_schema,
    get_create_temp_articles_table_sql,
    get_insert_article_sql,
    get_insert_sources_sql,
    get_placeholder_style,
    get_select_unprocessed_sql,
    get_sources_table_schema,
    get_update_field_sql,
    parse_journals_tsv,
)


class TestConstants:
    """Test module constants."""

    def test_sources_table_columns(self):
        """Test SOURCES_TABLE_COLUMNS constant."""
        assert SOURCES_TABLE_COLUMNS == ["name", "feed_url", "last_checked"]

    def test_articles_table_columns(self):
        """Test ARTICLES_TABLE_COLUMNS constant."""
        expected = [
            "id",
            "title",
            "journal_name",
            "summary",
            "url",
            "date",
            "doi",
            "tags",
            "reasoning",
        ]
        assert ARTICLES_TABLE_COLUMNS == expected

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
        ]
        assert ARTICLE_INSERT_FIELDS == expected


class TestGetSourcesTableSchema:
    """Test get_sources_table_schema function."""

    def test_schema_contains_create_table(self):
        """Test schema contains CREATE TABLE statement."""
        schema = get_sources_table_schema()
        assert "CREATE TABLE IF NOT EXISTS sources" in schema

    def test_schema_contains_all_columns(self):
        """Test schema contains all required columns."""
        schema = get_sources_table_schema()
        assert "name TEXT PRIMARY KEY" in schema
        assert "feed_url TEXT NOT NULL" in schema
        assert "last_checked TEXT NOT NULL" in schema


class TestGetArticlesTableSchema:
    """Test get_articles_table_schema function."""

    def test_duckdb_schema_includes_sequence(self):
        """Test DuckDB schema includes sequence creation."""
        schema = get_articles_table_schema(db_type="duckdb")
        assert "CREATE SEQUENCE IF NOT EXISTS article_id_seq START 1" in schema
        assert "NEXTVAL('article_id_seq')" in schema
        assert "PRIMARY KEY (url)" in schema

    def test_duckdb_schema_contains_all_columns(self):
        """Test DuckDB schema contains all required columns."""
        schema = get_articles_table_schema(db_type="duckdb")
        assert "CREATE TABLE IF NOT EXISTS articles" in schema
        assert "id INTEGER" in schema
        assert "title TEXT NOT NULL" in schema
        assert "journal_name TEXT" in schema
        assert "summary TEXT NOT NULL" in schema
        assert "url TEXT NOT NULL" in schema
        assert "date DATE NOT NULL" in schema
        assert "doi TEXT DEFAULT NULL" in schema
        assert "tags TEXT[] DEFAULT NULL" in schema
        assert "reasoning TEXT DEFAULT NULL" in schema
        assert "FOREIGN KEY (journal_name) REFERENCES sources(name)" in schema

    def test_postgresql_schema_uses_serial(self):
        """Test PostgreSQL schema uses SERIAL for id generation."""
        schema = get_articles_table_schema(db_type="postgresql")
        assert "id SERIAL PRIMARY KEY" in schema
        assert "url TEXT NOT NULL UNIQUE" in schema
        assert "CREATE SEQUENCE" not in schema  # SERIAL handles this

    def test_postgresql_schema_contains_all_columns(self):
        """Test PostgreSQL schema contains all required columns."""
        schema = get_articles_table_schema(db_type="postgresql")
        assert "CREATE TABLE IF NOT EXISTS articles" in schema
        assert "title TEXT NOT NULL" in schema
        assert "journal_name TEXT" in schema
        assert "summary TEXT NOT NULL" in schema
        assert "url TEXT NOT NULL UNIQUE" in schema
        assert "date DATE NOT NULL" in schema
        assert "doi TEXT DEFAULT NULL" in schema
        assert "tags TEXT[] DEFAULT NULL" in schema
        assert "reasoning TEXT DEFAULT NULL" in schema
        assert "FOREIGN KEY (journal_name) REFERENCES sources(name)" in schema

    def test_invalid_db_type_raises_error(self):
        """Test invalid db_type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown db_type: invalid"):
            get_articles_table_schema(db_type="invalid")


class TestParseJournalsTsv:
    """Test parse_journals_tsv function."""

    def test_parse_basic_tsv(self, tmp_path):
        """Test parsing basic TSV file."""
        tsv_file = tmp_path / "journals.tsv"
        tsv_file.write_text(
            "journal_name\tfeed_url\n"
            "Nature\thttps://nature.com/feed\n"
            "Science\thttps://science.org/feed\n"
        )

        journals = parse_journals_tsv(str(tsv_file))
        assert len(journals) == 2
        assert journals[0] == ("Nature", "https://nature.com/feed")
        assert journals[1] == ("Science", "https://science.org/feed")

    def test_skips_empty_lines(self, tmp_path):
        """Test parsing skips empty lines."""
        tsv_file = tmp_path / "journals.tsv"
        tsv_file.write_text(
            "journal_name\tfeed_url\n"
            "Nature\thttps://nature.com/feed\n"
            "\n"
            "Science\thttps://science.org/feed\n"
        )

        journals = parse_journals_tsv(str(tsv_file))
        assert len(journals) == 2

    def test_skips_header_line(self, tmp_path):
        """Test parsing skips header line."""
        tsv_file = tmp_path / "journals.tsv"
        tsv_file.write_text("journal_name\tfeed_url\nNature\thttps://nature.com/feed\n")

        journals = parse_journals_tsv(str(tsv_file))
        assert ("journal_name", "feed_url") not in journals


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

    def test_extract_custom_fields(self):
        """Test extracting custom field list."""
        article = {
            "title": "Test Article",
            "url": "https://example.com",
            "doi": "10.1234/test",
        }

        fields = extract_article_fields(article, fields=["title", "url"])
        assert fields == ("Test Article", "https://example.com")


class TestGetInsertSourcesSql:
    """Test get_insert_sources_sql function."""

    def test_duckdb_uses_insert_or_ignore(self):
        """Test DuckDB uses INSERT OR IGNORE syntax."""
        sql = get_insert_sources_sql(db_type="duckdb")
        assert "INSERT OR IGNORE INTO sources" in sql
        assert "(name, feed_url, last_checked)" in sql
        assert "VALUES (?, ?, ?)" in sql

    def test_postgresql_uses_on_conflict(self):
        """Test PostgreSQL uses ON CONFLICT syntax."""
        sql = get_insert_sources_sql(db_type="postgresql")
        assert "INSERT INTO sources" in sql
        assert "(name, feed_url, last_checked)" in sql
        assert "VALUES (%s, %s, %s)" in sql
        assert "ON CONFLICT (name) DO NOTHING" in sql

    def test_invalid_db_type_raises_error(self):
        """Test invalid db_type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown db_type: invalid"):
            get_insert_sources_sql(db_type="invalid")


class TestGetInsertArticleSql:
    """Test get_insert_article_sql function."""

    def test_duckdb_uses_question_marks(self):
        """Test DuckDB uses ? placeholders."""
        sql = get_insert_article_sql(db_type="duckdb")
        assert "INSERT INTO articles" in sql
        assert "(title, summary, url, journal_name, date, doi, tags, reasoning)" in sql
        assert "VALUES (?, ?, ?, ?, ?, ?, ?, ?)" in sql

    def test_postgresql_uses_percent_s(self):
        """Test PostgreSQL uses %s placeholders."""
        sql = get_insert_article_sql(db_type="postgresql")
        assert "INSERT INTO articles" in sql
        assert "(title, summary, url, journal_name, date, doi, tags, reasoning)" in sql
        assert "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)" in sql


class TestGetUpdateFieldSql:
    """Test get_update_field_sql function."""

    def test_duckdb_update_sql(self):
        """Test DuckDB UPDATE statement generation."""
        sql = get_update_field_sql("articles", "title", "url", db_type="duckdb")
        assert "UPDATE articles" in sql
        assert "SET title = ?" in sql
        assert "WHERE url = ?" in sql

    def test_postgresql_update_sql(self):
        """Test PostgreSQL UPDATE statement generation."""
        sql = get_update_field_sql("articles", "tags", "doi", db_type="postgresql")
        assert "UPDATE articles" in sql
        assert "SET tags = %s" in sql
        assert "WHERE doi = %s" in sql


class TestGetSelectUnprocessedSql:
    """Test get_select_unprocessed_sql function."""

    def test_returns_left_join_query(self):
        """Test returns LEFT JOIN query."""
        sql = get_select_unprocessed_sql()
        assert "SELECT a.url" in sql
        assert "FROM tmp_articles a" in sql
        assert "LEFT JOIN articles p" in sql
        assert "ON a.url = p.url" in sql
        assert "WHERE p.title IS NULL" in sql


class TestGetCreateTempArticlesTableSql:
    """Test get_create_temp_articles_table_sql function."""

    def test_duckdb_uses_temporary(self):
        """Test DuckDB uses TEMPORARY keyword."""
        sql = get_create_temp_articles_table_sql(db_type="duckdb")
        assert "CREATE TEMPORARY TABLE tmp_articles" in sql
        assert "url TEXT" in sql

    def test_postgresql_uses_temp(self):
        """Test PostgreSQL uses TEMP keyword."""
        sql = get_create_temp_articles_table_sql(db_type="postgresql")
        assert "CREATE TEMP TABLE tmp_articles" in sql
        assert "url TEXT" in sql


class TestGetPlaceholderStyle:
    """Test get_placeholder_style function."""

    def test_duckdb_returns_question_mark(self):
        """Test DuckDB returns ? placeholder."""
        assert get_placeholder_style(db_type="duckdb") == "?"

    def test_postgresql_returns_percent_s(self):
        """Test PostgreSQL returns %s placeholder."""
        assert get_placeholder_style(db_type="postgresql") == "%s"

    def test_invalid_db_type_raises_error(self):
        """Test invalid db_type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown db_type: invalid"):
            get_placeholder_style(db_type="invalid")
