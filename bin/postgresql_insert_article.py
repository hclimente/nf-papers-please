#!/usr/bin/env python
import argparse
import json
import logging

import psycopg2

from common.db import extract_article_fields, get_insert_article_sql
from common.parsers import (
    add_input_articles_json_argument,
    add_postgresql_arguments,
)


def insert_article(
    connection_string: str,
    articles_json: str,
) -> None:
    """
    Insert articles from a JSON file into a PostgreSQL database.

    Args:
        connection_string (str): PostgreSQL connection string.
            Format: postgresql://user:password@host:port/database # pragma: allowlist secret
            Example: postgresql://myuser:mypass@localhost:5432/papers_db # pragma: allowlist secret
        articles_json (str): Path to the JSON file containing articles.

    Returns:
        None
    """

    articles = json.load(open(articles_json, "r"))
    logging.info(f"Loaded {len(articles)} articles from {articles_json}.")

    insert_sql = get_insert_article_sql(db_type="postgresql")

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
        description="Insert articles from a JSON file into a PostgreSQL database."
    )

    parser = add_input_articles_json_argument(parser)
    parser = add_postgresql_arguments(parser)

    args = parser.parse_args()

    insert_article(
        args.connection_string,
        args.articles_json,
    )
