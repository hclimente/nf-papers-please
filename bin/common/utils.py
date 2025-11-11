import logging
import os

from .models import Article, ArticleTable


def get_common_variations(expected_values: list):
    """
    Generate common variations of expected values (case, quotes, punctuation).

    Args:
        expected_values (list): List of expected values.

    Returns:
        dict: Mapping of variations to normalized values.
    """
    d = {}

    for v in expected_values:
        d[v] = v
        d[v.lower()] = v
        d[v.upper()] = v
        d[v.capitalize()] = v
        d[v.title()] = v

    update = {}
    for k, v in d.items():
        update[f"'{k}'"] = v
        update[f'"{k}"'] = v
        update[f"{k}."] = v

    d.update(update)
    return d


def get_env_variable(var_name: str, raise_error: bool = False) -> str:
    """
    Retrieve the value of an environment variable.

    Args:
        var_name (str): The name of the environment variable.
        raise_error (bool): Whether to raise an error if the variable is not found.

    Returns:
        str: The value of the environment variable.

    Raises:
        ValueError: If the environment variable is not found and raise_error is True.
    """
    value = os.environ.get(var_name)

    if not value:
        error_msg = f"{var_name} environment variable not found."
        logging.error(f"❌ {error_msg}")
        if raise_error:
            raise ValueError(error_msg)
    return value


def article_to_text(article: Article | ArticleTable) -> str:
    """
    Deprecated: Use article.to_embedding_text() instead.

    Prepare the text representation of an article for embedding.

    Args:
        article: The article object.

    Returns:
        str: The text representation of the article.
    """
    return article.to_embedding_text()


def prune_article_for_classification(article: Article) -> Article:
    """
    Deprecated: Use article.prune_for_classification() instead.

    Create a pruned copy of an article with only fields needed for classification.

    Keeps: title, journal, authors (first and last only), summary, tags, doi, nearest_neighbors.
    Removes all other fields to reduce token usage in LLM prompts.
    Recursively prunes any Article objects in nearest_neighbors.

    Args:
        article: The full article object.

    Returns:
        Article: A pruned copy with only classification-relevant fields.
    """
    return article.prune_for_classification()
