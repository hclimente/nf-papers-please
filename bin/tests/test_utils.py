#!/usr/bin/env python
"""Tests for common/utils.py"""

import os
import pytest
from unittest.mock import patch
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.utils import (
    get_env_variable,
    get_common_variations,
    prune_article_for_classification,
)
from common.models import Article, Author
from datetime import date


class TestGetEnvVariable:
    """Test suite for get_env_variable function"""

    def test_get_existing_env_variable(self):
        """Test retrieving an existing environment variable"""
        # Set a test environment variable
        test_var = "TEST_VAR_12345"
        test_value = "test_value"
        os.environ[test_var] = test_value

        try:
            result = get_env_variable(test_var)
            assert result == test_value
        finally:
            # Clean up
            del os.environ[test_var]

    def test_get_existing_env_variable_with_raise_error_false(self):
        """Test retrieving an existing variable with raise_error=False"""
        test_var = "TEST_VAR_67890"
        test_value = "another_value"
        os.environ[test_var] = test_value

        try:
            result = get_env_variable(test_var, raise_error=False)
            assert result == test_value
        finally:
            del os.environ[test_var]

    def test_get_existing_env_variable_with_raise_error_true(self):
        """Test retrieving an existing variable with raise_error=True"""
        test_var = "TEST_VAR_RAISE"
        test_value = "value_with_raise"
        os.environ[test_var] = test_value

        try:
            result = get_env_variable(test_var, raise_error=True)
            assert result == test_value
        finally:
            del os.environ[test_var]

    def test_get_missing_env_variable_default_behavior(self):
        """Test retrieving a missing variable with default behavior (raise_error=False)"""
        test_var = "NONEXISTENT_VAR_12345"
        # Ensure it doesn't exist
        if test_var in os.environ:
            del os.environ[test_var]

        result = get_env_variable(test_var)
        assert result is None

    def test_get_missing_env_variable_with_raise_error_false(self):
        """Test retrieving a missing variable with raise_error=False"""
        test_var = "NONEXISTENT_VAR_67890"
        # Ensure it doesn't exist
        if test_var in os.environ:
            del os.environ[test_var]

        result = get_env_variable(test_var, raise_error=False)
        assert result is None

    def test_get_missing_env_variable_with_raise_error_true(self):
        """Test that missing variable raises ValueError when raise_error=True"""
        test_var = "NONEXISTENT_VAR_ERROR"
        # Ensure it doesn't exist
        if test_var in os.environ:
            del os.environ[test_var]

        with pytest.raises(
            ValueError, match=f"{test_var} environment variable not found"
        ):
            get_env_variable(test_var, raise_error=True)

    def test_get_empty_string_env_variable(self):
        """Test retrieving an environment variable set to empty string"""
        test_var = "EMPTY_VAR_12345"
        os.environ[test_var] = ""

        try:
            # Empty string is falsy, function logs error but still returns empty string
            result = get_env_variable(test_var)
            assert result == ""
        finally:
            del os.environ[test_var]

    def test_get_empty_string_env_variable_with_raise_error_true(self):
        """Test that empty string raises ValueError when raise_error=True"""
        test_var = "EMPTY_VAR_ERROR"
        os.environ[test_var] = ""

        try:
            with pytest.raises(
                ValueError, match=f"{test_var} environment variable not found"
            ):
                get_env_variable(test_var, raise_error=True)
        finally:
            del os.environ[test_var]

    def test_get_env_variable_with_special_characters(self):
        """Test retrieving an environment variable with special characters in value"""
        test_var = "SPECIAL_CHAR_VAR"
        test_value = "value with spaces and !@#$%"
        os.environ[test_var] = test_value

        try:
            result = get_env_variable(test_var)
            assert result == test_value
        finally:
            del os.environ[test_var]

    def test_get_env_variable_with_multiline_value(self):
        """Test retrieving an environment variable with multiline value"""
        test_var = "MULTILINE_VAR"
        test_value = "line1\nline2\nline3"
        os.environ[test_var] = test_value

        try:
            result = get_env_variable(test_var)
            assert result == test_value
            assert "\n" in result
        finally:
            del os.environ[test_var]

    def test_get_env_variable_with_numeric_value(self):
        """Test retrieving an environment variable with numeric value (stored as string)"""
        test_var = "NUMERIC_VAR"
        test_value = "12345"
        os.environ[test_var] = test_value

        try:
            result = get_env_variable(test_var)
            assert result == test_value
            assert isinstance(result, str)
        finally:
            del os.environ[test_var]

    @patch("common.utils.logging.error")
    def test_get_missing_env_variable_logs_error(self, mock_logging_error):
        """Test that missing variable logs an error message"""
        test_var = "LOGGING_TEST_VAR"
        # Ensure it doesn't exist
        if test_var in os.environ:
            del os.environ[test_var]

        get_env_variable(test_var, raise_error=False)

        # Check that logging.error was called
        mock_logging_error.assert_called_once()
        call_args = mock_logging_error.call_args[0][0]
        assert test_var in call_args
        assert "not found" in call_args

    @patch("common.utils.logging.error")
    def test_get_empty_env_variable_logs_error(self, mock_logging_error):
        """Test that empty variable logs an error message"""
        test_var = "EMPTY_LOGGING_TEST_VAR"
        os.environ[test_var] = ""

        try:
            get_env_variable(test_var, raise_error=False)

            # Check that logging.error was called
            mock_logging_error.assert_called_once()
            call_args = mock_logging_error.call_args[0][0]
            assert test_var in call_args
            assert "not found" in call_args
        finally:
            del os.environ[test_var]

    def test_get_env_variable_case_sensitive(self):
        """Test that environment variable names are case-sensitive"""
        test_var_lower = "test_case_var"
        test_var_upper = "TEST_CASE_VAR"
        test_value = "case_test_value"

        os.environ[test_var_lower] = test_value

        try:
            # Should find the lowercase version
            result_lower = get_env_variable(test_var_lower)
            assert result_lower == test_value

            # Should not find the uppercase version (if not set)
            if test_var_upper not in os.environ:
                result_upper = get_env_variable(test_var_upper)
                assert result_upper is None
        finally:
            if test_var_lower in os.environ:
                del os.environ[test_var_lower]


