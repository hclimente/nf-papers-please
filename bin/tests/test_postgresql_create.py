"""Tests for postgresql_create.py script."""

from unittest.mock import MagicMock, mock_open, patch


# Mock psycopg2 before importing the module
import sys

from postgresql_create import create_articles_table, create_journal_table

sys.modules["psycopg2"] = MagicMock()


class TestCreateJournalTable:
    """Test create_journal_table function."""

    @patch("postgresql_create.psycopg2.connect")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="name\tfeed_url\nNature\thttps://nature.com/feed\nScience\thttps://science.org/feed\n",
    )
    def test_creates_sources_table(self, mock_file, mock_connect):
        """Test that sources table is created."""
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
            "postgresql://user:pass@localhost/db",  # pragma: allowlist secret
            "2025-01-01",
        )

        # Check that CREATE TABLE was called
        create_call = mock_cursor.execute.call_args_list[0]
        assert "CREATE TABLE IF NOT EXISTS sources" in create_call[0][0]

    @patch("postgresql_create.psycopg2.connect")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="name\tfeed_url\nNature\thttps://nature.com/feed\nScience\thttps://science.org/feed\n",
    )
    def test_inserts_journal_sources(self, mock_file, mock_connect):
        """Test that journal sources are inserted."""
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
            "postgresql://user:pass@localhost/db",  # pragma: allowlist secret
            "2025-01-01",
        )

        # Check that INSERT statements were called (2 journals)
        insert_calls = [
            call for call in mock_cursor.execute.call_args_list if "INSERT" in str(call)
        ]
        assert len(insert_calls) == 2

    @patch("postgresql_create.psycopg2.connect")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="name\tfeed_url\nNature\thttps://nature.com/feed\n",
    )
    def test_uses_on_conflict(self, mock_file, mock_connect):
        """Test that ON CONFLICT is used for duplicate handling."""
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
            "postgresql://user:pass@localhost/db",  # pragma: allowlist secret
            "2025-01-01",
        )

        # Check that ON CONFLICT is in the INSERT statement
        insert_calls = [
            call for call in mock_cursor.execute.call_args_list if "INSERT" in str(call)
        ]
        assert any("ON CONFLICT" in str(call) for call in insert_calls)

    @patch("postgresql_create.psycopg2.connect")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="name\tfeed_url\nNature\thttps://nature.com/feed\n",
    )
    def test_commits_transaction(self, mock_file, mock_connect):
        """Test that transaction is committed."""
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
            "postgresql://user:pass@localhost/db",  # pragma: allowlist secret
            "2025-01-01",
        )

        # Check that commit was called (twice: once after CREATE, once after INSERTs)
        assert mock_conn.commit.call_count == 2

    @patch("postgresql_create.psycopg2.connect")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="name\tfeed_url\nNature\thttps://nature.com/feed\n\nScience\thttps://science.org/feed\n",
    )
    def test_skips_empty_lines(self, mock_file, mock_connect):
        """Test that empty lines in TSV are skipped."""
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
            "postgresql://user:pass@localhost/db",  # pragma: allowlist secret
            "2025-01-01",
        )

        # Should only have 2 INSERT calls (not 3)
        insert_calls = [
            call for call in mock_cursor.execute.call_args_list if "INSERT" in str(call)
        ]
        assert len(insert_calls) == 2


class TestCreateArticlesTable:
    """Test create_articles_table function."""

    @patch("postgresql_create.psycopg2.connect")
    def test_creates_articles_table(self, mock_connect):
        """Test that articles table is created."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        create_articles_table(
            "postgresql://user:pass@localhost/db"  # pragma: allowlist secret
        )

        # Check that CREATE TABLE was called
        create_call = mock_cursor.execute.call_args_list[0]
        assert "CREATE TABLE IF NOT EXISTS articles" in create_call[0][0]

    @patch("postgresql_create.psycopg2.connect")
    def test_uses_serial_for_id(self, mock_connect):
        """Test that SERIAL is used for id column."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        create_articles_table(
            "postgresql://user:pass@localhost/db"  # pragma: allowlist secret
        )

        # Check that SERIAL is in the CREATE statement
        create_call = mock_cursor.execute.call_args_list[0]
        assert "SERIAL PRIMARY KEY" in create_call[0][0]

    @patch("postgresql_create.psycopg2.connect")
    def test_has_unique_url_constraint(self, mock_connect):
        """Test that url column has UNIQUE constraint."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        create_articles_table(
            "postgresql://user:pass@localhost/db"  # pragma: allowlist secret
        )

        # Check that url has UNIQUE constraint
        create_call = mock_cursor.execute.call_args_list[0]
        assert "url TEXT NOT NULL UNIQUE" in create_call[0][0]

    @patch("postgresql_create.psycopg2.connect")
    def test_commits_transaction(self, mock_connect):
        """Test that transaction is committed."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        create_articles_table(
            "postgresql://user:pass@localhost/db"  # pragma: allowlist secret
        )

        # Check that commit was called
        assert mock_conn.commit.call_count == 1

    @patch("postgresql_create.psycopg2.connect")
    def test_has_foreign_key_constraint(self, mock_connect):
        """Test that journal_name has foreign key constraint."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        create_articles_table(
            "postgresql://user:pass@localhost/db"  # pragma: allowlist secret
        )

        # Check that FOREIGN KEY constraint exists
        create_call = mock_cursor.execute.call_args_list[0]
        assert (
            "FOREIGN KEY (journal_name) REFERENCES sources(name)" in create_call[0][0]
        )
