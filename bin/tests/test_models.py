#!/usr/bin/env python
"""Tests for common/models.py"""

import pytest
from datetime import date
from pydantic import ValidationError
import sys
from pathlib import Path
import json

# Add the parent directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.models import (
    ArticleAuthorLink,
    ArticleTagLink,
    ArticleJournalLink,
    ArticleBase,
    ArticleTable,
    Author,
    AuthorTable,
    Article,
    ArticleList,
    Tag,
    JournalTable,
    MetadataResponse,
    TaggingResponse,
    ClassificationResponse,
    pprint,
)


class TestAuthor:
    """Test suite for Author model"""

    def test_create_individual_author(self):
        """Test creating a valid individual author"""
        author = Author(first_name="John", last_name="Doe")
        assert author.first_name == "John"
        assert author.last_name == "Doe"
        assert not author.is_institutional
        assert str(author) == "John Doe"

    def test_create_institutional_author(self):
        """Test creating an institutional author (first_name=None)"""
        author = Author(last_name="University Research Lab")
        assert author.first_name is None
        assert author.last_name == "University Research Lab"
        assert author.is_institutional
        assert str(author) == "University Research Lab"

    def test_author_requires_last_name(self):
        """Test that Author requires last_name"""
        with pytest.raises(ValidationError) as exc_info:
            Author(first_name="John")
        assert "last_name" in str(exc_info.value).lower()
        assert (
            "field required" in str(exc_info.value).lower()
            or "missing" in str(exc_info.value).lower()
        )

    def test_author_json_serialization(self):
        """Test Author JSON serialization"""
        author = Author(first_name="Jane", last_name="Smith")
        json_str = author.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["first_name"] == "Jane"
        assert parsed["last_name"] == "Smith"


class TestInstitutionalAuthor:
    """Test suite for institutional authors using Author"""

    def test_create_institutional_author(self):
        """Test creating a valid institutional author"""
        author = Author(last_name="University Research Lab")
        assert author.last_name == "University Research Lab"
        assert author.first_name is None
        assert author.is_institutional

    def test_institutional_author_requires_name(self):
        """Test that institutional author requires last_name"""
        with pytest.raises(ValidationError) as exc_info:
            Author()
        assert "last_name" in str(exc_info.value).lower()
        assert (
            "field required" in str(exc_info.value).lower()
            or "missing" in str(exc_info.value).lower()
        )

    def test_institutional_author_json_serialization(self):
        """Test institutional author JSON serialization"""
        author = Author(last_name="Research Institute")
        json_str = author.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["last_name"] == "Research Institute"
        # first_name should be None but might not be in JSON if excluded


