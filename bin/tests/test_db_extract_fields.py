"""Tests for db_extract_fields.py script."""

from unittest.mock import MagicMock, mock_open, patch


class TestExtractFieldsDuckDB:
    """Test extract_fields function with DuckDB."""

    @patch("duckdb.connect")
    @patch("builtins.open", new_callable=mock_open)
    def test_extracts_fields_from_table(self, mock_file, mock_connect):
        """Test that fields are extracted from a table."""
        from db_extract_fields import extract_fields

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value.fetchall.return_value = [
            ("Title 1", "Summary 1"),
            ("Title 2", "Summary 2"),
        ]
        mock_connect.return_value = mock_conn

        extract_fields(
            table="articles",
            columns="title, summary",
            out="output.tsv",
            db_type="duckdb",
            db_path="test.duckdb",
        )

        # Check that SELECT query was executed
        assert mock_conn.execute.called
        query = mock_conn.execute.call_args[0][0]
        assert "SELECT title, summary FROM articles" in query

    @patch("duckdb.connect")
    @patch("builtins.open", new_callable=mock_open)
    def test_applies_where_clause(self, mock_file, mock_connect):
        """Test that WHERE clause is applied correctly."""
        from db_extract_fields import extract_fields

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value.fetchall.return_value = [
            ("Title 1", "Summary 1")
        ]
        mock_connect.return_value = mock_conn

        extract_fields(
            table="articles",
            columns="title, summary",
            out="output.tsv",
            db_type="duckdb",
            db_path="test.duckdb",
            where_clause="date > '2025-01-01'",
        )

        query = mock_conn.execute.call_args[0][0]
        assert "WHERE date > '2025-01-01'" in query

    @patch("duckdb.connect")
    @patch("builtins.open", new_callable=mock_open)
    def test_writes_header_row(self, mock_file, mock_connect):
        """Test that header row is written to TSV."""
        from db_extract_fields import extract_fields

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value.fetchall.return_value = [
            ("Title 1", "Summary 1")
        ]
        mock_connect.return_value = mock_conn

        extract_fields(
            table="articles",
            columns="title, summary",
            out="output.tsv",
            db_type="duckdb",
            db_path="test.duckdb",
        )

        # Check that write was called with header
        write_calls = mock_file().write.call_args_list
        assert "title\tsummary\n" in write_calls[0][0][0]

    @patch("duckdb.connect")
    @patch("builtins.open", new_callable=mock_open)
    def test_writes_data_rows(self, mock_file, mock_connect):
        """Test that data rows are written to TSV."""
        from db_extract_fields import extract_fields

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value.fetchall.return_value = [
            ("Title 1", "Summary 1"),
            ("Title 2", "Summary 2"),
        ]
        mock_connect.return_value = mock_conn

        extract_fields(
            table="articles",
            columns="title, summary",
            out="output.tsv",
            db_type="duckdb",
            db_path="test.duckdb",
        )

        # Check that data rows were written
        write_calls = mock_file().write.call_args_list
        assert len(write_calls) == 3  # header + 2 data rows

    @patch("duckdb.connect")
    @patch("builtins.open", new_callable=mock_open)
    def test_custom_separator(self, mock_file, mock_connect):
        """Test that custom separator is used."""
        from db_extract_fields import extract_fields

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value.fetchall.return_value = [
            ("Title 1", "Summary 1")
        ]
        mock_connect.return_value = mock_conn

        extract_fields(
            table="articles",
            columns="title, summary",
            out="output.tsv",
            db_type="duckdb",
            db_path="test.duckdb",
            sep=",",
        )

        # Check that comma separator was used
        write_calls = mock_file().write.call_args_list
        assert "title,summary\n" in write_calls[0][0][0]


class TestExtractFieldsPostgreSQL:
    """Test extract_fields function with PostgreSQL."""

    @patch("psycopg2.connect")
    @patch("builtins.open", new_callable=mock_open)
    def test_extracts_fields_from_table(self, mock_file, mock_connect):
        """Test that fields are extracted from a table."""
        from db_extract_fields import extract_fields

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchall.return_value = [
            ("Title 1", "Summary 1"),
            ("Title 2", "Summary 2"),
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        extract_fields(
            table="articles",
            columns="title, summary",
            out="output.tsv",
            db_type="postgresql",
            connection_string="postgresql://user:pass@localhost/db",  # noqa: F402 # pragma: allowlist secret
        )

        # Check that SELECT query was executed
        assert mock_cursor.execute.called
        query = mock_cursor.execute.call_args[0][0]
        assert "SELECT title, summary FROM articles" in query

    @patch("psycopg2.connect")
    @patch("builtins.open", new_callable=mock_open)
    def test_applies_where_clause(self, mock_file, mock_connect):
        """Test that WHERE clause is applied correctly."""
        from db_extract_fields import extract_fields

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchall.return_value = [("Title 1", "Summary 1")]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        extract_fields(
            table="articles",
            columns="title, summary",
            out="output.tsv",
            db_type="postgresql",
            connection_string="postgresql://user:pass@localhost/db",  # noqa: F402 # pragma: allowlist secret
            where_clause="date > '2025-01-01'",
        )

        query = mock_cursor.execute.call_args[0][0]
        assert "WHERE date > '2025-01-01'" in query

    @patch("psycopg2.connect")
    @patch("builtins.open", new_callable=mock_open)
    def test_writes_header_and_data(self, mock_file, mock_connect):
        """Test that header and data are written to TSV."""
        from db_extract_fields import extract_fields

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchall.return_value = [("Title 1", "Summary 1")]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        extract_fields(
            table="articles",
            columns="title, summary",
            out="output.tsv",
            db_type="postgresql",
            connection_string="postgresql://user:pass@localhost/db",  # noqa: F402 # pragma: allowlist secret
        )

        # Check that write was called
        assert mock_file().write.called
