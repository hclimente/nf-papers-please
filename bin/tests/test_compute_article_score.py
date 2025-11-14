"""
Tests for compute_article_score.py
"""

from datetime import date
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

from compute_article_score import (
    build_category_index,
    compute_article_score,
    load_research_interests,
)
from common.models import Article


@pytest.fixture
def sample_research_interests():
    """Sample research interests structure for testing."""
    return {
        "field": [
            {
                "name": "Computational Biology",
                "aliases": ["Machine Learning in Biology"],
                "points": 1,
                "subcategories": [
                    {
                        "name": "Network Biology",
                        "aliases": ["Graphs"],
                        "points": 3,
                    },
                    {
                        "name": "Statistical Genetics",
                        "points": 2,
                    },
                    {
                        "name": "Cancer Biology",
                        "points": 2,
                    },
                ],
            },
            {
                "name": "No relevant field or subfield",
                "points": -3,
            },
        ],
        "applications": [
            {
                "name": "Drug discovery",
                "points": 1,
                "subcategories": [
                    {
                        "name": "Drug Target Discovery",
                        "aliases": ["Disease Gene Identification"],
                        "points": 3,
                    },
                ],
            },
            {
                "name": "Other application",
                "points": -2,
                "subcategories": [
                    {
                        "name": "Only non-human application(s)",
                        "points": -5,
                    }
                ],
            },
        ],
        "preferred_article_types": [
            {
                "name": "Review",
                "points": 3,
            },
            {
                "name": "New Computational Method",
                "points": 1,
            },
            {
                "name": "Pre-print",
                "points": -1,
            },
        ],
    }


@pytest.fixture
def sample_article():
    """Sample article for testing."""
    return Article(
        title="Test Article",
        url="https://example.com/article",
        journal="Test Journal",
        date=date(2024, 1, 1),
        access_date=date(2024, 1, 1),
        raw_contents="Test content",
    )


def test_build_category_index(sample_research_interests):
    """Test building category index."""
    index = build_category_index(sample_research_interests)

    # Check parent category
    assert "Computational Biology" in index
    assert index["Computational Biology"]["points"] == 1
    assert index["Computational Biology"]["parent"] is None
    assert index["Computational Biology"]["has_subcategories"] is True

    # Check subcategory
    assert "Network Biology" in index
    assert index["Network Biology"]["points"] == 3
    assert index["Network Biology"]["parent"] == "Computational Biology"
    assert index["Network Biology"]["has_subcategories"] is False

    # Check alias
    assert "Graphs" in index
    assert index["Graphs"]["is_alias_of"] == "Network Biology"
    assert index["Graphs"]["points"] == 3

    # Check category without subcategories
    assert "Review" in index
    assert index["Review"]["points"] == 3
    assert index["Review"]["has_subcategories"] is False


def test_compute_score_no_tags(sample_article, sample_research_interests):
    """Test scoring article with no tags."""
    score = compute_article_score(sample_article, sample_research_interests)
    assert score == 0


def test_compute_score_single_leaf_tag(sample_article, sample_research_interests):
    """Test scoring with a single subcategory tag."""
    sample_article.tags = ["Network Biology"]
    score = compute_article_score(sample_article, sample_research_interests)
    # Should get 3 points for Network Biology, NOT 1 for Computational Biology
    assert score == 3


def test_compute_score_parent_and_child(sample_article, sample_research_interests):
    """Test scoring when both parent and child are tagged."""
    sample_article.tags = ["Computational Biology", "Network Biology"]
    score = compute_article_score(sample_article, sample_research_interests)
    # Should get 3 points for Network Biology only
    # Parent is excluded because child is tagged
    assert score == 3


def test_compute_score_multiple_siblings(sample_article, sample_research_interests):
    """Test scoring with multiple subcategories at same level."""
    sample_article.tags = ["Network Biology", "Statistical Genetics"]
    score = compute_article_score(sample_article, sample_research_interests)
    # Should get 3 + 2 = 5 points
    # Parent is not tagged, so both siblings count
    assert score == 5


def test_compute_score_multiple_dimensions(sample_article, sample_research_interests):
    """Test scoring across multiple dimensions."""
    sample_article.tags = ["Network Biology", "Drug Target Discovery", "Review"]
    score = compute_article_score(sample_article, sample_research_interests)
    # Network Biology: 3
    # Drug Target Discovery: 3
    # Review: 3
    # Total: 9
    assert score == 9


def test_compute_score_with_alias(sample_article, sample_research_interests):
    """Test scoring with alias tags."""
    sample_article.tags = ["Graphs", "Disease Gene Identification"]
    score = compute_article_score(sample_article, sample_research_interests)
    # Graphs (alias of Network Biology): 3
    # Disease Gene Identification (alias of Drug Target Discovery): 3
    # Total: 6
    assert score == 6


def test_compute_score_negative_points(sample_article, sample_research_interests):
    """Test scoring with negative point categories."""
    sample_article.tags = ["Pre-print", "Network Biology"]
    score = compute_article_score(sample_article, sample_research_interests)
    # Network Biology: 3
    # Pre-print: -1
    # Total: 2
    assert score == 2


def test_compute_score_parent_in_multiple_dimensions(
    sample_article, sample_research_interests
):
    """Test that parent exclusion only applies within same dimension."""
    sample_article.tags = [
        "Computational Biology",
        "Network Biology",
        "Drug discovery",
        "Drug Target Discovery",
    ]
    score = compute_article_score(sample_article, sample_research_interests)
    # Network Biology: 3 (Computational Biology excluded)
    # Drug Target Discovery: 3 (Drug discovery excluded)
    # Total: 6
    assert score == 6


def test_compute_score_nested_negative(sample_article, sample_research_interests):
    """Test scoring with nested category that has negative points."""
    sample_article.tags = ["Other application", "Only non-human application(s)"]
    score = compute_article_score(sample_article, sample_research_interests)
    # Only the child category should count
    # Only non-human application(s): -5
    assert score == -5


def test_compute_score_leaf_only(sample_article, sample_research_interests):
    """Test scoring with only parent category (no children tagged)."""
    sample_article.tags = ["Computational Biology"]
    score = compute_article_score(sample_article, sample_research_interests)
    # Should get 1 point for parent when no children are tagged
    assert score == 1


def test_compute_score_complex_scenario(sample_article, sample_research_interests):
    """Test complex scoring scenario."""
    sample_article.tags = [
        "Computational Biology",
        "Network Biology",
        "Cancer Biology",
        "Drug discovery",
        "Drug Target Discovery",
        "Review",
        "Pre-print",
    ]
    score = compute_article_score(sample_article, sample_research_interests)
    # Network Biology: 3 (Computational Biology excluded due to this)
    # Cancer Biology: 2 (Computational Biology excluded due to this too)
    # Drug Target Discovery: 3 (Drug discovery excluded)
    # Review: 3
    # Pre-print: -1
    # Total: 10
    assert score == 10


def test_load_research_interests_from_yaml():
    """Test loading research interests from YAML content."""
    yaml_content = """
field:
  - name: "Test Category"
    points: 5
    subcategories:
      - name: "Test Subcategory"
        points: 10
"""
    with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        temp_path = Path(f.name)

    try:
        interests = load_research_interests(temp_path)
        assert "field" in interests
        assert interests["field"][0]["name"] == "Test Category"
        assert interests["field"][0]["points"] == 5
        assert interests["field"][0]["subcategories"][0]["name"] == "Test Subcategory"
    finally:
        temp_path.unlink()