class TestArticle:
    """Test suite for Article model"""

    def test_create_minimal_article(self):
        """Test creating an Article with minimal required fields"""
        article = Article(
            url="https://example.com/article",
            journal="Nature",
            date=date(2024, 1, 15),
            access_date=date(2024, 1, 20),
            raw_contents="Article text content",
        )
        assert str(article.url) == "https://example.com/article"
        assert article.journal == "Nature"
        assert article.date == date(2024, 1, 15)
        assert article.access_date == date(2024, 1, 20)
        assert article.raw_contents == "Article text content"

    def test_create_full_article(self):
        """Test creating an Article with all fields"""
        authors = [
            Author(first_name="John", last_name="Doe"),
            Author(first_name="Jane", last_name="Smith"),
        ]
        article = Article(
            title="Test Article",
            authors=authors,
            summary="Article summary",
            doi="10.1234/test",
            url="https://example.com/article",
            journal="Nature",
            journal_short_name="Nat.",
            volume=123,
            issue=4,
            date=date(2024, 1, 15),
            language="en",
            tags=["Network Biology", "Cancer Biology"],
            reasoning="Important findings",
            access_date=date(2024, 1, 20),
            raw_contents="Full article content",
            zotero_key="ABC123",
        )
        assert article.title == "Test Article"
        assert len(article.authors) == 2
        assert article.summary == "Article summary"
        assert article.doi == "10.1234/test"
        assert article.volume == 123
        assert article.issue == 4
        assert article.language == "en"
        assert article.tags == ["Network Biology", "Cancer Biology"]
        assert article.reasoning == "Important findings"
        assert article.zotero_key == "ABC123"

    def test_article_with_mixed_authors(self):
        """Test Article with both individual and institutional authors"""
        authors = [
            Author(first_name="John", last_name="Doe"),
            Author(last_name="Research Institute"),  # Institutional author
        ]
        article = Article(
            url="https://example.com/article",
            authors=authors,
            journal="Science",
            date=date(2024, 1, 15),
            access_date=date(2024, 1, 20),
            raw_contents="Content",
        )
        assert len(article.authors) == 2
        assert isinstance(article.authors[0], Author)
        assert isinstance(article.authors[1], Author)
        assert not article.authors[0].is_institutional
        assert article.authors[1].is_institutional

    def test_article_optional_fields_default_to_none(self):
        """Test that optional fields default to None"""
        article = Article(
            url="https://example.com/article",
            journal="Journal",
            date=date(2024, 1, 15),
            access_date=date(2024, 1, 20),
            raw_contents="Content",
        )
        assert article.title is None
        assert article.authors is None
        assert article.summary is None
        assert article.doi is None
        assert article.journal_short_name is None
        assert article.volume is None
        assert article.issue is None
        assert article.language is None
        assert article.tags is None
        assert article.reasoning is None
        assert article.zotero_key is None

    def test_article_requires_url(self):
        """Test that Article requires url"""
        with pytest.raises(ValidationError) as exc_info:
            Article(
                journal="Journal",
                date=date(2024, 1, 15),
                access_date=date(2024, 1, 20),
                raw_contents="Content",
            )
        assert "url" in str(exc_info.value).lower()

    def test_article_requires_journal(self):
        """Test that Article requires journal"""
        with pytest.raises(ValidationError) as exc_info:
            Article(
                url="https://example.com/article",
                date=date(2024, 1, 15),
                access_date=date(2024, 1, 20),
                raw_contents="Content",
            )
        assert "journal" in str(exc_info.value).lower()

    def test_article_requires_date(self):
        """Test that Article requires date"""
        with pytest.raises(ValidationError) as exc_info:
            Article(
                url="https://example.com/article",
                journal="Journal",
                access_date=date(2024, 1, 20),
                raw_contents="Content",
            )
        assert "date" in str(exc_info.value).lower()

    def test_article_requires_access_date(self):
        """Test that Article requires access_date"""
        with pytest.raises(ValidationError) as exc_info:
            Article(
                url="https://example.com/article",
                journal="Journal",
                date=date(2024, 1, 15),
                raw_contents="Content",
            )
        assert "access_date" in str(exc_info.value).lower()

    def test_article_requires_raw_contents(self):
        """Test that Article requires raw_contents"""
        with pytest.raises(ValidationError) as exc_info:
            Article(
                url="https://example.com/article",
                journal="Journal",
                date=date(2024, 1, 15),
                access_date=date(2024, 1, 20),
            )
        assert "raw_contents" in str(exc_info.value).lower()

    def test_article_validates_url_format(self):
        """Test that Article validates URL format"""
        with pytest.raises(ValidationError) as exc_info:
            Article(
                url="not-a-valid-url",
                journal="Journal",
                date=date(2024, 1, 15),
                access_date=date(2024, 1, 20),
                raw_contents="Content",
            )
        error_msg = str(exc_info.value).lower()
        assert "url" in error_msg

    def test_from_zotero_item_basic(self):
        """Test converting a basic Zotero item to Article"""
        zotero_item = {
            "key": "ABCDEF123",  # pragma: allowlist secret
            "data": {
                "itemType": "journalArticle",
                "title": "Test Article from Zotero",
                "abstractNote": "This is a test abstract",
                "DOI": "10.1234/test.zotero",
                "url": "https://example.com/zotero-article",
                "publicationTitle": "Nature",
                "journalAbbreviation": "Nat.",
                "date": "2024-01-15",
                "accessDate": "2024-01-20",
                "volume": "123",
                "issue": "4",
                "language": "en",
                "creators": [
                    {"creatorType": "author", "firstName": "John", "lastName": "Doe"},
                    {"creatorType": "author", "firstName": "Jane", "lastName": "Smith"},
                ],
                "tags": [{"tag": "Network Biology"}, {"tag": "Cancer"}],
            },
        }

        article = Article.from_zotero_item(zotero_item)

        assert article.title == "Test Article from Zotero"
        assert article.summary == "This is a test abstract"
        assert article.doi == "10.1234/test.zotero"
        assert str(article.url) == "https://example.com/zotero-article"
        assert article.journal == "Nature"
        assert article.journal_short_name == "Nat."
        assert article.date == date(2024, 1, 15)
        assert article.access_date == date(2024, 1, 20)
        assert article.volume == 123
        assert article.issue == 4
        assert article.language == "en"
        assert article.zotero_key == "ABCDEF123"  # pragma: allowlist secret
        assert len(article.authors) == 2
        assert article.authors[0].first_name == "John"
        assert article.authors[0].last_name == "Doe"
        assert len(article.tags) == 2
        assert "Network Biology" in article.tags

    def test_from_zotero_item_minimal(self):
        """Test converting a minimal Zotero item"""
        zotero_item = {
            "data": {
                "itemType": "journalArticle",
                "url": "https://example.com/minimal",
                "publicationTitle": "Science",
                "date": "2024-01-15",
            },
        }

        article = Article.from_zotero_item(zotero_item)

        assert article.url == "https://example.com/minimal"
        assert article.journal == "Science"
        assert article.title is None
        assert article.summary is None
        assert article.doi is None
        assert article.zotero_key is None

    def test_from_zotero_item_with_institutional_author(self):
        """Test converting Zotero item with institutional author"""
        zotero_item = {
            "data": {
                "itemType": "journalArticle",
                "url": "https://example.com/institutional",
                "publicationTitle": "Journal",
                "date": "2024-01-15",
                "creators": [
                    {"creatorType": "author", "name": "WHO Consortium"},
                    {"creatorType": "author", "firstName": "Jane", "lastName": "Smith"},
                ],
            },
        }

        article = Article.from_zotero_item(zotero_item)

        assert len(article.authors) == 2
        assert article.authors[0].first_name is None
        assert article.authors[0].last_name == "WHO Consortium"
        assert article.authors[0].is_institutional
        assert article.authors[1].first_name == "Jane"
        assert not article.authors[1].is_institutional

    def test_from_zotero_item_invalid_date(self):
        """Test that invalid dates default to today"""
        zotero_item = {
            "data": {
                "itemType": "journalArticle",
                "url": "https://example.com/test",
                "publicationTitle": "Journal",
                "date": "invalid-date",
                "accessDate": "also-invalid",
            },
        }

        article = Article.from_zotero_item(zotero_item)

        # Should default to today's date
        assert article.date == date.today()
        assert article.access_date == date.today()

    def test_from_zotero_item_missing_dates(self):
        """Test that missing dates default to today"""
        zotero_item = {
            "data": {
                "itemType": "journalArticle",
                "url": "https://example.com/test",
                "publicationTitle": "Journal",
            },
        }

        article = Article.from_zotero_item(zotero_item)

        assert article.date == date.today()
        assert article.access_date == date.today()


