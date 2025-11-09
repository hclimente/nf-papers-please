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
    Prepare the text representation of an article for embedding.

    Args:
        article: The article object.

    Returns:
        str: The text representation of the article.
    """
    return f"""
Title: {article.title}
Journal: {article.journal if isinstance(article, Article) else article.journal}
First Author: {article.authors[0] if article.authors else "N/A"}
Last Author: {article.authors[-1] if article.authors else "N/A"}
Summary: {article.summary}
Tags: {", ".join(str(tag) for tag in article.tags) if article.tags else "N/A"}
"""
