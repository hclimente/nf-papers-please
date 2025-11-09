#!/usr/bin/env python
"""Tests for llm_embed_articles.py"""

import json
import sys
from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add the parent directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm_embed_articles import prepare_text_to_embed, llm_process_articles
from common.models import Article, Author


class TestPrepareTextToEmbed:
    """Test suite for prepare_text_to_embed function"""

    @pytest.fixture
    def basic_article(self):
        """Create a basic article for testing"""
        return Article(
            title="Test Article Title",
            url="https://example.com/article",
            journal_name="Test Journal",
            date=date(2024, 1, 1),
            access_date=date(2024, 1, 15),
            raw_contents="Raw content",
            summary="This is a test summary of the article.",
            authors=[
                Author(first_name="John", last_name="Doe"),
                Author(first_name="Jane", last_name="Smith"),
            ],
            tags=["tag1", "tag2", "tag3"],
        )

    def test_prepare_text_with_all_fields(self, basic_article):
        """Test preparing text with all fields populated"""
        result = prepare_text_to_embed(basic_article)

        assert "Title: Test Article Title" in result
        assert "Journal: Test Journal" in result
        assert "First Author:" in result
        assert "John Doe" in result.replace("\n", " ")  # Author formatting may vary
        assert "Last Author:" in result
        assert "Jane Smith" in result.replace("\n", " ")
        assert "Summary: This is a test summary of the article." in result
        assert "Tags: tag1, tag2, tag3" in result

    def test_prepare_text_without_authors(self):
        """Test preparing text when article has no authors"""
        article = Article(
            title="No Author Article",
            url="https://example.com/article",
            journal_name="Test Journal",
            date=date(2024, 1, 1),
            access_date=date(2024, 1, 15),
            raw_contents="Raw content",
            summary="Summary without authors",
            authors=None,
        )

        result = prepare_text_to_embed(article)

        assert "First Author: N/A" in result
        assert "Last Author: N/A" in result

    def test_prepare_text_with_empty_authors_list(self):
        """Test preparing text when article has empty authors list"""
        article = Article(
            title="Empty Authors Article",
            url="https://example.com/article",
            journal_name="Test Journal",
            date=date(2024, 1, 1),
            access_date=date(2024, 1, 15),
            raw_contents="Raw content",
            summary="Summary with empty authors",
            authors=[],
        )

        result = prepare_text_to_embed(article)

        assert "First Author: N/A" in result
        assert "Last Author: N/A" in result

    def test_prepare_text_without_tags(self):
        """Test preparing text when article has no tags"""
        article = Article(
            title="No Tags Article",
            url="https://example.com/article",
            journal_name="Test Journal",
            date=date(2024, 1, 1),
            access_date=date(2024, 1, 15),
            raw_contents="Raw content",
            summary="Summary without tags",
            authors=[Author(first_name="John", last_name="Doe")],
            tags=None,
        )

        result = prepare_text_to_embed(article)

        assert "Tags: N/A" in result

    def test_prepare_text_with_empty_tags_list(self):
        """Test preparing text when article has empty tags list"""
        article = Article(
            title="Empty Tags Article",
            url="https://example.com/article",
            journal_name="Test Journal",
            date=date(2024, 1, 1),
            access_date=date(2024, 1, 15),
            raw_contents="Raw content",
            summary="Summary with empty tags",
            authors=[Author(first_name="John", last_name="Doe")],
            tags=[],
        )

        result = prepare_text_to_embed(article)

        assert "Tags: N/A" in result

    def test_prepare_text_with_single_author(self):
        """Test preparing text when article has single author"""
        article = Article(
            title="Single Author Article",
            url="https://example.com/article",
            journal_name="Test Journal",
            date=date(2024, 1, 1),
            access_date=date(2024, 1, 15),
            raw_contents="Raw content",
            summary="Summary with single author",
            authors=[Author(first_name="John", last_name="Doe")],
        )

        result = prepare_text_to_embed(article)

        # First and last author should be the same
        assert "First Author:" in result
        assert "Last Author:" in result
        assert result.count("John Doe") >= 2 or "Doe" in result

    def test_prepare_text_with_institutional_author(self):
        """Test preparing text with institutional authors"""
        article = Article(
            title="Institutional Author Article",
            url="https://example.com/article",
            journal_name="Test Journal",
            date=date(2024, 1, 1),
            access_date=date(2024, 1, 15),
            raw_contents="Raw content",
            summary="Summary with institutional author",
            authors=[
                Author(last_name="World Health Organization"),
                Author(first_name="John", last_name="Doe"),
            ],
        )

        result = prepare_text_to_embed(article)

        assert "Title: Institutional Author Article" in result
        # The institutional author should be formatted somehow
        assert "First Author:" in result
        assert "Last Author:" in result

    def test_prepare_text_with_long_summary(self):
        """Test preparing text with a very long summary"""
        long_summary = "A" * 1000
        article = Article(
            title="Long Summary Article",
            url="https://example.com/article",
            journal_name="Test Journal",
            date=date(2024, 1, 1),
            access_date=date(2024, 1, 15),
            raw_contents="Raw content",
            summary=long_summary,
            authors=[Author(first_name="John", last_name="Doe")],
        )

        result = prepare_text_to_embed(article)

        assert long_summary in result

    def test_prepare_text_with_special_characters(self):
        """Test preparing text with special characters"""
        article = Article(
            title="Special Characters: Test & Symbols",
            url="https://example.com/article",
            journal_name="Test Journal™",
            date=date(2024, 1, 1),
            access_date=date(2024, 1, 15),
            raw_contents="Raw content",
            summary="Summary with €, £, ¥ symbols",
            authors=[Author(first_name="José", last_name="O'Brien")],
            tags=["tag-1", "tag_2", "tag.3"],
        )

        result = prepare_text_to_embed(article)

        assert "Special Characters: Test & Symbols" in result
        assert "Test Journal™" in result
        assert "€, £, ¥" in result

    def test_prepare_text_with_multiple_tags(self):
        """Test preparing text with many tags"""
        article = Article(
            title="Many Tags Article",
            url="https://example.com/article",
            journal_name="Test Journal",
            date=date(2024, 1, 1),
            access_date=date(2024, 1, 15),
            raw_contents="Raw content",
            summary="Summary with many tags",
            authors=[Author(first_name="John", last_name="Doe")],
            tags=["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"],
        )

        result = prepare_text_to_embed(article)

        assert "tag1, tag2, tag3, tag4, tag5, tag6" in result

    def test_prepare_text_returns_string(self, basic_article):
        """Test that prepare_text_to_embed returns a string"""
        result = prepare_text_to_embed(basic_article)
        assert isinstance(result, str)

    def test_prepare_text_not_empty(self, basic_article):
        """Test that prepared text is not empty"""
        result = prepare_text_to_embed(basic_article)
        assert len(result) > 0


