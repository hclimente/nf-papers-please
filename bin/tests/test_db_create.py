"""Tests for db_create.py script."""

from unittest.mock import MagicMock, mock_open, patch

import pytest
from db_create import (
    get_articles_table_schema,
    get_insert_sources_sql,
    get_sources_table_schema,
    parse_journals_tsv,
)


class TestCreateJournalTableDuckDB:
    """Test create_journal_table function with DuckDB."""

    @patch("duckdb.connect")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="name\tfeed_url\nNature\thttps://nature.com/feed\nScience\thttps://science.org/feed\n",
    )
    def test_creates_sources_table(self, mock_file, mock_connect):
        """Test that sources table is created."""
        from db_create import create_journal_table

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_connect.return_value = mock_conn

        create_journal_table(
            "journals.tsv", "2025-01-01", "duckdb", db_path="test.duckdb"
        )

        # Check that CREATE TABLE was called
        create_call = mock_conn.execute.call_args_list[0]
        assert "CREATE TABLE IF NOT EXISTS sources" in create_call[0][0]

    @patch("duckdb.connect")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="name\tfeed_url\nNature\thttps://nature.com/feed\nScience\thttps://science.org/feed\n",
    )
    def test_inserts_journal_sources(self, mock_file, mock_connect):
        """Test that journal sources are inserted."""
        from db_create import create_journal_table

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_connect.return_value = mock_conn

        create_journal_table(
            "journals.tsv", "2025-01-01", "duckdb", db_path="test.duckdb"
        )

        # Check that executemany was called with sources
        assert mock_conn.executemany.called
        call_args = mock_conn.executemany.call_args
        assert "INSERT" in call_args[0][0]
        assert len(call_args[0][1]) == 2  # 2 journals

    @patch("duckdb.connect")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="name\tfeed_url\nNature\thttps://nature.com/feed\n",
    )
    def test_uses_insert_or_ignore(self, mock_file, mock_connect):
        """Test that INSERT OR IGNORE is used for duplicate handling."""
        from db_create import create_journal_table

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_connect.return_value = mock_conn

        create_journal_table(
            "journals.tsv", "2025-01-01", "duckdb", db_path="test.duckdb"
        )

        # Check that INSERT OR IGNORE is in the INSERT statement
        call_args = mock_conn.executemany.call_args
        assert "INSERT OR IGNORE" in call_args[0][0]


class TestCreateJournalTablePostgreSQL:
    """Test create_journal_table function with PostgreSQL."""

    @patch("psycopg2.connect")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="name\tfeed_url\nNature\thttps://nature.com/feed\nScience\thttps://science.org/feed\n",
    )
    def test_creates_sources_table(self, mock_file, mock_connect):
        """Test that sources table is created."""
        from db_create import create_journal_table

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        create_journal_table(
            "journals.tsv",
            "2025-01-01",
            "postgresql",
            connection_string="postgresql://user:pass@localhost/db",  # noqa: F402 # pragma: allowlist secret
        )

        # Check that CREATE TABLE was called
        create_call = mock_cursor.execute.call_args_list[0]
        assert "CREATE TABLE IF NOT EXISTS sources" in create_call[0][0]

    @patch("psycopg2.connect")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="name\tfeed_url\nNature\thttps://nature.com/feed\nScience\thttps://science.org/feed\n",
    )
    def test_inserts_journal_sources(self, mock_file, mock_connect):
        """Test that journal sources are inserted."""
        from db_create import create_journal_table

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        create_journal_table(
            "journals.tsv",
            "2025-01-01",
            "postgresql",
            connection_string="postgresql://user:pass@localhost/db",  # noqa: F402 # pragma: allowlist secret
        )

        # Check that INSERT statements were called (2 journals)
        insert_calls = [
            call for call in mock_cursor.execute.call_args_list if "INSERT" in str(call)
        ]
        assert len(insert_calls) == 2

    @patch("psycopg2.connect")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="name\tfeed_url\nNature\thttps://nature.com/feed\n",
    )
    def test_uses_on_conflict(self, mock_file, mock_connect):
        """Test that ON CONFLICT is used for duplicate handling."""
        from db_create import create_journal_table

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        create_journal_table(
            "journals.tsv",
            "2025-01-01",
            "postgresql",
            connection_string="postgresql://user:pass@localhost/db",  # noqa: F402 # pragma: allowlist secret
        )

        # Check that ON CONFLICT is in the INSERT statement
        insert_calls = [
            call for call in mock_cursor.execute.call_args_list if "INSERT" in str(call)
        ]
        assert any("ON CONFLICT" in str(call) for call in insert_calls)


class TestCreateArticlesTableDuckDB:
    """Test create_articles_table function with DuckDB."""

    @patch("duckdb.connect")
    def test_creates_articles_table(self, mock_connect):
        """Test that articles table is created."""
        from db_create import create_articles_table

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_connect.return_value = mock_conn

        create_articles_table("duckdb", db_path="test.duckdb")

        # Check that CREATE TABLE was called
        assert mock_conn.execute.called
        create_call = mock_conn.execute.call_args[0][0]
        assert "CREATE TABLE IF NOT EXISTS articles" in create_call

    @patch("duckdb.connect")
    def test_uses_sequence_for_id(self, mock_connect):
        """Test that DuckDB uses a sequence for the id field."""
        from db_create import create_articles_table

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_connect.return_value = mock_conn

        create_articles_table("duckdb", db_path="test.duckdb")

        create_call = mock_conn.execute.call_args[0][0]
        assert "CREATE SEQUENCE" in create_call


class TestCreateArticlesTablePostgreSQL:
    """Test create_articles_table function with PostgreSQL."""

    @patch("psycopg2.connect")
    def test_creates_articles_table(self, mock_connect):
        """Test that articles table is created."""
        from db_create import create_articles_table

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        create_articles_table(
            "postgresql",
            connection_string="postgresql://user:pass@localhost/db",  # noqa: F402 # pragma: allowlist secret
        )

        # Check that CREATE TABLE was called
        assert mock_cursor.execute.called
        create_call = mock_cursor.execute.call_args[0][0]
        assert "CREATE TABLE IF NOT EXISTS articles" in create_call

    @patch("psycopg2.connect")
    def test_uses_serial_for_id(self, mock_connect):
        """Test that PostgreSQL uses SERIAL for the id field."""
        from db_create import create_articles_table

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        create_articles_table(
            "postgresql",
            connection_string="postgresql://user:pass@localhost/db",  # noqa: F402 # pragma: allowlist secret
        )

        create_call = mock_cursor.execute.call_args[0][0]
        assert "SERIAL" in create_call or "serial" in create_call


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
