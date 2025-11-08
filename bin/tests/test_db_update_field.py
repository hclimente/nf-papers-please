"""Tests for db_update_field.py script."""

from unittest.mock import MagicMock, patch

from db_update_field import get_update_field_sql

# Test connection string for PostgreSQL tests
TEST_PG_CONN_STRING = "postgresql://user:pass@localhost/db"  # pragma: allowlist secret


class TestUpdateFieldDuckDB:
    """Test update_field function with DuckDB."""

    @patch("duckdb.connect")
    def test_updates_field(self, mock_connect):
        """Test that field is updated."""
        from db_update_field import update_field

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_connect.return_value = mock_conn

        update_field(
            table="articles",
            set_clause="tags = 'biology'",
            where_clause="doi = '10.1234/test'",
            db_type="duckdb",
            db_path="test.duckdb",
        )

        # Check that UPDATE query was executed
        assert mock_conn.execute.called
        query = mock_conn.execute.call_args[0][0]
        assert "UPDATE articles" in query
        assert "SET tags = 'biology'" in query
        assert "WHERE doi = '10.1234/test'" in query

    @patch("duckdb.connect")
    def test_multiple_fields_in_set_clause(self, mock_connect):
        """Test that multiple fields can be updated."""
        from db_update_field import update_field

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_connect.return_value = mock_conn

        update_field(
            table="articles",
            set_clause="tags = 'biology', reasoning = 'relevant'",
            where_clause="doi = '10.1234/test'",
            db_type="duckdb",
            db_path="test.duckdb",
        )

        query = mock_conn.execute.call_args[0][0]
        assert "tags = 'biology', reasoning = 'relevant'" in query

    @patch("duckdb.connect")
    def test_complex_where_clause(self, mock_connect):
        """Test that complex WHERE clauses work."""
        from db_update_field import update_field

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_connect.return_value = mock_conn

        update_field(
            table="articles",
            set_clause="tags = 'biology'",
            where_clause="date > '2025-01-01' AND journal_name = 'Nature'",
            db_type="duckdb",
            db_path="test.duckdb",
        )

        query = mock_conn.execute.call_args[0][0]
        assert "WHERE date > '2025-01-01' AND journal_name = 'Nature'" in query


class TestUpdateFieldPostgreSQL:
    """Test update_field function with PostgreSQL."""

    @patch("psycopg2.connect")
    def test_updates_field(self, mock_connect):
        """Test that field is updated."""
        from db_update_field import update_field

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        update_field(
            table="articles",
            set_clause="tags = 'biology'",
            where_clause="doi = '10.1234/test'",
            db_type="postgresql",
            connection_string=TEST_PG_CONN_STRING,
        )

        # Check that UPDATE query was executed
        assert mock_cursor.execute.called
        query = mock_cursor.execute.call_args[0][0]
        assert "UPDATE articles" in query
        assert "SET tags = 'biology'" in query
        assert "WHERE doi = '10.1234/test'" in query

    @patch("psycopg2.connect")
    def test_commits_transaction(self, mock_connect):
        """Test that transaction is committed."""
        from db_update_field import update_field

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        update_field(
            table="articles",
            set_clause="tags = 'biology'",
            where_clause="doi = '10.1234/test'",
            db_type="postgresql",
            connection_string=TEST_PG_CONN_STRING,
        )

        assert mock_conn.commit.called

    @patch("psycopg2.connect")
    def test_multiple_fields_in_set_clause(self, mock_connect):
        """Test that multiple fields can be updated."""
        from db_update_field import update_field

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        update_field(
            table="articles",
            set_clause="tags = 'biology', reasoning = 'relevant'",
            where_clause="doi = '10.1234/test'",
            db_type="postgresql",
            connection_string=TEST_PG_CONN_STRING,
        )

        query = mock_cursor.execute.call_args[0][0]
        assert "tags = 'biology', reasoning = 'relevant'" in query

    @patch("psycopg2.connect")
    def test_complex_where_clause(self, mock_connect):
        """Test that complex WHERE clauses work."""
        from db_update_field import update_field

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        update_field(
            table="articles",
            set_clause="tags = 'biology'",
            where_clause="date > '2025-01-01' AND journal_name = 'Nature'",
            db_type="postgresql",
            connection_string=TEST_PG_CONN_STRING,
        )

        query = mock_cursor.execute.call_args[0][0]
        assert "WHERE date > '2025-01-01' AND journal_name = 'Nature'" in query


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
