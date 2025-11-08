"""Tests for db_remove_processed.py script."""

from unittest.mock import MagicMock, mock_open, patch

from db_remove_processed import (
    get_create_temp_articles_table_sql,
    get_select_unprocessed_sql,
)

# Test connection string for PostgreSQL tests
TEST_PG_CONN_STRING = "postgresql://user:pass@localhost/db"  # pragma: allowlist secret


class TestRemoveUnprocessedArticlesDuckDB:
    """Test remove_unprocessed_articles function with DuckDB."""

    @patch("duckdb.connect")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='[{"url": "https://example1.com"}, {"url": "https://example2.com"}]',
    )
    def test_creates_temp_table(self, mock_file, mock_connect):
        """Test that temporary table is created."""
        from db_remove_processed import remove_processed_articles

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value.fetchall.return_value = [
            ("https://example1.com",)
        ]
        mock_connect.return_value = mock_conn

        remove_processed_articles(
            "articles.json", "output.json", "duckdb", db_path="test.duckdb"
        )

        # Check that CREATE TEMPORARY TABLE was called
        create_calls = [
            call
            for call in mock_conn.execute.call_args_list
            if "CREATE TEMPORARY TABLE" in str(call)
        ]
        assert len(create_calls) > 0

    @patch("duckdb.connect")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='[{"url": "https://example1.com"}, {"url": "https://example2.com"}]',
    )
    def test_inserts_urls_to_temp_table(self, mock_file, mock_connect):
        """Test that URLs are inserted into temporary table."""
        from db_remove_processed import remove_processed_articles

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value.fetchall.return_value = [
            ("https://example1.com",)
        ]
        mock_connect.return_value = mock_conn

        remove_processed_articles(
            "articles.json", "output.json", "duckdb", db_path="test.duckdb"
        )

        # Check that executemany was called
        assert mock_conn.executemany.called
        call_args = mock_conn.executemany.call_args
        assert "INSERT INTO tmp_articles" in call_args[0][0]

    @patch("duckdb.connect")
    @patch("db_remove_processed.json.load")
    @patch("db_remove_processed.json.dump")
    @patch("builtins.open", new_callable=mock_open)
    def test_writes_unprocessed_articles(
        self, mock_file, mock_dump, mock_load, mock_connect
    ):
        """Test that unprocessed articles are written to output file."""
        from db_remove_processed import remove_processed_articles

        mock_load.return_value = [
            {"url": "https://example1.com", "title": "Article 1"},
            {"url": "https://example2.com", "title": "Article 2"},
        ]

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        # Only example1 is unprocessed
        mock_conn.execute.return_value.fetchall.return_value = [
            ("https://example1.com",)
        ]
        mock_connect.return_value = mock_conn

        remove_processed_articles(
            "articles.json", "output.json", "duckdb", db_path="test.duckdb"
        )

        # Check that json.dump was called with only unprocessed article
        assert mock_dump.called
        dumped_articles = mock_dump.call_args[0][0]
        assert len(dumped_articles) == 1
        assert dumped_articles[0]["url"] == "https://example1.com"

    @patch("duckdb.connect")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="[]",
    )
    def test_handles_empty_articles_list(self, mock_file, mock_connect):
        """Test that empty articles list is handled."""
        from db_remove_processed import remove_processed_articles

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        remove_processed_articles(
            "articles.json", "output.json", "duckdb", db_path="test.duckdb"
        )

        # Should not try to connect to database
        assert not mock_connect.called


class TestRemoveUnprocessedArticlesPostgreSQL:
    """Test remove_unprocessed_articles function with PostgreSQL."""

    @patch("psycopg2.connect")
    @patch("psycopg2.extras.execute_values")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='[{"url": "https://example1.com"}, {"url": "https://example2.com"}]',
    )
    def test_creates_temp_table(self, mock_file, mock_execute_values, mock_connect):
        """Test that temporary table is created."""
        from db_remove_processed import remove_processed_articles

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchall.return_value = [("https://example1.com",)]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        remove_processed_articles(
            "articles.json",
            "output.json",
            "pg",
            connection_string=TEST_PG_CONN_STRING,
        )

        # Check that CREATE TEMP TABLE was called
        create_calls = [
            call
            for call in mock_cursor.execute.call_args_list
            if "CREATE" in str(call) and "TEMP" in str(call)
        ]
        assert len(create_calls) > 0

    @patch("psycopg2.connect")
    @patch("psycopg2.extras.execute_values")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='[{"url": "https://example1.com"}, {"url": "https://example2.com"}]',
    )
    def test_uses_execute_values(self, mock_file, mock_execute_values, mock_connect):
        """Test that execute_values is used for batch insert."""
        from db_remove_processed import remove_processed_articles

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchall.return_value = [("https://example1.com",)]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        remove_processed_articles(
            "articles.json",
            "output.json",
            "pg",
            connection_string=TEST_PG_CONN_STRING,
        )

        # Check that execute_values was called
        assert mock_execute_values.called
        call_args = mock_execute_values.call_args
        assert "INSERT INTO tmp_articles" in call_args[0][1]

    @patch("psycopg2.connect")
    @patch("psycopg2.extras.execute_values")
    @patch("db_remove_processed.json.load")
    @patch("db_remove_processed.json.dump")
    @patch("builtins.open", new_callable=mock_open)
    def test_writes_unprocessed_articles(
        self, mock_file, mock_dump, mock_load, mock_execute_values, mock_connect
    ):
        """Test that unprocessed articles are written to output file."""
        from db_remove_processed import remove_processed_articles

        mock_load.return_value = [
            {"url": "https://example1.com", "title": "Article 1"},
            {"url": "https://example2.com", "title": "Article 2"},
        ]

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        # Only example1 is unprocessed
        mock_cursor.fetchall.return_value = [("https://example1.com",)]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        remove_processed_articles(
            "articles.json",
            "output.json",
            "pg",
            connection_string=TEST_PG_CONN_STRING,
        )

        # Check that json.dump was called with only unprocessed article
        assert mock_dump.called
        dumped_articles = mock_dump.call_args[0][0]
        assert len(dumped_articles) == 1
        assert dumped_articles[0]["url"] == "https://example1.com"

    @patch("psycopg2.connect")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="[]",
    )
    def test_handles_empty_articles_list(self, mock_file, mock_connect):
        """Test that empty articles list is handled."""
        from db_remove_processed import remove_processed_articles

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        remove_processed_articles(
            "articles.json",
            "output.json",
            "pg",
            connection_string=TEST_PG_CONN_STRING,
        )

        # Should not try to connect to database
        assert not mock_connect.called


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
        sql = get_create_temp_articles_table_sql(db_type="pg")
        assert "CREATE TEMP TABLE tmp_articles" in sql
        assert "url TEXT" in sql