class TestGetCommonVariations:
    """Test suite for get_common_variations function"""

    def test_get_variations_single_value(self):
        """Test generating variations for a single value"""
        result = get_common_variations(["test"])

        # Check basic case variations
        assert result["test"] == "test"
        assert result["TEST"] == "test"
        assert result["Test"] == "test"

        # Check quote variations
        assert result["'test'"] == "test"
        assert result['"test"'] == "test"

        # Check punctuation
        assert result["test."] == "test"

    def test_get_variations_multiple_values(self):
        """Test generating variations for multiple values"""
        result = get_common_variations(["yes", "no"])

        assert result["yes"] == "yes"
        assert result["YES"] == "yes"
        assert result["no"] == "no"
        assert result["NO"] == "no"

    def test_get_variations_with_priority_levels(self):
        """Test generating variations for priority levels"""
        result = get_common_variations(["high", "medium", "low"])

        assert result["high"] == "high"
        assert result["High"] == "high"
        assert result["HIGH"] == "high"
        assert result["'high'"] == "high"
        assert result['"high"'] == "high"
        assert result["high."] == "high"

        assert result["medium"] == "medium"
        assert result["low"] == "low"

    def test_get_variations_with_boolean_strings(self):
        """Test generating variations for boolean strings"""
        result = get_common_variations(["true", "false"])

        assert result["true"] == "true"
        assert result["True"] == "true"
        assert result["TRUE"] == "true"
        assert result["false"] == "false"
        assert result["False"] == "false"
        assert result["FALSE"] == "false"

    def test_get_variations_empty_list(self):
        """Test generating variations for empty list"""
        result = get_common_variations([])
        assert result == {}

    def test_get_variations_with_multiword(self):
        """Test generating variations for multi-word values"""
        result = get_common_variations(["very high"])

        assert result["very high"] == "very high"
        assert result["Very High"] == "very high"
        assert result["VERY HIGH"] == "very high"

    def test_get_variations_preserves_original(self):
        """Test that original value is preserved in mapping"""
        expected = ["original"]
        result = get_common_variations(expected)

        # All variations should map back to the original
        for key in result.keys():
            assert result[key] == "original"

    def test_get_variations_case_insensitive_lookup(self):
        """Test that variations enable case-insensitive lookup"""
        values = ["Accept", "Reject"]
        mapping = get_common_variations(values)

        # All these should resolve to "Accept"
        assert mapping.get("accept") == "Accept"
        assert mapping.get("ACCEPT") == "Accept"
        assert mapping.get("Accept") == "Accept"

        # All these should resolve to "Reject"
        assert mapping.get("reject") == "Reject"
        assert mapping.get("REJECT") == "Reject"
        assert mapping.get("Reject") == "Reject"

    def test_get_variations_with_all_case_methods(self):
        """Test that all case transformation methods are included"""
        result = get_common_variations(["tEsT"])

        # Original
        assert result["tEsT"] == "tEsT"
        # lower()
        assert result["test"] == "tEsT"
        # upper()
        assert result["TEST"] == "tEsT"
        # capitalize()
        assert result["Test"] == "tEsT"
        # title()
        assert result["Test"] == "tEsT"

    def test_get_variations_with_quotes_and_punctuation(self):
        """Test that quote and punctuation variations are created for all case variants"""
        result = get_common_variations(["val"])

        # Should have variations like 'val', "val", val. for all case variants
        assert "'val'" in result
        assert '"val"' in result
        assert "val." in result
        assert "'VAL'" in result
        assert '"VAL"' in result
        assert "VAL." in result