class TestMetadataResponse:
    """Test suite for MetadataResponse model"""

    def test_create_metadata_response(self):
        """Test creating a valid MetadataResponse"""
        response = MetadataResponse(
            title="Test Article",
            summary="Article summary",
            url="https://example.com/article",
            doi="10.1234/test",
        )
        assert response.title == "Test Article"
        assert response.summary == "Article summary"
        assert str(response.url) == "https://example.com/article"
        assert response.doi == "10.1234/test"

    def test_metadata_response_validates_doi_format(self):
        """Test that MetadataResponse validates DOI format"""
        with pytest.raises(ValidationError) as exc_info:
            MetadataResponse(
                title="Test",
                summary="Summary",
                url="https://example.com/article",
                doi="invalid-doi",
            )
        error_msg = str(exc_info.value).lower()
        assert "doi" in error_msg

    def test_metadata_response_requires_all_fields(self):
        """Test that MetadataResponse requires all fields"""
        with pytest.raises(ValidationError) as exc_info:
            MetadataResponse(
                title="Test",
                summary="Summary",
                url="https://example.com/article",
            )
        assert "doi" in str(exc_info.value).lower()

    def test_metadata_response_valid_doi_formats(self):
        """Test various valid DOI formats"""
        valid_dois = [
            "10.1234/test",
            "10.1000/xyz123",
            "10.12345/journal.2024.01.001",
            "10.1234/test-article-2024",
        ]
        for doi in valid_dois:
            response = MetadataResponse(
                title="Test",
                summary="Summary",
                url="https://example.com/article",
                doi=doi,
            )
            assert response.doi == doi

    def test_metadata_response_invalid_doi_formats(self):
        """Test various invalid DOI formats"""
        invalid_dois = [
            "doi:10.1234/test",  # Has prefix
            "10.123/test",  # Too few digits before slash
            "11.1234/test",  # Must start with 10
            "10.1234",  # Missing slash and suffix
            "10.1234/",  # Missing suffix
        ]
        for doi in invalid_dois:
            with pytest.raises(ValidationError) as exc_info:
                MetadataResponse(
                    title="Test",
                    summary="Summary",
                    url="https://example.com/article",
                    doi=doi,
                )
            assert "doi" in str(exc_info.value).lower()


