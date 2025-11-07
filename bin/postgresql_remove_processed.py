#!/usr/bin/env python
import argparse
import json
import logging

try:
    import psycopg2
    from psycopg2.extras import execute_values
except ImportError:
    raise ImportError(
        "psycopg2 is required for PostgreSQL support. "
        "Install it with: pip install psycopg2-binary"
    )

from common.db import (
    get_create_temp_articles_table_sql,
    get_select_unprocessed_sql,
)
from common.parsers import (
    add_input_articles_json_argument,
    add_postgresql_arguments,
)


def remove_unprocessed_articles(
    connection_string: str,
    articles_json: str,
    output_json: str,
) -> None:
    """
    Remove articles that have already been processed from a JSON file using a PostgreSQL database.

    Args:
        connection_string (str): PostgreSQL connection string.
        articles_json (str): Path to the JSON file containing articles.
        output_json (str): Path to the output JSON file containing unprocessed articles.

    Returns:
        None
    """

    logging.info("-" * 20)
    logging.info(f"connection_string : {connection_string}")
    logging.info(f"articles_json     : {articles_json}")
    logging.info(f"output_json       : {output_json}")
    logging.info("-" * 20)

    articles = json.load(open(articles_json, "r"))
    logging.info(f"Loaded {len(articles)} articles from {articles_json}.")

    urls = [a["url"] for a in articles]

    # Handle empty articles list
    if not urls:
        logging.info("No articles to process.")
        return

    with psycopg2.connect(connection_string) as conn:
        with conn.cursor() as cur:
            cur.execute(get_create_temp_articles_table_sql(db_type="postgresql"))

            # Use execute_values for efficient batch insert
            execute_values(
                cur,
                "INSERT INTO tmp_articles (url) VALUES %s",
                [(url,) for url in urls],
            )

            cur.execute(get_select_unprocessed_sql())
            result = cur.fetchall()
            logging.info(f"Found {len(result)} unprocessed articles.")

    unprocessed_articles = [a for a in articles if (a["url"],) in result]

    if unprocessed_articles:
        json.dump(unprocessed_articles, open(output_json, "w"), indent=2)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description="Remove articles that have already been processed from a JSON file using a PostgreSQL database."
    )

    parser = add_input_articles_json_argument(parser)
    parser = add_postgresql_arguments(parser)
    parser.add_argument(
        "--output_json",
        type=str,
        required=True,
        help="Path to the output JSON file.",
    )

    args = parser.parse_args()

    remove_unprocessed_articles(
        args.connection_string,
        args.articles_json,
        args.output_json,
    )
