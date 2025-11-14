"""Tests for db_insert_article.py script."""

from unittest.mock import MagicMock, patch

import pytest

# Test connection string for PostgreSQL tests
TEST_PG_CONN_STRING = "postgresql://user:pass@localhost/db"  # pragma: allowlist secret


class TestInsertArticle:
    """Test insert_article function with SQLModel."""

    @patch("db_insert_article.create_engine")
    @patch("pathlib.Path.read_text")
    def test_inserts_single_article(self, mock_read_text, mock_create_engine):
        """Test that a single article is inserted."""
        from db_insert_article import insert_article

        mock_read_text.return_value = '[{"title": "Test Article", "summary": "Test summary", "url": "https://example.com", "journal": "Nature", "date": "2025-01-01", "access_date": "2025-11-09", "raw_contents": "test contents", "doi": "10.1234/test", "tags": ["test"], "reasoning": "test reason"}]'

        mock_engine = MagicMock()
        _ = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_engine.connect.return_value.__enter__.return_value = MagicMock()

        with patch("db_insert_article.Session") as mock_session_class:
            mock_session_instance = MagicMock()
            mock_session_class.return_value.__enter__.return_value = (
                mock_session_instance
            )

            insert_article("articles.json", connection_string=TEST_PG_CONN_STRING)

            # Check that add was called (for article and potentially related objects)
            assert mock_session_instance.add.called
            # Check that commit was called
            assert mock_session_instance.commit.called

    @patch("db_insert_article.create_engine")
    @patch("pathlib.Path.read_text")
    def test_inserts_multiple_articles(self, mock_read_text, mock_create_engine):
        """Test that multiple articles are inserted."""
        from db_insert_article import insert_article

        mock_read_text.return_value = '[{"title": "Article 1", "summary": "Summary 1", "url": "https://example1.com", "journal": "Nature", "date": "2025-01-01", "access_date": "2025-11-09", "raw_contents": "contents1", "doi": "10.1234/test1", "tags": ["test"], "reasoning": "reason1"}, {"title": "Article 2", "summary": "Summary 2", "url": "https://example2.com", "journal": "Science", "date": "2025-01-02", "access_date": "2025-11-09", "raw_contents": "contents2", "doi": "10.1234/test2", "tags": ["test"], "reasoning": "reason2"}]'

        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_engine.connect.return_value.__enter__.return_value = MagicMock()

        with patch("db_insert_article.Session") as mock_session_class:
            mock_session_instance = MagicMock()
            mock_session_class.return_value.__enter__.return_value = (
                mock_session_instance
            )

            insert_article("articles.json", connection_string=TEST_PG_CONN_STRING)

            # Check that add was called multiple times
            assert mock_session_instance.add.call_count >= 2
            assert mock_session_instance.commit.called

    @patch("db_insert_article.create_engine")
    @patch("pathlib.Path.read_text")
    def test_handles_null_fields(self, mock_read_text, mock_create_engine):
        """Test that null fields are handled correctly."""
        from db_insert_article import insert_article

        mock_read_text.return_value = '[{"title": "Test", "summary": "Summary", "url": "https://example.com", "journal": "Nature", "date": "2025-01-01", "access_date": "2025-11-09", "raw_contents": "test contents", "doi": null, "tags": null, "reasoning": null}]'

        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_engine.connect.return_value.__enter__.return_value = MagicMock()

        with patch("db_insert_article.Session") as mock_session_class:
            mock_session_instance = MagicMock()
            mock_session_class.return_value.__enter__.return_value = (
                mock_session_instance
            )

            insert_article("articles.json", connection_string=TEST_PG_CONN_STRING)

            assert mock_session_instance.add.called
            assert mock_session_instance.commit.called

    @patch("db_insert_article.create_engine")
    @patch("pathlib.Path.read_text")
    def test_error_handling(self, mock_read_text, mock_create_engine):
        """Test that errors are raised properly."""
        from db_insert_article import insert_article

        mock_read_text.return_value = '[{"title": "Test", "summary": "Summary", "url": "https://example.com", "journal": "Nature", "date": "2025-01-01", "access_date": "2025-11-09", "raw_contents": "test contents", "doi": "10.1234/test", "tags": ["test"], "reasoning": "reason"}]'

        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_engine.connect.return_value.__enter__.return_value = MagicMock()

        with patch("db_insert_article.Session") as mock_session_class:
            mock_session_instance = MagicMock()
            mock_session_instance.add.side_effect = Exception("Database error")
            mock_session_class.return_value.__enter__.return_value = (
                mock_session_instance
            )

            with pytest.raises(Exception):
                insert_article("articles.json", connection_string=TEST_PG_CONN_STRING)

    @patch("db_insert_article.create_engine")
    @patch("pathlib.Path.read_text")
    def test_handles_authors_and_tags(self, mock_read_text, mock_create_engine):
        """Test that articles with authors and tags are inserted correctly."""
        from db_insert_article import insert_article

        mock_read_text.return_value = '[{"title": "Test", "summary": "Summary", "url": "https://example.com", "journal": "Nature", "date": "2025-01-01", "access_date": "2025-11-09", "raw_contents": "test contents", "doi": "10.1234/test", "authors": [{"first_name": "John", "last_name": "Doe"}], "tags": ["genetics", "research"], "reasoning": "reason"}]'

        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_engine.connect.return_value.__enter__.return_value = MagicMock()

        with patch("db_insert_article.Session") as mock_session_class:
            mock_session_instance = MagicMock()
            mock_session_class.return_value.__enter__.return_value = (
                mock_session_instance
            )

            insert_article("articles.json", connection_string=TEST_PG_CONN_STRING)

            # Should add article and related objects
            assert mock_session_instance.add.called
            assert mock_session_instance.commit.called