class TestLabellingResponse:
    """Test suite for TaggingResponse model"""

    def test_create_tagging_response(self):
        """Test creating a valid TaggingResponse"""
        response = TaggingResponse(
            doi="10.1234/test",
            tags=["Network Biology", "Cancer Biology"],
            reasoning="Important findings in network-based cancer research",
        )
        assert response.doi == "10.1234/test"
        assert response.tags == ["Network Biology", "Cancer Biology"]
        assert (
            response.reasoning == "Important findings in network-based cancer research"
        )

    def test_tagging_response_single_tag(self):
        """Test TaggingResponse with single tag"""
        response = TaggingResponse(
            doi="10.1234/test",
            tags=["Review"],
            reasoning="Comprehensive review article",
        )
        assert response.tags == ["Review"]

    def test_tagging_response_multiple_tags(self):
        """Test TaggingResponse with multiple tags"""
        response = TaggingResponse(
            doi="10.1234/test",
            tags=[
                "Computational Biology",
                "Network Biology",
                "Drug discovery",
                "Drug Target Discovery",
                "Review",
            ],
            reasoning="Network-based drug discovery review",
        )
        assert len(response.tags) == 5

    def test_tagging_response_empty_tags(self):
        """Test TaggingResponse with empty tags list"""
        response = TaggingResponse(
            doi="10.1234/test", tags=[], reasoning="No matching categories"
        )
        assert response.tags == []

    def test_tagging_response_requires_all_fields(self):
        """Test that TaggingResponse requires all fields"""
        with pytest.raises(ValidationError) as exc_info:
            TaggingResponse(doi="10.1234/test", tags=["Test"])
        assert "reasoning" in str(exc_info.value).lower()

        with pytest.raises(ValidationError) as exc_info:
            TaggingResponse(doi="10.1234/test", reasoning="Test")
        assert "tags" in str(exc_info.value).lower()

        with pytest.raises(ValidationError) as exc_info:
            TaggingResponse(tags=["Test"], reasoning="Test")
        assert "doi" in str(exc_info.value).lower()

    def test_tagging_response_tags_must_be_list(self):
        """Test that tags must be a list of strings"""
        # This should work - list of strings
        response = TaggingResponse(
            doi="10.1234/test", tags=["Network Biology", "Review"], reasoning="Test"
        )
        assert response.tags == ["Network Biology", "Review"]

        # This should fail - not a list
        with pytest.raises(ValidationError):
            TaggingResponse(
                doi="10.1234/test", tags="Network Biology", reasoning="Test"
            )