class TestLlmProcessArticles:
    """Test suite for llm_process_articles function"""

    @pytest.fixture
    def sample_articles(self):
        """Create sample articles for testing"""
        return [
            Article(
                title="Test Article 1",
                url="https://example.com/article1",
                journal_name="Test Journal",
                date=date(2024, 1, 1),
                access_date=date(2024, 1, 15),
                raw_contents="Content 1",
                summary="Summary 1",
                authors=[Author(first_name="John", last_name="Doe")],
                tags=["tag1"],
            ),
            Article(
                title="Test Article 2",
                url="https://example.com/article2",
                journal_name="Test Journal",
                date=date(2024, 1, 2),
                access_date=date(2024, 1, 15),
                raw_contents="Content 2",
                summary="Summary 2",
                authors=[Author(first_name="Jane", last_name="Smith")],
                tags=["tag2"],
            ),
        ]

    @pytest.fixture
    def articles_json_file(self, tmp_path, sample_articles):
        """Create a temporary JSON file with articles"""
        from common.models import pprint

        json_file = tmp_path / "articles.json"
        json_file.write_text(pprint(sample_articles))
        return str(json_file)

    @pytest.fixture
    def mock_embeddings(self):
        """Create mock embeddings"""
        mock_emb1 = Mock()
        mock_emb1.values = [0.1, 0.2, 0.3]
        mock_emb2 = Mock()
        mock_emb2.values = [0.4, 0.5, 0.6]
        return [mock_emb1, mock_emb2]

    @patch("llm_embed_articles.embed")
    @patch("llm_embed_articles.get_env_variable")
    def test_llm_process_articles_basic(
        self, mock_get_env, mock_embed, articles_json_file, mock_embeddings, tmp_path
    ):
        """Test basic functionality of llm_process_articles"""
        mock_get_env.return_value = "fake-api-key"
        mock_embed.return_value = mock_embeddings

        out_file = tmp_path / "output.json"

        llm_process_articles(
            articles_json=articles_json_file,
            model="gemini-embedding-001",
            task="CLASSIFICATION",
            out=str(out_file),
            debug=False,
        )

        # Verify embed was called
        mock_embed.assert_called_once()
        call_kwargs = mock_embed.call_args.kwargs
        assert call_kwargs["model"] == "gemini-embedding-001"
        assert call_kwargs["api_key"] == "fake-api-key"  # pragma: allowlist secret
        assert call_kwargs["task"] == "CLASSIFICATION"
        assert len(call_kwargs["texts"]) == 2

        # Verify output file was created
        assert out_file.exists()

        # Verify output contains embeddings
        output_content = out_file.read_text()
        assert "embedding" in output_content
        assert "0.1" in output_content or "[0.1, 0.2, 0.3]" in output_content

    @patch("llm_embed_articles.embed")
    @patch("llm_embed_articles.get_env_variable")
    def test_llm_process_articles_calls_prepare_text(
        self, mock_get_env, mock_embed, articles_json_file, mock_embeddings, tmp_path
    ):
        """Test that llm_process_articles calls prepare_text_to_embed for each article"""
        mock_get_env.return_value = "fake-api-key"
        mock_embed.return_value = mock_embeddings

        out_file = tmp_path / "output.json"

        llm_process_articles(
            articles_json=articles_json_file,
            model="gemini-embedding-001",
            task="CLASSIFICATION",
            out=str(out_file),
            debug=False,
        )

        # Verify texts passed to embed contain expected content
        call_kwargs = mock_embed.call_args.kwargs
        texts = call_kwargs["texts"]
        assert "Test Article 1" in texts[0]
        assert "Test Article 2" in texts[1]
        assert "Summary 1" in texts[0]
        assert "Summary 2" in texts[1]

    @patch("llm_embed_articles.embed")
    @patch("llm_embed_articles.get_env_variable")
    def test_llm_process_articles_with_debug(
        self, mock_get_env, mock_embed, articles_json_file, mock_embeddings, tmp_path
    ):
        """Test llm_process_articles with debug mode enabled"""
        mock_get_env.return_value = "fake-api-key"
        mock_embed.return_value = mock_embeddings

        out_file = tmp_path / "output.json"

        llm_process_articles(
            articles_json=articles_json_file,
            model="gemini-embedding-001",
            task="CLASSIFICATION",
            out=str(out_file),
            debug=True,
        )

        # Should still work with debug=True
        assert out_file.exists()

    @patch("llm_embed_articles.embed")
    @patch("llm_embed_articles.get_env_variable")
    def test_llm_process_articles_different_models(
        self, mock_get_env, mock_embed, articles_json_file, mock_embeddings, tmp_path
    ):
        """Test llm_process_articles with different models"""
        mock_get_env.return_value = "fake-api-key"
        mock_embed.return_value = mock_embeddings

        out_file = tmp_path / "output.json"

        for model in ["gemini-embedding-001", "text-embedding-004"]:
            llm_process_articles(
                articles_json=articles_json_file,
                model=model,
                task="CLASSIFICATION",
                out=str(out_file),
                debug=False,
            )

            # Verify correct model was passed
            call_kwargs = mock_embed.call_args.kwargs
            assert call_kwargs["model"] == model

    @patch("llm_embed_articles.embed")
    @patch("llm_embed_articles.get_env_variable")
    def test_llm_process_articles_different_tasks(
        self, mock_get_env, mock_embed, articles_json_file, mock_embeddings, tmp_path
    ):
        """Test llm_process_articles with different tasks"""
        mock_get_env.return_value = "fake-api-key"
        mock_embed.return_value = mock_embeddings

        out_file = tmp_path / "output.json"

        tasks = [
            "SEMANTIC_SIMILARITY",
            "CLASSIFICATION",
            "CLUSTERING",
            "RETRIEVAL_DOCUMENT",
        ]

        for task in tasks:
            llm_process_articles(
                articles_json=articles_json_file,
                model="gemini-embedding-001",
                task=task,
                out=str(out_file),
                debug=False,
            )

            # Verify correct task was passed
            call_kwargs = mock_embed.call_args.kwargs
            assert call_kwargs["task"] == task

    @patch("llm_embed_articles.embed")
    @patch("llm_embed_articles.get_env_variable")
    def test_llm_process_articles_empty_list(self, mock_get_env, mock_embed, tmp_path):
        """Test llm_process_articles with empty articles list"""
        mock_get_env.return_value = "fake-api-key"
        mock_embed.return_value = []

        from common.models import pprint

        json_file = tmp_path / "empty_articles.json"
        json_file.write_text(pprint([]))
        out_file = tmp_path / "output.json"

        llm_process_articles(
            articles_json=str(json_file),
            model="gemini-embedding-001",
            task="CLASSIFICATION",
            out=str(out_file),
            debug=False,
        )

        # Verify embed was called with empty list
        mock_embed.assert_called_once()
        call_kwargs = mock_embed.call_args.kwargs
        assert call_kwargs["texts"] == []

    @patch("llm_embed_articles.embed")
    @patch("llm_embed_articles.get_env_variable")
    def test_llm_process_articles_sets_embedding_attribute(
        self, mock_get_env, mock_embed, articles_json_file, mock_embeddings, tmp_path
    ):
        """Test that embeddings are correctly set on articles"""
        mock_get_env.return_value = "fake-api-key"
        mock_embed.return_value = mock_embeddings

        out_file = tmp_path / "output.json"

        llm_process_articles(
            articles_json=articles_json_file,
            model="gemini-embedding-001",
            task="CLASSIFICATION",
            out=str(out_file),
            debug=False,
        )

        # Load output and verify embeddings are present
        from common.models import ArticleList

        output_content = out_file.read_text()
        articles = ArticleList.validate_json(output_content)

        assert len(articles) == 2
        assert articles[0].embedding == [0.1, 0.2, 0.3]
        assert articles[1].embedding == [0.4, 0.5, 0.6]

    @patch("llm_embed_articles.get_env_variable")
    def test_llm_process_articles_missing_api_key(
        self, mock_get_env, articles_json_file, tmp_path
    ):
        """Test that missing API key raises appropriate error"""
        mock_get_env.return_value = None

        out_file = tmp_path / "output.json"

        # This should raise an error when embed() is called
        with pytest.raises(Exception):
            llm_process_articles(
                articles_json=articles_json_file,
                model="gemini-embedding-001",
                task="CLASSIFICATION",
                out=str(out_file),
                debug=False,
            )

    def test_llm_process_articles_invalid_json_file(self, tmp_path):
        """Test with invalid JSON file"""
        invalid_json_file = tmp_path / "invalid.json"
        invalid_json_file.write_text("not valid json")

        out_file = tmp_path / "output.json"

        with pytest.raises(Exception):
            llm_process_articles(
                articles_json=str(invalid_json_file),
                model="gemini-embedding-001",
                task="CLASSIFICATION",
                out=str(out_file),
                debug=False,
            )

    def test_llm_process_articles_nonexistent_file(self):
        """Test with nonexistent input file"""
        with pytest.raises(FileNotFoundError):
            llm_process_articles(
                articles_json="/nonexistent/file.json",
                model="gemini-embedding-001",
                task="CLASSIFICATION",
                out="/tmp/output.json",
                debug=False,
            )

    @patch("llm_embed_articles.embed")
    @patch("llm_embed_articles.get_env_variable")
    def test_llm_process_articles_output_file_format(
        self, mock_get_env, mock_embed, articles_json_file, mock_embeddings, tmp_path
    ):
        """Test that output file is properly formatted JSON"""
        mock_get_env.return_value = "fake-api-key"
        mock_embed.return_value = mock_embeddings

        out_file = tmp_path / "output.json"

        llm_process_articles(
            articles_json=articles_json_file,
            model="gemini-embedding-001",
            task="CLASSIFICATION",
            out=str(out_file),
            debug=False,
        )

        # Verify output is valid JSON
        output_content = out_file.read_text()
        parsed = json.loads(output_content)
        assert isinstance(parsed, list)
        assert len(parsed) == 2

    @patch("llm_embed_articles.embed")
    @patch("llm_embed_articles.get_env_variable")
    def test_llm_process_articles_preserves_article_data(
        self, mock_get_env, mock_embed, articles_json_file, mock_embeddings, tmp_path
    ):
        """Test that original article data is preserved in output"""
        mock_get_env.return_value = "fake-api-key"
        mock_embed.return_value = mock_embeddings

        out_file = tmp_path / "output.json"

        llm_process_articles(
            articles_json=articles_json_file,
            model="gemini-embedding-001",
            task="CLASSIFICATION",
            out=str(out_file),
            debug=False,
        )

        # Load output and verify original data is intact
        from common.models import ArticleList

        output_content = out_file.read_text()
        articles = ArticleList.validate_json(output_content)

        assert articles[0].title == "Test Article 1"
        assert str(articles[0].url) == "https://example.com/article1"
        assert articles[0].summary == "Summary 1"
        assert articles[1].title == "Test Article 2"
        assert str(articles[1].url) == "https://example.com/article2"
        assert articles[1].summary == "Summary 2"

    @patch("llm_embed_articles.embed")
    @patch("llm_embed_articles.get_env_variable")
    def test_llm_process_articles_logs_info(
        self,
        mock_get_env,
        mock_embed,
        articles_json_file,
        mock_embeddings,
        tmp_path,
        caplog,
    ):
        """Test that function logs appropriate information"""
        import logging

        caplog.set_level(logging.INFO)
        mock_get_env.return_value = "fake-api-key"
        mock_embed.return_value = mock_embeddings

        out_file = tmp_path / "output.json"

        llm_process_articles(
            articles_json=articles_json_file,
            model="gemini-embedding-001",
            task="CLASSIFICATION",
            out=str(out_file),
            debug=False,
        )

        # Check that logging occurred
        assert "llm_process_articles called" in caplog.text
        assert "Loaded 2 articles" in caplog.text

    @patch("llm_embed_articles.embed")
    @patch("llm_embed_articles.get_env_variable")
    def test_llm_process_articles_with_single_article(
        self, mock_get_env, mock_embed, tmp_path
    ):
        """Test processing a single article"""
        mock_get_env.return_value = "fake-api-key"

        single_embedding = Mock()
        single_embedding.values = [0.1, 0.2, 0.3]
        mock_embed.return_value = [single_embedding]

        from common.models import pprint

        single_article = [
            Article(
                title="Single Article",
                url="https://example.com/article",
                journal_name="Test Journal",
                date=date(2024, 1, 1),
                access_date=date(2024, 1, 15),
                raw_contents="Content",
                summary="Summary",
                authors=[Author(first_name="John", last_name="Doe")],
            )
        ]

        json_file = tmp_path / "single_article.json"
        json_file.write_text(pprint(single_article))
        out_file = tmp_path / "output.json"

        llm_process_articles(
            articles_json=str(json_file),
            model="gemini-embedding-001",
            task="CLASSIFICATION",
            out=str(out_file),
            debug=False,
        )

        # Verify output
        from common.models import ArticleList

        output_content = out_file.read_text()
        articles = ArticleList.validate_json(output_content)

        assert len(articles) == 1
        assert articles[0].embedding == [0.1, 0.2, 0.3]
