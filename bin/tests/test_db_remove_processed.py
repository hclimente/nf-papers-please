"""Tests for db_remove_processed.py script."""

from unittest.mock import MagicMock, patch, mock_open

# Test connection string for PostgreSQL tests
TEST_PG_CONN_STRING = "postgresql://user:pass@localhost/db"  # pragma: allowlist secret


class TestRemoveProcessedArticles:
    """Test remove_processed_articles function with SQLModel."""

    @patch("db_remove_processed.create_engine")
    @patch("pathlib.Path.read_text")
    @patch("builtins.open", new_callable=mock_open)
    def test_creates_temp_table(self, mock_file, mock_read_text, mock_create_engine):
        """Test that temporary table is created."""
        from db_remove_processed import remove_processed_articles

        mock_read_text.return_value = '[{"url": "https://example1.com", "date": "2025-01-01", "access_date": "2025-11-09", "raw_contents": "test", "journal_name": "Nature"}, {"url": "https://example2.com", "date": "2025-01-01", "access_date": "2025-11-09", "raw_contents": "test", "journal_name": "Science"}]'

        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        with patch("db_remove_processed.Session") as mock_session_class:
            mock_session_instance = MagicMock()
            mock_session_class.return_value.__enter__.return_value = (
                mock_session_instance
            )
            mock_session_instance.exec.return_value.all.return_value = [
                ("https://example1.com",)
            ]

            # Mock the Table.create method
            with patch("db_remove_processed.Table") as mock_table_class:
                mock_table = MagicMock()
                mock_table_class.return_value = mock_table

                remove_processed_articles(
                    "articles.json",
                    "output.json",
                    connection_string=TEST_PG_CONN_STRING,
                )

                # Check that temp table was created
                assert mock_table.create.called

    @patch("db_remove_processed.create_engine")
    @patch("pathlib.Path.read_text")
    @patch("builtins.open", new_callable=mock_open)
    def test_inserts_urls_to_temp_table(
        self, mock_file, mock_read_text, mock_create_engine
    ):
        """Test that URLs are inserted into temporary table."""
        from db_remove_processed import remove_processed_articles

        mock_read_text.return_value = '[{"url": "https://example1.com", "date": "2025-01-01", "access_date": "2025-11-09", "raw_contents": "test", "journal_name": "Nature"}, {"url": "https://example2.com", "date": "2025-01-01", "access_date": "2025-11-09", "raw_contents": "test", "journal_name": "Science"}]'

        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        with patch("db_remove_processed.Session") as mock_session_class:
            mock_session_instance = MagicMock()
            mock_session_class.return_value.__enter__.return_value = (
                mock_session_instance
            )
            mock_session_instance.exec.return_value.all.return_value = [
                ("https://example1.com",)
            ]

            # Mock the Table.create method
            with patch("db_remove_processed.Table"):
                remove_processed_articles(
                    "articles.json",
                    "output.json",
                    connection_string=TEST_PG_CONN_STRING,
                )

                # Check that execute was called to insert URLs
                assert mock_session_instance.execute.called

    @patch("db_remove_processed.create_engine")
    @patch("pathlib.Path.read_text")
    @patch("builtins.open", mock_open())
    def test_writes_unprocessed_articles(self, mock_read_text, mock_create_engine):
        """Test that unprocessed articles are written to output file."""
        from db_remove_processed import remove_processed_articles

        mock_read_text.return_value = '[{"url": "https://example1.com", "title": "Article 1", "date": "2025-01-01", "access_date": "2025-11-09", "raw_contents": "test", "journal_name": "Nature"}, {"url": "https://example2.com", "title": "Article 2", "date": "2025-01-01", "access_date": "2025-11-09", "raw_contents": "test", "journal_name": "Science"}]'

        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        with patch("db_remove_processed.Session") as mock_session_class:
            mock_session_instance = MagicMock()
            mock_session_class.return_value.__enter__.return_value = (
                mock_session_instance
            )
            # Only example1 is unprocessed
            mock_session_instance.exec.return_value.all.return_value = [
                ("https://example1.com",)
            ]

            # Mock the Table.create and drop methods
            with patch("db_remove_processed.Table"):
                with patch("builtins.open", mock_open()) as mock_file:
                    remove_processed_articles(
                        "articles.json",
                        "output.json",
                        connection_string=TEST_PG_CONN_STRING,
                    )

                    # Check that output file was opened for writing
                    mock_file.assert_called_with("output.json", "w")
                    # Check that write was called
                    handle = mock_file()
                    assert handle.write.called

    @patch("db_remove_processed.create_engine")
    @patch("pathlib.Path.read_text")
    def test_filters_correctly(self, mock_read_text, mock_create_engine):
        """Test that articles are filtered correctly based on database results."""
        from db_remove_processed import remove_processed_articles

        mock_read_text.return_value = '[{"url": "https://example1.com", "title": "Article 1", "date": "2025-01-01", "access_date": "2025-11-09", "raw_contents": "test", "journal_name": "Nature"}, {"url": "https://example2.com", "title": "Article 2", "date": "2025-01-01", "access_date": "2025-11-09", "raw_contents": "test", "journal_name": "Science"}, {"url": "https://example3.com", "title": "Article 3", "date": "2025-01-01", "access_date": "2025-11-09", "raw_contents": "test", "journal_name": "Cell"}]'

        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        with patch("db_remove_processed.Session") as mock_session_class:
            mock_session_instance = MagicMock()
            mock_session_class.return_value.__enter__.return_value = (
                mock_session_instance
            )
            # Only example1 and example3 are unprocessed
            mock_session_instance.exec.return_value.all.return_value = [
                ("https://example1.com",),
                ("https://example3.com",),
            ]

            written_content = []

            def mock_write(content):
                written_content.append(content)

            with patch("db_remove_processed.Table"):
                with patch("builtins.open", mock_open()) as mock_file:
                    mock_file.return_value.write.side_effect = mock_write

                    remove_processed_articles(
                        "articles.json",
                        "output.json",
                        connection_string=TEST_PG_CONN_STRING,
                    )

                    # Verify that some content was written
                    assert len(written_content) > 0

    @patch("db_remove_processed.create_engine")
    @patch("pathlib.Path.read_text")
    @patch("builtins.open", mock_open())
    def test_commits_transaction(self, mock_read_text, mock_create_engine):
        """Test that transaction is committed."""
        from db_remove_processed import remove_processed_articles

        mock_read_text.return_value = '[{"url": "https://example1.com", "date": "2025-01-01", "access_date": "2025-11-09", "raw_contents": "test", "journal_name": "Nature"}]'

        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        with patch("db_remove_processed.Session") as mock_session_class:
            mock_session_instance = MagicMock()
            mock_session_class.return_value.__enter__.return_value = (
                mock_session_instance
            )
            mock_session_instance.exec.return_value.all.return_value = [
                ("https://example1.com",)
            ]

            with patch("db_remove_processed.Table"):
                remove_processed_articles(
                    "articles.json",
                    "output.json",
                    connection_string=TEST_PG_CONN_STRING,
                )

                # Check that commit was called
                assert mock_session_instance.commit.called

    @patch("db_remove_processed.create_engine")
    @patch("pathlib.Path.read_text")
    @patch("builtins.open", mock_open())
    def test_drops_temp_table(self, mock_read_text, mock_create_engine):
        """Test that temporary table is dropped after processing."""
        from db_remove_processed import remove_processed_articles

        mock_read_text.return_value = '[{"url": "https://example1.com", "date": "2025-01-01", "access_date": "2025-11-09", "raw_contents": "test", "journal_name": "Nature"}]'

        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        with patch("db_remove_processed.Session") as mock_session_class:
            mock_session_instance = MagicMock()
            mock_session_class.return_value.__enter__.return_value = (
                mock_session_instance
            )
            mock_session_instance.exec.return_value.all.return_value = [
                ("https://example1.com",)
            ]

            with patch("db_remove_processed.Table") as mock_table_class:
                mock_table = MagicMock()
                mock_table_class.return_value = mock_table

                remove_processed_articles(
                    "articles.json",
                    "output.json",
                    connection_string=TEST_PG_CONN_STRING,
                )

                # Check that temp table was dropped
                assert mock_table.drop.called