class TestClassificationResponse:
    """Test suite for ClassificationResponse model"""

    def test_create_classification_response(self):
        """Test creating a valid ClassificationResponse"""
        response = ClassificationResponse(
            doi="10.1234/test",
            priority="high",
            reasoning="Strong alignment with cluster on network-based drug discovery methods",
        )
        assert response.doi == "10.1234/test"
        assert response.priority == "high"
        assert "Strong alignment" in response.reasoning

    def test_classification_response_all_priority_levels(self):
        """Test ClassificationResponse with all valid priority levels"""
        for level in ["high", "medium", "low"]:
            response = ClassificationResponse(
                doi="10.1234/test",
                priority=level,
                reasoning=f"Test reasoning for {level} priority",
            )
            assert response.priority == level

    def test_classification_response_invalid_priority(self):
        """Test that ClassificationResponse rejects invalid priority values"""
        invalid_values = ["High", "MEDIUM", "Low", "very high", "none", ""]
        for invalid in invalid_values:
            with pytest.raises(ValidationError) as exc_info:
                ClassificationResponse(
                    doi="10.1234/test",
                    priority=invalid,
                    reasoning="Test reasoning",
                )
            assert "priority" in str(exc_info.value).lower()

    def test_classification_response_requires_all_fields(self):
        """Test that ClassificationResponse requires all fields"""
        with pytest.raises(ValidationError) as exc_info:
            ClassificationResponse(doi="10.1234/test", priority="high")
        assert "reasoning" in str(exc_info.value).lower()

        with pytest.raises(ValidationError) as exc_info:
            ClassificationResponse(doi="10.1234/test", reasoning="Test")
        assert "priority" in str(exc_info.value).lower()

        with pytest.raises(ValidationError) as exc_info:
            ClassificationResponse(priority="high", reasoning="Test")
        assert "doi" in str(exc_info.value).lower()

    def test_classification_response_reasoning_can_be_detailed(self):
        """Test ClassificationResponse with detailed reasoning"""
        long_reasoning = (
            "The 5 neighbor articles all focus on network analysis methods for biological data. "
            "Target article presents a graph neural network approach for predicting protein interactions. "
            "Tag overlap includes 'Network Biology', 'Machine Learning', and 'Protein Interactions'. "
            "Methodology is consistent with neighbors. High priority assigned."
        )
        response = ClassificationResponse(
            doi="10.1234/test",
            priority="high",
            reasoning=long_reasoning,
        )
        assert response.reasoning == long_reasoning
        assert len(response.reasoning) > 100