class TestPruneArticleForClassification:
    """Test suite for prune_article_for_classification function"""

    def test_prune_keeps_required_fields(self):
        """Test that pruning keeps all required fields for classification"""
        neighbor1 = Article(
            title="Neighbor 1",
            journal="Neighbor Journal",
            url="https://example.com/neighbor1",
            date=date(2024, 1, 1),
            access_date=date(2024, 1, 2),
            raw_contents="neighbor content",
        )
        neighbor2 = Article(
            title="Neighbor 2",
            journal="Neighbor Journal",
            url="https://example.com/neighbor2",
            date=date(2024, 1, 1),
            access_date=date(2024, 1, 2),
            raw_contents="neighbor content",
        )

        article = Article(
            title="Test Article",
            journal="Nature",
            journal_short_name="Nat",
            authors=[Author(first_name="John", last_name="Doe")],
            summary="Test summary",
            tags=["Tag1", "Tag2"],
            doi="10.1234/test",
            url="https://example.com",
            date=date(2024, 1, 1),
            access_date=date(2024, 1, 2),
            raw_contents="Full text content here",
            nearest_neighbors=[neighbor1, neighbor2],
        )

        pruned = prune_article_for_classification(article)

        assert pruned.title == "Test Article"
        assert pruned.journal == "Nature"
        assert pruned.journal_short_name == "Nat"
        assert len(pruned.authors) == 1
        assert pruned.authors[0].first_name == "John"
        assert pruned.summary == "Test summary"
        assert pruned.tags == ["Tag1", "Tag2"]
        assert pruned.doi == "10.1234/test"
        assert pruned.url == "https://example.com"
        assert len(pruned.nearest_neighbors) == 2
        assert isinstance(pruned.nearest_neighbors[0], Article)

    def test_prune_empties_raw_contents(self):
        """Test that pruning empties raw_contents to save tokens"""
        article = Article(
            title="Test",
            journal="Test Journal",
            url="https://example.com",
            date=date(2024, 1, 1),
            access_date=date(2024, 1, 2),
            raw_contents="Very long raw content that should be removed",
        )

        pruned = prune_article_for_classification(article)

        assert pruned.raw_contents == ""

    def test_prune_preserves_nearest_neighbors(self):
        """Test that nearest_neighbors field is preserved"""
        neighbor = Article(
            title="Neighbor Article",
            journal="Neighbor Journal",
            url="https://example.com/neighbor",
            date=date(2024, 1, 1),
            access_date=date(2024, 1, 2),
            raw_contents="neighbor content",
        )

        article = Article(
            title="Test",
            journal="Test Journal",
            url="https://example.com",
            date=date(2024, 1, 1),
            access_date=date(2024, 1, 2),
            raw_contents="content",
            nearest_neighbors=[neighbor],
        )

        pruned = prune_article_for_classification(article)

        assert len(pruned.nearest_neighbors) == 1
        assert isinstance(pruned.nearest_neighbors[0], Article)
        assert pruned.nearest_neighbors[0].title == "Neighbor Article"

    def test_prune_handles_none_nearest_neighbors(self):
        """Test that pruning handles articles without nearest_neighbors"""
        article = Article(
            title="Test",
            journal="Test Journal",
            url="https://example.com",
            date=date(2024, 1, 1),
            access_date=date(2024, 1, 2),
            raw_contents="content",
        )

        pruned = prune_article_for_classification(article)

        assert pruned.nearest_neighbors is None

    def test_prune_returns_article_instance(self):
        """Test that pruned result is an Article instance"""
        article = Article(
            title="Test",
            journal="Test Journal",
            url="https://example.com",
            date=date(2024, 1, 1),
            access_date=date(2024, 1, 2),
            raw_contents="content",
        )

        pruned = prune_article_for_classification(article)

        assert isinstance(pruned, Article)

    def test_prune_recursively_prunes_neighbor_articles(self):
        """Test that pruning recursively prunes Article objects in nearest_neighbors"""
        neighbor1 = Article(
            title="Neighbor 1",
            journal="Journal 1",
            url="https://example.com/1",
            date=date(2024, 1, 1),
            access_date=date(2024, 1, 2),
            raw_contents="Long raw content for neighbor 1",
            tags=["Tag1"],
        )
        neighbor2 = Article(
            title="Neighbor 2",
            journal="Journal 2",
            url="https://example.com/2",
            date=date(2024, 1, 1),
            access_date=date(2024, 1, 2),
            raw_contents="Long raw content for neighbor 2",
            tags=["Tag2"],
        )

        article = Article(
            title="Target Article",
            journal="Main Journal",
            url="https://example.com/target",
            date=date(2024, 1, 1),
            access_date=date(2024, 1, 2),
            raw_contents="Target article raw content",
            nearest_neighbors=[neighbor1, neighbor2],
        )

        pruned = prune_article_for_classification(article)

        # Check that main article was pruned
        assert pruned.raw_contents == ""

        # Check that neighbors were pruned recursively
        assert len(pruned.nearest_neighbors) == 2
        assert isinstance(pruned.nearest_neighbors[0], Article)
        assert pruned.nearest_neighbors[0].raw_contents == ""
        assert pruned.nearest_neighbors[1].raw_contents == ""
        assert pruned.nearest_neighbors[0].title == "Neighbor 1"
        assert pruned.nearest_neighbors[1].title == "Neighbor 2"


