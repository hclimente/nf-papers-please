#!/usr/bin/env python
import argparse
import json
import logging
from typing import Dict, List, Tuple

from common.parsers import (
    add_input_articles_json_argument,
    add_duckdb_arguments,
    add_postgresql_arguments,
)

# Field names for insertion (excluding auto-generated id)
ARTICLE_INSERT_FIELDS = [
    "title",
    "summary",
    "url",
    "journal_name",
    "date",
    "doi",
    "tags",
    "reasoning",
]


def extract_article_fields(article: Dict, fields: List[str] = None) -> Tuple:
    """
    Extract fields from an article dictionary for database insertion.

    Args:
        article: Dictionary containing article data
        fields: List of field names to extract (defaults to ARTICLE_INSERT_FIELDS)

    Returns:
        Tuple of field values in the same order as fields
    """
    if fields is None:
        fields = ARTICLE_INSERT_FIELDS

    values = []
    for field in fields:
        if field in ["tags", "reasoning"]:
            # These fields might not exist, use get() with None default
            values.append(article.get(field, None))
        else:
            values.append(article[field])
    return tuple(values)


def get_insert_article_sql(db_type: str = "duckdb") -> str:
    """
    Get SQL template for inserting an article.

    Args:
        db_type: Either 'duckdb' or 'postgresql'

    Returns:
        SQL INSERT statement with appropriate placeholder style
    """
    placeholders = (
        "?, ?, ?, ?, ?, ?, ?, ?"
        if db_type == "duckdb"
        else "%s, %s, %s, %s, %s, %s, %s, %s"
    )
    return f"""
        INSERT INTO articles (title, summary, url, journal_name, date, doi, tags, reasoning)
        VALUES ({placeholders})
    """


def insert_article(
    articles_json: str,
    db_type: str,
    db_path: str = None,
    connection_string: str = None,
) -> None:
    """
    Insert articles from a JSON file into a database.

    Args:
        articles_json (str): Path to the JSON file containing articles.
        db_type (str): Database type ("duckdb" or "postgresql").
        db_path (str): Path to the DuckDB database file (required for duckdb).
        connection_string (str): PostgreSQL connection string (required for postgresql).
            Format: postgresql://user:password@host:port/database # pragma: allowlist secret
            Example: postgresql://myuser:mypass@localhost:5432/papers_db # pragma: allowlist secret

    Returns:
        None
    """

    articles = json.load(open(articles_json, "r"))
    logging.info(f"Loaded {len(articles)} articles from {articles_json}.")

    insert_sql = get_insert_article_sql(db_type=db_type)

    if db_type == "duckdb":
        import duckdb

        for a in articles:
            logging.info(f"Inserting article: {a['title'][:50]}...")

            with duckdb.connect(db_path) as con:
                try:
                    article_values = extract_article_fields(a)
                    con.execute(insert_sql, article_values)
                    logging.info("✅ Article inserted successfully")
                except Exception as e:
                    logging.error(f"❌ Failed to insert article: {e}")
                    raise

    elif db_type == "postgresql":
        try:
            import psycopg2
        except ImportError:
            raise ImportError(
                "psycopg2 is required for PostgreSQL support. "
                "Install it with: pip install psycopg2-binary"
            )

        for a in articles:
            logging.info(f"Inserting article: {a['title'][:50]}...")

            with psycopg2.connect(connection_string) as conn:
                with conn.cursor() as cur:
                    try:
                        article_values = extract_article_fields(a)
                        cur.execute(insert_sql, article_values)
                        conn.commit()
                        logging.info("✅ Article inserted successfully")
                    except Exception as e:
                        conn.rollback()
                        logging.error(f"❌ Failed to insert article: {e}")
                        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description="Insert articles from a JSON file into a database."
    )

    subparsers = parser.add_subparsers(
        dest="db_type", required=True, help="Database backend to use"
    )

    duckdb_parser = subparsers.add_parser(
        "duckdb", help="Use DuckDB as the database backend"
    )
    duckdb_parser = add_duckdb_arguments(duckdb_parser)
    duckdb_parser = add_input_articles_json_argument(duckdb_parser)

    pg_parser = subparsers.add_parser(
        "pg", help="Use PostgreSQL as the database backend"
    )
    pg_parser = add_postgresql_arguments(pg_parser)
    pg_parser = add_input_articles_json_argument(pg_parser)

    args = parser.parse_args()

    insert_article(
        articles_json=args.articles_json,
        db_type=args.db_type,
        db_path=getattr(args, "db_path", None),
        connection_string=getattr(args, "connection_string", None),
    )
