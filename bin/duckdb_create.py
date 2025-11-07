#!/usr/bin/env python
import argparse
import logging

import duckdb

from common.db import (
    get_articles_table_schema,
    get_insert_sources_sql,
    get_sources_table_schema,
    parse_journals_tsv,
)
from common.parsers import add_duckdb_arguments


def create_journal_table(journals_tsv: str, db_path: str, global_cutoff_date: str):
    """
    Create and populate the sources table in the database.

    Args:
        journals_tsv (str): Path to the TSV file containing journal names and RSS feed URLs.
        db_path (str): Path to the DuckDB database file.
        global_cutoff_date (str): Global cutoff date for articles in ISO 8601 format (YYYY-MM-DD).
    """
    logging.info("-" * 20)
    logging.info("Called create_journal_table with the following arguments:")
    logging.info(f"journals_tsv       : {journals_tsv}")
    logging.info(f"db_path            : {db_path}")
    logging.info(f"global_cutoff_date : {global_cutoff_date}")
    logging.info("-" * 20)

    with duckdb.connect(db_path) as con:
        logging.info("⌛ Began creating sources table...")
        con.execute(get_sources_table_schema())
        logging.info("✅ Done creating sources table")

        journals = parse_journals_tsv(journals_tsv)
        sources = [(name, feed_url, global_cutoff_date) for name, feed_url in journals]

        logging.info("⌛ Began inserting journal sources...")
        con.executemany(get_insert_sources_sql(db_type="duckdb"), sources)
        logging.info("✅ Done inserting journal sources")


def create_articles_table(db_path: str):
    """
    Create the articles table in the database.

    Args:
        db_path (str): Path to the DuckDB database file.
    """
    logging.info("-" * 20)
    logging.info("Called create_articles_table with the following arguments:")
    logging.info(f"db_path : {db_path}")
    logging.info("-" * 20)

    with duckdb.connect(db_path) as con:
        logging.info("⌛ Began creating articles table...")
        con.execute(get_articles_table_schema(db_type="duckdb"))
        logging.info("✅ Done creating articles table")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description="Fetch articles from RSS feeds and store them in a database."
    )
    parser = add_duckdb_arguments(parser)
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

    create_journal_table(args.journals_tsv, args.db_path, args.global_cutoff_date)
    create_articles_table(args.db_path)