class TestArticleTableToArticle:
    """Test suite for article_table_to_article function"""

    def test_converts_basic_fields(self):
        """Test that basic fields are converted correctly"""
        from common.utils import article_table_to_article
        from common.models import ArticleTable, AuthorTable, JournalTable, Tag

        # Create a simple ArticleTable
        journal = JournalTable(name="Nature", short_name="Nat.")
        author = AuthorTable(first_name="John", last_name="Doe")
        tag = Tag(name="Computational Biology")

        article_table = ArticleTable(
            doi="10.1234/test",
            title="Test Article",
            summary="Test summary",
            url="https://example.com/test",
            date=date(2024, 1, 1),
            access_date=date(2024, 1, 2),
            raw_contents="Test raw content",
        )
        article_table.journal = journal
        article_table.authors = [author]
        article_table.tags = [tag]
        article_table.embedding = [0.1] * 3072

        result = article_table_to_article(article_table)

        assert result.doi == "10.1234/test"
        assert result.title == "Test Article"
        assert result.summary == "Test summary"
        assert result.url == "https://example.com/test"
        assert result.date == date(2024, 1, 1)
        assert result.access_date == date(2024, 1, 2)
        assert result.raw_contents == "Test raw content"
        assert result.journal == "Nature"
        assert result.journal_short_name == "Nat."
        assert len(result.authors) == 1
        assert result.authors[0].first_name == "John"
        assert result.authors[0].last_name == "Doe"
        assert len(result.tags) == 1
        assert result.tags[0] == "Computational Biology"
        assert len(result.embedding) == 3072

    def test_handles_optional_fields(self):
        """Test that None optional fields are handled correctly"""
        from common.utils import article_table_to_article
        from common.models import ArticleTable, JournalTable

        journal = JournalTable(name="Science")

        article_table = ArticleTable(
            title="Test",
            url="https://example.com/test",
            date=date(2024, 1, 1),
            access_date=date(2024, 1, 2),
            raw_contents="content",
        )
        article_table.journal = journal

        result = article_table_to_article(article_table)

        assert result.doi is None
        assert result.summary is None
        assert result.language is None
        assert result.reasoning is None
        assert result.relevance is None
        assert result.zotero_key is None
        assert result.authors is None
        assert result.tags is None
        assert result.journal_short_name is None

    def test_handles_multiple_authors(self):
        """Test conversion with multiple authors"""
        from common.utils import article_table_to_article
        from common.models import ArticleTable, AuthorTable, JournalTable

        journal = JournalTable(name="Cell")

        article_table = ArticleTable(
            title="Test",
            url="https://example.com/test",
            date=date(2024, 1, 1),
            access_date=date(2024, 1, 2),
            raw_contents="content",
        )
        article_table.journal = journal
        article_table.authors = [
            AuthorTable(first_name="Alice", last_name="Smith"),
            AuthorTable(first_name="Bob", last_name="Jones"),
            AuthorTable(first_name="Charlie", last_name="Brown"),
        ]

        result = article_table_to_article(article_table)

        assert len(result.authors) == 3
        assert result.authors[0].first_name == "Alice"
        assert result.authors[1].first_name == "Bob"
        assert result.authors[2].first_name == "Charlie"

    def test_handles_institutional_author(self):
        """Test conversion with institutional author (no first_name)"""
        from common.utils import article_table_to_article
        from common.models import ArticleTable, AuthorTable, JournalTable

        journal = JournalTable(name="PNAS")

        article_table = ArticleTable(
            title="Test",
            url="https://example.com/test",
            date=date(2024, 1, 1),
            access_date=date(2024, 1, 2),
            raw_contents="content",
        )
        article_table.journal = journal
        article_table.authors = [
            AuthorTable(last_name="WHO Consortium"),
        ]

        result = article_table_to_article(article_table)

        assert len(result.authors) == 1
        assert result.authors[0].first_name is None
        assert result.authors[0].last_name == "WHO Consortium"
        assert result.authors[0].is_institutional

    def test_returns_article_instance(self):
        """Test that the function returns an Article instance"""
        from common.utils import article_table_to_article
        from common.models import ArticleTable, JournalTable, Article

        journal = JournalTable(name="Nature")

        article_table = ArticleTable(
            title="Test",
            url="https://example.com/test",
            date=date(2024, 1, 1),
            access_date=date(2024, 1, 2),
            raw_contents="content",
        )
        article_table.journal = journal

        result = article_table_to_article(article_table)

        assert isinstance(result, Article)