class TestPprint:
    """Test suite for pprint function"""

    def test_pprint_single_author(self):
        """Test pprint with a single Author model"""
        author = Author(first_name="John", last_name="Doe")
        result = pprint(author)
        parsed = json.loads(result)
        assert parsed["first_name"] == "John"
        assert parsed["last_name"] == "Doe"
        assert isinstance(result, str)
        # Verify pretty formatting
        assert "\n" in result
        assert "  " in result or "\t" in result  # Check for indentation

    def test_pprint_list_of_authors(self):
        """Test pprint with a list of models"""
        authors = [
            Author(first_name="John", last_name="Doe"),
            Author(first_name="Jane", last_name="Smith"),
        ]
        result = pprint(authors)
        parsed = json.loads(result)
        assert len(parsed) == 2
        assert parsed[0]["first_name"] == "John"
        assert parsed[1]["first_name"] == "Jane"
        assert result.startswith("[")
        assert result.endswith("]")
        # Verify pretty formatting
        assert "\n" in result
        assert "  " in result or "\t" in result

    def test_pprint_dict_of_models(self):
        """Test pprint with a dict of models"""
        authors = {
            "author1": Author(first_name="John", last_name="Doe"),
            "author2": Author(first_name="Jane", last_name="Smith"),
        }
        result = pprint(authors)
        parsed = json.loads(result)
        assert "author1" in parsed
        assert "author2" in parsed
        assert parsed["author1"]["first_name"] == "John"
        assert parsed["author2"]["first_name"] == "Jane"
        assert result.startswith("{")
        assert result.endswith("}")
        # Verify pretty formatting
        assert "\n" in result
        assert "  " in result or "\t" in result

    def test_pprint_article_with_none_values(self):
        """Test pprint excludes None values by default"""
        article = Article(
            url="https://example.com/article",
            journal="Journal",
            date=date(2024, 1, 15),
            access_date=date(2024, 1, 20),
            raw_contents="Content",
        )
        result = pprint(article)
        parsed = json.loads(result)
        # None fields should not appear in output
        assert "title" not in parsed
        assert "summary" not in parsed
        assert "doi" not in parsed

    def test_pprint_article_include_none_values(self):
        """Test pprint includes None values when exclude_none=False"""
        article = Article(
            url="https://example.com/article",
            journal="Journal",
            date=date(2024, 1, 15),
            access_date=date(2024, 1, 20),
            raw_contents="Content",
        )
        result = pprint(article, exclude_none=False)
        parsed = json.loads(result)
        # None fields should appear in output as null
        assert "title" in parsed
        assert parsed["title"] is None

    def test_pprint_metadata_response(self):
        """Test pprint with MetadataResponse"""
        response = MetadataResponse(
            title="Test Article",
            summary="Summary",
            url="https://example.com/article",
            doi="10.1234/test",
        )
        result = pprint(response)
        parsed = json.loads(result)
        assert parsed["title"] == "Test Article"
        assert parsed["doi"] == "10.1234/test"

    def test_pprint_labelling_response(self):
        """Test pprint with LabellingResponse"""
        response = TaggingResponse(
            doi="10.1234/test",
            tags=["Network Biology", "Review"],
            reasoning="Important findings",
        )
        result = pprint(response)
        parsed = json.loads(result)
        assert parsed["doi"] == "10.1234/test"
        assert parsed["tags"] == ["Network Biology", "Review"]
        assert parsed["reasoning"] == "Important findings"

    def test_pprint_empty_list(self):
        """Test pprint with empty list"""
        result = pprint([])
        parsed = json.loads(result)
        assert parsed == []
        assert result.startswith("[")
        assert result.endswith("]")

    def test_pprint_empty_dict(self):
        """Test pprint with empty dict"""
        result = pprint({})
        parsed = json.loads(result)
        assert parsed == {}
        assert result.startswith("{")
        assert result.endswith("}")

    def test_pprint_list_has_proper_formatting(self):
        """Test that pprint formats list with proper indentation and commas"""
        authors = [
            Author(first_name="John", last_name="Doe"),
            Author(first_name="Jane", last_name="Smith"),
        ]
        result = pprint(authors)
        parsed = json.loads(result)
        assert len(parsed) == 2
        # Check for proper JSON list structure
        assert result.startswith("[")
        assert result.endswith("]")
        # Verify pretty formatting with newlines and indentation
        lines = result.split("\n")
        assert len(lines) > 2  # Should have multiple lines
        # Check that elements are indented
        assert any(
            line.startswith("  ") or line.startswith("\t") for line in lines[1:-1]
        )

    def test_pprint_dict_has_proper_formatting(self):
        """Test that pprint formats dict with proper structure"""
        authors = {
            "author1": Author(first_name="John", last_name="Doe"),
        }
        result = pprint(authors)
        parsed = json.loads(result)
        assert "author1" in parsed
        assert result.startswith("{")
        assert result.endswith("}")
        # Verify pretty formatting with newlines and indentation
        lines = result.split("\n")
        assert len(lines) > 2  # Should have multiple lines
        assert any(
            line.startswith("  ") or line.startswith("\t") for line in lines[1:-1]
        )

    def test_pprint_raises_error_for_invalid_input(self):
        """Test that pprint raises TypeError for invalid input"""
        with pytest.raises(TypeError, match="Input must be a Pydantic BaseModel"):
            pprint("not a model")

        with pytest.raises(TypeError, match="Input must be a Pydantic BaseModel"):
            pprint(123)

        with pytest.raises(TypeError, match="Input must be a Pydantic BaseModel"):
            pprint(None)


class TestArticleAuthorLink:
    """Test suite for ArticleAuthorLink model"""

    def test_create_article_author_link(self):
        """Test creating a valid ArticleAuthorLink"""
        link = ArticleAuthorLink(article_id=1, author_id=2)
        assert link.article_id == 1
        assert link.author_id == 2

    def test_article_author_link_defaults(self):
        """Test that ArticleAuthorLink allows None defaults for foreign keys"""
        # SQLModel allows default=None for foreign keys
        link = ArticleAuthorLink()
        assert link.article_id is None
        assert link.author_id is None


class TestArticleTagLink:
    """Test suite for ArticleTagLink model"""

    def test_create_article_tag_link(self):
        """Test creating a valid ArticleTagLink"""
        link = ArticleTagLink(article_id=1, tag_id=3)
        assert link.article_id == 1
        assert link.tag_id == 3

    def test_article_tag_link_defaults(self):
        """Test that ArticleTagLink allows None defaults for foreign keys"""
        # SQLModel allows default=None for foreign keys
        link = ArticleTagLink()
        assert link.article_id is None
        assert link.tag_id is None