class TestGetOrCreateFunctions:
    """Test get_or_create helper functions."""

    @patch("db_insert_article.select")
    def test_get_or_create_journal_existing(self, mock_select):
        """Test that existing journal is retrieved."""
        from db_insert_article import get_or_create_journal

        mock_session = MagicMock()
        mock_journal = MagicMock()
        mock_session.exec.return_value.first.return_value = mock_journal

        result = get_or_create_journal(mock_session, "Nature", "Nat")

        assert result == mock_journal
        assert not mock_session.add.called

    @patch("db_insert_article.select")
    def test_get_or_create_journal_new(self, mock_select):
        """Test that new journal is created."""
        from db_insert_article import get_or_create_journal

        mock_session = MagicMock()
        mock_session.exec.return_value.first.return_value = None

        result = get_or_create_journal(mock_session, "Nature", "Nat")

        assert mock_session.add.called
        assert result is not None

    @patch("db_insert_article.select")
    def test_get_or_create_author_existing(self, mock_select):
        """Test that existing author is retrieved."""
        from db_insert_article import get_or_create_author
        from common.models import Author

        mock_session = MagicMock()
        mock_author = MagicMock()
        mock_session.exec.return_value.first.return_value = mock_author

        author_data = Author(first_name="John", last_name="Doe")
        result = get_or_create_author(mock_session, author_data)

        assert result == mock_author
        assert not mock_session.add.called

    @patch("db_insert_article.select")
    def test_get_or_create_author_new(self, mock_select):
        """Test that new author is created."""
        from db_insert_article import get_or_create_author
        from common.models import Author

        mock_session = MagicMock()
        mock_session.exec.return_value.first.return_value = None

        author_data = Author(first_name="Jane", last_name="Smith")
        result = get_or_create_author(mock_session, author_data)

        assert mock_session.add.called
        assert result is not None

    @patch("db_insert_article.select")
    def test_get_or_create_tag_existing(self, mock_select):
        """Test that existing tag is retrieved."""
        from db_insert_article import get_or_create_tag

        mock_session = MagicMock()
        mock_tag = MagicMock()
        mock_session.exec.return_value.first.return_value = mock_tag

        result = get_or_create_tag(mock_session, "genetics")

        assert result == mock_tag
        assert not mock_session.add.called

    @patch("db_insert_article.select")
    def test_get_or_create_tag_new(self, mock_select):
        """Test that new tag is created."""
        from db_insert_article import get_or_create_tag

        mock_session = MagicMock()
        mock_session.exec.return_value.first.return_value = None

        result = get_or_create_tag(mock_session, "genetics")

        assert mock_session.add.called
        assert result is not None


class TestConvertArticleToTable:
    """Test convert_article_to_table function."""

    @patch("db_insert_article.get_or_create_journal")
    @patch("db_insert_article.get_or_create_author")
    @patch("db_insert_article.get_or_create_tag")
    def test_converts_article_with_all_fields(
        self, mock_get_tag, mock_get_author, mock_get_journal
    ):
        """Test conversion of article with all fields populated."""
        from db_insert_article import convert_article_to_table
        from common.models import Article, Author

        mock_session = MagicMock()
        mock_journal = MagicMock()
        mock_author = MagicMock()
        mock_tag = MagicMock()

        mock_get_journal.return_value = mock_journal
        mock_get_author.return_value = mock_author
        mock_get_tag.return_value = mock_tag

        article = Article(
            title="Test",
            summary="Summary",
            url="https://example.com",
            journal="Nature",
            journal_short_name="Nat",
            date="2025-01-01",
            access_date="2025-11-09",
            raw_contents="test contents",
            doi="10.1234/test",
            authors=[Author(first_name="John", last_name="Doe")],
            tags=["genetics", "research"],
            reasoning="test reason",
        )

        result = convert_article_to_table(article, mock_session)

        assert result is not None
        mock_get_journal.assert_called_once_with(mock_session, "Nature", "Nat")
        mock_get_author.assert_called_once()
        assert mock_get_tag.call_count == 2

    @patch("db_insert_article.get_or_create_journal")
    def test_converts_article_without_optional_fields(self, mock_get_journal):
        """Test conversion of article without optional fields."""
        from db_insert_article import convert_article_to_table
        from common.models import Article

        mock_session = MagicMock()
        mock_journal = MagicMock()
        mock_get_journal.return_value = mock_journal

        article = Article(
            title="Test",
            summary="Summary",
            url="https://example.com",
            journal="Nature",
            date="2025-01-01",
            access_date="2025-11-09",
            raw_contents="test contents",
        )

        result = convert_article_to_table(article, mock_session)

        assert result is not None
        mock_get_journal.assert_called_once_with(mock_session, "Nature", None)
