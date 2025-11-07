#!/usr/bin/env python
import argparse
import logging

try:
    import psycopg2
except ImportError:
    raise ImportError(
        "psycopg2 is required for PostgreSQL support. "
        "Install it with: pip install psycopg2-binary"
    )

from common.db import (
    get_articles_table_schema,
    get_insert_sources_sql,
    get_sources_table_schema,
    parse_journals_tsv,
)
from common.parsers import add_postgresql_arguments


def create_journal_table(
    journals_tsv: str, connection_string: str, global_cutoff_date: str
):
    """
    Create and populate the sources table in the database.

    Args:
        journals_tsv (str): Path to the TSV file containing journal names and RSS feed URLs.
        connection_string (str): PostgreSQL connection string.
        global_cutoff_date (str): Global cutoff date for articles in ISO 8601 format (YYYY-MM-DD).
    """
    logging.info("-" * 20)
    logging.info("Called create_journal_table with the following arguments:")
    logging.info(f"journals_tsv       : {journals_tsv}")
    logging.info(f"connection_string  : {connection_string}")
    logging.info(f"global_cutoff_date : {global_cutoff_date}")
    logging.info("-" * 20)

    with psycopg2.connect(connection_string) as conn:
        with conn.cursor() as cur:
            logging.info("⌛ Began creating sources table...")
            cur.execute(get_sources_table_schema())
            conn.commit()
            logging.info("✅ Done creating sources table")

            journals = parse_journals_tsv(journals_tsv)
            sources = [
                (name, feed_url, global_cutoff_date) for name, feed_url in journals
            ]

            logging.info("⌛ Began inserting journal sources...")
            insert_sql = get_insert_sources_sql(db_type="postgresql")
            for source in sources:
                cur.execute(insert_sql, source)
            conn.commit()
            logging.info("✅ Done inserting journal sources")


def create_articles_table(connection_string: str):
    """
    Create the articles table in the database.

    Args:
        connection_string (str): PostgreSQL connection string.
    """
    logging.info("-" * 20)
    logging.info("Called create_articles_table with the following arguments:")
    logging.info(f"connection_string : {connection_string}")
    logging.info("-" * 20)

    with psycopg2.connect(connection_string) as conn:
        with conn.cursor() as cur:
            logging.info("⌛ Began creating articles table...")
            cur.execute(get_articles_table_schema(db_type="postgresql"))
            conn.commit()
            logging.info("✅ Done creating articles table")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description="Create PostgreSQL tables for storing articles from RSS feeds."
    )
    parser = add_postgresql_arguments(parser)
    parser.add_argument(
        "--journals_tsv",
        type=str,
        required=True,
        help="Path to the TSV file containing journal names and RSS feed URLs.",
    )
    parser.add_argument(
        "--global_cutoff_date",
        type=str,
        default=None,
        help="Global cutoff date for articles in ISO 8601 format (YYYY-MM-DD). If not provided, uses the current date.",
    )

    args = parser.parse_args()

    create_journal_table(
        args.journals_tsv, args.connection_string, args.global_cutoff_date
    )
    create_articles_table(args.connection_string)