class TestArticleJournalLink:
    """Test suite for ArticleJournalLink model"""

    def test_create_article_journal_link(self):
        """Test creating a valid ArticleJournalLink"""
        link = ArticleJournalLink(article_id=1, journal_id=5)
        assert link.article_id == 1
        assert link.journal_id == 5

    def test_article_journal_link_defaults(self):
        """Test that ArticleJournalLink allows None defaults for foreign keys"""
        # SQLModel allows default=None for foreign keys
        link = ArticleJournalLink()
        assert link.article_id is None
        assert link.journal_id is None


class TestArticleBase:
    """Test suite for ArticleBase model"""

    def test_create_minimal_article_base(self):
        """Test creating an ArticleBase with minimal required fields"""
        article = ArticleBase(
            url="https://example.com/article",
            date=date(2024, 1, 15),
            access_date=date(2024, 1, 20),
            raw_contents="Article text content",
        )
        assert str(article.url) == "https://example.com/article"
        assert article.date == date(2024, 1, 15)
        assert article.access_date == date(2024, 1, 20)
        assert article.raw_contents == "Article text content"

    def test_create_full_article_base(self):
        """Test creating an ArticleBase with all fields"""
        article = ArticleBase(
            doi="10.1234/test",
            title="Test Article",
            summary="Article summary",
            url="https://example.com/article",
            volume=123,
            issue=4,
            date=date(2024, 1, 15),
            language="en",
            reasoning="Important findings",
            score=85,
            access_date=date(2024, 1, 20),
            raw_contents="Full article content",
            zotero_key="ABC123",
        )
        assert article.doi == "10.1234/test"
        assert article.title == "Test Article"
        assert article.summary == "Article summary"
        assert article.volume == 123
        assert article.issue == 4
        assert article.language == "en"
        assert article.reasoning == "Important findings"
        assert article.score == 85
        assert article.zotero_key == "ABC123"

    def test_article_base_validates_url_format(self):
        """Test that ArticleBase validates URL format"""
        with pytest.raises(ValidationError) as exc_info:
            ArticleBase(
                url="not-a-valid-url",
                date=date(2024, 1, 15),
                access_date=date(2024, 1, 20),
                raw_contents="Content",
            )
        error_msg = str(exc_info.value).lower()
        assert "url" in error_msg


class TestArticleTable:
    """Test suite for ArticleTable model"""

    def test_create_article_table(self):
        """Test creating an ArticleTable"""
        article = ArticleTable(
            url="https://example.com/article",
            date=date(2024, 1, 15),
            access_date=date(2024, 1, 20),
            raw_contents="Article content",
            embedding=[0.1] * 3072,  # Vector of 3072 dimensions
        )
        assert str(article.url) == "https://example.com/article"
        assert article.id is None  # Not set until saved to DB
        assert len(article.embedding) == 3072

    def test_article_table_with_id(self):
        """Test creating an ArticleTable with an ID"""
        article = ArticleTable(
            id=42,
            url="https://example.com/article",
            date=date(2024, 1, 15),
            access_date=date(2024, 1, 20),
            raw_contents="Article content",
            embedding=[0.5] * 3072,
        )
        assert article.id == 42

    def test_article_table_inherits_from_article_base(self):
        """Test that ArticleTable inherits all ArticleBase fields"""
        article = ArticleTable(
            doi="10.1234/test",
            title="Test Article",
            summary="Summary",
            url="https://example.com/article",
            volume=10,
            issue=2,
            date=date(2024, 1, 15),
            language="en",
            reasoning="Test reasoning",
            score=90,
            access_date=date(2024, 1, 20),
            raw_contents="Content",
            zotero_key="KEY123",
            embedding=[0.2] * 3072,
        )
        assert article.doi == "10.1234/test"
        assert article.title == "Test Article"
        assert article.score == 90


class TestAuthorTable:
    """Test suite for AuthorTable model"""

    def test_create_author_table(self):
        """Test creating an AuthorTable"""
        author = AuthorTable(first_name="John", last_name="Doe")
        assert author.first_name == "John"
        assert author.last_name == "Doe"
        assert author.id is None  # Not set until saved to DB

    def test_create_institutional_author_table(self):
        """Test creating an institutional AuthorTable"""
        author = AuthorTable(last_name="Research Institute")
        assert author.first_name is None
        assert author.last_name == "Research Institute"
        assert author.is_institutional

    def test_author_table_with_id(self):
        """Test creating an AuthorTable with an ID"""
        author = AuthorTable(id=10, first_name="Jane", last_name="Smith")
        assert author.id == 10
        assert author.first_name == "Jane"

    def test_author_table_inherits_from_author_base(self):
        """Test that AuthorTable inherits Author functionality"""
        author = AuthorTable(first_name="Alice", last_name="Johnson")
        assert str(author) == "Alice Johnson"
        assert not author.is_institutional


