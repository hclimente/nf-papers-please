#!/usr/bin/env python
"""Tests for zotero_fetch_articles.py"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add the parent directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.models import ArticleList
from zotero_fetch_articles import fetch_articles


class TestFetchArticles:
    """Test suite for fetch_articles function"""

    @pytest.fixture
    def mock_zotero_items(self):
        """Mock Zotero collection items with various types"""
        return [
            {
                "key": "ITEM001",
                "data": {
                    "itemType": "journalArticle",
                    "title": "Sample Article 1",
                    "url": "https://doi.org/10.1234/article1",
                    "DOI": "10.1234/article1",
                    "abstractNote": "This is the abstract for article 1.",
                    "date": "2024-01-15",
                    "publicationTitle": "Nature",
                    "creators": [
                        {
                            "firstName": "John",
                            "lastName": "Doe",
                            "creatorType": "author",
                        },
                        {
                            "firstName": "Jane",
                            "lastName": "Smith",
                            "creatorType": "author",
                        },
                    ],
                },
            },
            {
                "key": "ITEM002",
                "data": {
                    "itemType": "journalArticle",
                    "title": "Sample Article 2",
                    "url": "https://example.com/article2",
                    "DOI": "10.5678/article2",
                    "abstractNote": "This is the abstract for article 2.",
                    "date": "2024-02-10",
                    "publicationTitle": "Science",
                    "creators": [
                        {
                            "firstName": "Alice",
                            "lastName": "Brown",
                            "creatorType": "author",
                        },
                    ],
                },
            },
            {
                "key": "NOTE001",
                "data": {
                    "itemType": "note",  # Not a journal article
                    "note": "This is a note, not an article.",
                },
            },
            {
                "key": "BOOK001",
                "data": {
                    "itemType": "book",  # Not a journal article
                    "title": "Some Book",
                },
            },
        ]

    @pytest.fixture
    def mock_zotero_journal_articles(self, mock_zotero_items):
        """Only the journal articles from mock_zotero_items"""
        return [
            item
            for item in mock_zotero_items
            if item.get("data", {}).get("itemType") == "journalArticle"
        ]

    def test_fetches_articles_from_zotero_collection(self, mock_zotero_items, tmp_path):
        """Test basic functionality of fetching articles from Zotero"""
        output_file = tmp_path / "output.json"

        with (
            patch("zotero_fetch_articles.zotero.Zotero") as mock_zotero_class,
            patch("zotero_fetch_articles.get_env_variable") as mock_get_env,
        ):
            # Setup mocks
            mock_get_env.return_value = "fake_api_key"
            mock_zot_instance = MagicMock()
            mock_zot_instance.collection_items.return_value = mock_zotero_items
            mock_zotero_class.return_value = mock_zot_instance

            # Execute
            fetch_articles(
                zotero_user_id="12345",
                zotero_library_type="user",
                zotero_collection_id="ABC123",
                output=str(output_file),
            )

            # Verify Zotero client was initialized correctly
            mock_zotero_class.assert_called_once_with("12345", "user", "fake_api_key")

            # Verify collection_items was called
            mock_zot_instance.collection_items.assert_called_once_with("ABC123")

            # Verify output file was created
            assert output_file.exists()

    def test_filters_only_journal_articles(self, mock_zotero_items, tmp_path):
        """Test that only journal articles are processed, not notes or books"""
        output_file = tmp_path / "output.json"

        with (
            patch("zotero_fetch_articles.zotero.Zotero") as mock_zotero_class,
            patch("zotero_fetch_articles.get_env_variable") as mock_get_env,
        ):
            mock_get_env.return_value = "fake_api_key"
            mock_zot_instance = MagicMock()
            mock_zot_instance.collection_items.return_value = mock_zotero_items
            mock_zotero_class.return_value = mock_zot_instance

            fetch_articles(
                zotero_user_id="12345",
                zotero_library_type="user",
                zotero_collection_id="ABC123",
                output=str(output_file),
            )

            # Read and validate output
            with open(output_file, "r") as f:
                content = f.read()
                articles = ArticleList.validate_json(content)

            # Should only have 2 journal articles (not the note or book)
            assert len(articles) == 2
            assert all(
                article.title.startswith("Sample Article") for article in articles
            )

    def test_converts_zotero_items_to_article_objects(
        self, mock_zotero_items, tmp_path
    ):
        """Test that Zotero items are properly converted to Article objects"""
        output_file = tmp_path / "output.json"

        with (
            patch("zotero_fetch_articles.zotero.Zotero") as mock_zotero_class,
            patch("zotero_fetch_articles.get_env_variable") as mock_get_env,
        ):
            mock_get_env.return_value = "fake_api_key"
            mock_zot_instance = MagicMock()
            mock_zot_instance.collection_items.return_value = mock_zotero_items
            mock_zotero_class.return_value = mock_zot_instance

            fetch_articles(
                zotero_user_id="12345",
                zotero_library_type="user",
                zotero_collection_id="ABC123",
                output=str(output_file),
            )

            # Read and validate output
            with open(output_file, "r") as f:
                content = f.read()
                articles = ArticleList.validate_json(content)

            # Verify first article
            article1 = articles[0]
            assert article1.title == "Sample Article 1"
            assert article1.url == "https://doi.org/10.1234/article1"
            assert article1.doi == "10.1234/article1"
            assert article1.summary == "This is the abstract for article 1."
            assert article1.journal == "Nature"
            assert len(article1.authors) == 2
            assert article1.authors[0].first_name == "John"
            assert article1.authors[0].last_name == "Doe"

            # Verify second article
            article2 = articles[1]
            assert article2.title == "Sample Article 2"
            assert len(article2.authors) == 1

    def test_handles_empty_collection(self, tmp_path):
        """Test behavior when Zotero collection is empty"""
        output_file = tmp_path / "output.json"

        with (
            patch("zotero_fetch_articles.zotero.Zotero") as mock_zotero_class,
            patch("zotero_fetch_articles.get_env_variable") as mock_get_env,
        ):
            mock_get_env.return_value = "fake_api_key"
            mock_zot_instance = MagicMock()
            mock_zot_instance.collection_items.return_value = []
            mock_zotero_class.return_value = mock_zot_instance

            fetch_articles(
                zotero_user_id="12345",
                zotero_library_type="user",
                zotero_collection_id="ABC123",
                output=str(output_file),
            )

            # Output file should not be created when no articles
            assert not output_file.exists()

    def test_handles_collection_with_no_journal_articles(self, tmp_path):
        """Test behavior when collection has items but no journal articles"""
        output_file = tmp_path / "output.json"

        non_journal_items = [
            {
                "key": "NOTE001",
                "data": {
                    "itemType": "note",
                    "note": "This is a note.",
                },
            },
            {
                "key": "BOOK001",
                "data": {
                    "itemType": "book",
                    "title": "Some Book",
                },
            },
        ]

        with (
            patch("zotero_fetch_articles.zotero.Zotero") as mock_zotero_class,
            patch("zotero_fetch_articles.get_env_variable") as mock_get_env,
        ):
            mock_get_env.return_value = "fake_api_key"
            mock_zot_instance = MagicMock()
            mock_zot_instance.collection_items.return_value = non_journal_items
            mock_zotero_class.return_value = mock_zot_instance

            fetch_articles(
                zotero_user_id="12345",
                zotero_library_type="user",
                zotero_collection_id="ABC123",
                output=str(output_file),
            )

            # Output file should not be created when no journal articles
            assert not output_file.exists()

    def test_uses_group_library_type(self, mock_zotero_items, tmp_path):
        """Test that group library type is passed correctly to Zotero client"""
        output_file = tmp_path / "output.json"

        with (
            patch("zotero_fetch_articles.zotero.Zotero") as mock_zotero_class,
            patch("zotero_fetch_articles.get_env_variable") as mock_get_env,
        ):
            mock_get_env.return_value = "fake_api_key"
            mock_zot_instance = MagicMock()
            mock_zot_instance.collection_items.return_value = mock_zotero_items
            mock_zotero_class.return_value = mock_zot_instance

            fetch_articles(
                zotero_user_id="99999",
                zotero_library_type="group",
                zotero_collection_id="XYZ789",
                output=str(output_file),
            )

            # Verify group library type was used
            mock_zotero_class.assert_called_once_with("99999", "group", "fake_api_key")

    def test_retrieves_api_key_from_environment(self, mock_zotero_items, tmp_path):
        """Test that Zotero API key is retrieved from environment variable"""
        output_file = tmp_path / "output.json"

        with (
            patch("zotero_fetch_articles.zotero.Zotero") as mock_zotero_class,
            patch("zotero_fetch_articles.get_env_variable") as mock_get_env,
        ):
            mock_get_env.return_value = "secret_key_12345"
            mock_zot_instance = MagicMock()
            mock_zot_instance.collection_items.return_value = mock_zotero_items
            mock_zotero_class.return_value = mock_zot_instance

            fetch_articles(
                zotero_user_id="12345",
                zotero_library_type="user",
                zotero_collection_id="ABC123",
                output=str(output_file),
            )

            # Verify API key was retrieved and used
            mock_get_env.assert_called_once_with("ZOTERO_API_KEY")
            mock_zotero_class.assert_called_once_with(
                "12345", "user", "secret_key_12345"
            )

    def test_logs_collection_statistics(self, mock_zotero_items, tmp_path, caplog):
        """Test that the function logs statistics about retrieved items"""
        output_file = tmp_path / "output.json"

        with (
            patch("zotero_fetch_articles.zotero.Zotero") as mock_zotero_class,
            patch("zotero_fetch_articles.get_env_variable") as mock_get_env,
        ):
            mock_get_env.return_value = "fake_api_key"
            mock_zot_instance = MagicMock()
            mock_zot_instance.collection_items.return_value = mock_zotero_items
            mock_zotero_class.return_value = mock_zot_instance

            with caplog.at_level("INFO"):
                fetch_articles(
                    zotero_user_id="12345",
                    zotero_library_type="user",
                    zotero_collection_id="ABC123",
                    output=str(output_file),
                )

            # Check that statistics were logged
            log_text = caplog.text
            assert "Retrieved 4 items from Zotero collection" in log_text
            assert "Found 2 journal articles" in log_text

    def test_logs_parameters(self, mock_zotero_items, tmp_path, caplog):
        """Test that the function logs input parameters"""
        output_file = tmp_path / "output.json"

        with (
            patch("zotero_fetch_articles.zotero.Zotero") as mock_zotero_class,
            patch("zotero_fetch_articles.get_env_variable") as mock_get_env,
        ):
            mock_get_env.return_value = "fake_api_key"
            mock_zot_instance = MagicMock()
            mock_zot_instance.collection_items.return_value = mock_zotero_items
            mock_zotero_class.return_value = mock_zot_instance

            with caplog.at_level("INFO"):
                fetch_articles(
                    zotero_user_id="TEST123",
                    zotero_library_type="group",
                    zotero_collection_id="COLL456",
                    output=str(output_file),
                )

            # Check that parameters were logged
            log_text = caplog.text
            assert "zotero_user_id       : TEST123" in log_text
            assert "zotero_library_type  : group" in log_text
            assert "zotero_collection_id : COLL456" in log_text
            assert f"output               : {output_file}" in log_text

    def test_writes_pretty_printed_json(self, mock_zotero_items, tmp_path):
        """Test that output JSON is properly formatted"""
        output_file = tmp_path / "output.json"

        with (
            patch("zotero_fetch_articles.zotero.Zotero") as mock_zotero_class,
            patch("zotero_fetch_articles.get_env_variable") as mock_get_env,
        ):
            mock_get_env.return_value = "fake_api_key"
            mock_zot_instance = MagicMock()
            mock_zot_instance.collection_items.return_value = mock_zotero_items
            mock_zotero_class.return_value = mock_zot_instance

            fetch_articles(
                zotero_user_id="12345",
                zotero_library_type="user",
                zotero_collection_id="ABC123",
                output=str(output_file),
            )

            # Read the output file
            with open(output_file, "r") as f:
                content = f.read()

            # Verify it's valid JSON
            articles = ArticleList.validate_json(content)
            assert len(articles) == 2

            # Verify it's pretty-printed (has indentation)
            assert "\n" in content
            assert "  " in content  # Has indentation

    def test_handles_single_article(self, tmp_path):
        """Test handling when collection has exactly one journal article"""
        output_file = tmp_path / "output.json"

        single_item = [
            {
                "key": "ITEM001",
                "data": {
                    "itemType": "journalArticle",
                    "title": "Single Article",
                    "url": "https://example.com/article",
                    "DOI": "10.1234/single",
                    "abstractNote": "Single article abstract.",
                    "date": "2024-01-01",
                    "publicationTitle": "Test Journal",
                    "creators": [],
                },
            }
        ]

        with (
            patch("zotero_fetch_articles.zotero.Zotero") as mock_zotero_class,
            patch("zotero_fetch_articles.get_env_variable") as mock_get_env,
        ):
            mock_get_env.return_value = "fake_api_key"
            mock_zot_instance = MagicMock()
            mock_zot_instance.collection_items.return_value = single_item
            mock_zotero_class.return_value = mock_zot_instance

            fetch_articles(
                zotero_user_id="12345",
                zotero_library_type="user",
                zotero_collection_id="ABC123",
                output=str(output_file),
            )

            # Verify output
            with open(output_file, "r") as f:
                content = f.read()
                articles = ArticleList.validate_json(content)

            assert len(articles) == 1
            assert articles[0].title == "Single Article"

    def test_raises_error_on_missing_api_key(self, mock_zotero_items, tmp_path):
        """Test that missing API key raises appropriate error"""
        output_file = tmp_path / "output.json"

        with (
            patch("zotero_fetch_articles.zotero.Zotero") as _,
            patch("zotero_fetch_articles.get_env_variable") as mock_get_env,
        ):
            # Simulate missing API key
            mock_get_env.side_effect = ValueError("ZOTERO_API_KEY not found")

            with pytest.raises(ValueError, match="ZOTERO_API_KEY not found"):
                fetch_articles(
                    zotero_user_id="12345",
                    zotero_library_type="user",
                    zotero_collection_id="ABC123",
                    output=str(output_file),
                )

    def test_preserves_article_metadata(self, tmp_path):
        """Test that all article metadata is preserved through the conversion"""
        output_file = tmp_path / "output.json"

        detailed_item = [
            {
                "key": "ITEM001",
                "data": {
                    "itemType": "journalArticle",
                    "title": "Detailed Article",
                    "url": "https://doi.org/10.9999/detailed",
                    "DOI": "10.9999/detailed",
                    "abstractNote": "Comprehensive abstract with details.",
                    "date": "2024-03-15",
                    "publicationTitle": "Advanced Science",
                    "volume": "42",
                    "issue": "3",
                    "pages": "123-145",
                    "language": "en",
                    "creators": [
                        {
                            "firstName": "Maria",
                            "lastName": "Garcia",
                            "creatorType": "author",
                        },
                        {"name": "Research Institute", "creatorType": "author"},
                    ],
                },
            }
        ]

        with (
            patch("zotero_fetch_articles.zotero.Zotero") as mock_zotero_class,
            patch("zotero_fetch_articles.get_env_variable") as mock_get_env,
        ):
            mock_get_env.return_value = "fake_api_key"
            mock_zot_instance = MagicMock()
            mock_zot_instance.collection_items.return_value = detailed_item
            mock_zotero_class.return_value = mock_zot_instance

            fetch_articles(
                zotero_user_id="12345",
                zotero_library_type="user",
                zotero_collection_id="ABC123",
                output=str(output_file),
            )

            # Verify all metadata was preserved
            with open(output_file, "r") as f:
                content = f.read()
                articles = ArticleList.validate_json(content)

            article = articles[0]
            assert article.title == "Detailed Article"
            assert article.doi == "10.9999/detailed"
            assert article.summary == "Comprehensive abstract with details."
            assert article.journal == "Advanced Science"
            assert article.volume == 42
            assert article.issue == 3
            assert article.language == "en"
            assert len(article.authors) == 2
            assert article.authors[0].first_name == "Maria"
            assert article.authors[1].first_name is None  # Institutional author


# Note: CLI argument parsing tests are not included here because they would require
# importing and executing the __main__ block, which is difficult to test in isolation.
# The argparse setup is straightforward and follows the same pattern as other scripts
# in this project, so the risk of bugs is low. Manual testing of CLI arguments is
# recommended when making changes to the argument parser.