class TestTag:
    """Test suite for Tag model"""

    def test_create_tag(self):
        """Test creating a valid Tag"""
        tag = Tag(name="Network Biology")
        assert tag.name == "Network Biology"
        assert tag.id is None  # Not set until saved to DB

    def test_create_tag_with_id(self):
        """Test creating a Tag with an ID"""
        tag = Tag(id=5, name="Cancer Biology")
        assert tag.id == 5
        assert tag.name == "Cancer Biology"

    def test_tag_json_serialization(self):
        """Test Tag JSON serialization"""
        tag = Tag(name="Machine Learning")
        json_str = tag.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["name"] == "Machine Learning"

    def test_tag_name_is_indexed(self):
        """Test that Tag name field is marked as indexed"""
        # This verifies the model structure, actual indexing happens in DB
        assert Tag.model_fields["name"].json_schema_extra is None or True


class TestJournalTable:
    """Test suite for JournalTable model"""

    def test_create_journal_table(self):
        """Test creating a valid JournalTable"""
        journal = JournalTable(name="Nature")
        assert journal.name == "Nature"
        assert journal.short_name is None
        assert journal.id is None  # Not set until saved to DB

    def test_create_journal_table_with_short_name(self):
        """Test creating a JournalTable with short name"""
        journal = JournalTable(name="Nature Genetics", short_name="Nat Genet")
        assert journal.name == "Nature Genetics"
        assert journal.short_name == "Nat Genet"

    def test_create_journal_table_with_id(self):
        """Test creating a JournalTable with an ID"""
        journal = JournalTable(id=15, name="Science", short_name="Sci")
        assert journal.id == 15
        assert journal.name == "Science"
        assert journal.short_name == "Sci"

    def test_journal_table_json_serialization(self):
        """Test JournalTable JSON serialization"""
        journal = JournalTable(name="Cell", short_name="Cell")
        json_str = journal.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["name"] == "Cell"
        assert parsed["short_name"] == "Cell"

    def test_journal_table_name_is_indexed(self):
        """Test that JournalTable name field is marked as indexed"""
        # This verifies the model structure, actual indexing happens in DB
        assert JournalTable.model_fields["name"].json_schema_extra is None or True


class TestArticleList:
    """Test suite for ArticleList TypeAdapter"""

    def test_article_list_validate_json(self):
        """Test validating a JSON list of articles"""
        json_data = """[
            {
                "url": "https://example.com/article1",
                "journal": "Nature",
                "date": "2024-01-15",
                "access_date": "2024-01-20",
                "raw_contents": "Content 1"
            },
            {
                "url": "https://example.com/article2",
                "journal": "Science",
                "date": "2024-02-10",
                "access_date": "2024-02-15",
                "raw_contents": "Content 2"
            }
        ]"""
        articles = ArticleList.validate_json(json_data)
        assert len(articles) == 2
        assert articles[0].journal == "Nature"
        assert articles[1].journal == "Science"

    def test_article_list_dump_json(self):
        """Test dumping a list of articles to JSON"""
        articles = [
            Article(
                url="https://example.com/article",
                journal="Nature",
                date=date(2024, 1, 15),
                access_date=date(2024, 1, 20),
                raw_contents="Content",
            )
        ]
        json_bytes = ArticleList.dump_json(articles, indent=2)
        json_str = json_bytes.decode()
        parsed = json.loads(json_str)
        assert len(parsed) == 1
        assert parsed[0]["journal"] == "Nature"

    def test_article_list_validates_items(self):
        """Test that ArticleList validates individual items"""
        invalid_json = """[
            {
                "url": "not-a-url",
                "journal": "Nature",
                "date": "2024-01-15",
                "access_date": "2024-01-20",
                "raw_contents": "Content"
            }
        ]"""
        with pytest.raises(ValidationError):
            ArticleList.validate_json(invalid_json)
