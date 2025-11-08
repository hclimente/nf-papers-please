#!/usr/bin/env python
import argparse
import json
import logging

from common.parsers import (
    add_input_articles_json_argument,
    add_duckdb_arguments,
    add_postgresql_arguments,
    add_output_argument,
)
from common.utils import build_pg_connection_string


def get_select_unprocessed_sql() -> str:
    """
    Get SQL to find unprocessed articles using a temporary table join.

    This query is identical for both DuckDB and PostgreSQL.

    Returns:
        SQL SELECT statement
    """
    return """
        SELECT a.url
        FROM tmp_articles a
        LEFT JOIN articles p
        ON a.url = p.url
        WHERE p.title IS NULL
    """


def get_create_temp_articles_table_sql(db_type: str = "duckdb") -> str:
    """
    Get SQL to create temporary table for articles.

    Args:
        db_type: Either 'duckdb' or 'postgresql'

    Returns:
        SQL CREATE TABLE statement
    """
    table_type = "TEMPORARY" if db_type == "duckdb" else "TEMP"
    return f"""
        CREATE {table_type} TABLE tmp_articles (
            url TEXT
        )
    """


def remove_unprocessed_articles(
    articles_json: str,
    output_json: str,
    db_type: str,
    db_path: str = None,
    connection_string: str = None,
) -> None:
    """
    Remove articles that have already been processed from a JSON file using a database.

    Args:
        articles_json (str): Path to the JSON file containing articles.
        output_json (str): Path to the output JSON file containing unprocessed articles.
        db_type (str): Database type ("duckdb" or "postgresql").
        db_path (str): Path to the DuckDB database file (required for duckdb).
        connection_string (str): PostgreSQL connection string (required for postgresql).

    Returns:
        None
    """

    logging.info("-" * 20)
    logging.info(f"articles_json : {articles_json}")
    logging.info(f"output_json   : {output_json}")
    logging.info(f"db_type       : {db_type}")
    logging.info("-" * 20)

    articles = json.load(open(articles_json, "r"))
    logging.info(f"Loaded {len(articles)} articles from {articles_json}.")

    urls = [a["url"] for a in articles]

    # Handle empty articles list
    if not urls:
        logging.info("No articles to process.")
        return

    if db_type == "duckdb":
        import duckdb

        with duckdb.connect(db_path) as con:
            con.execute(
                """
                CREATE TEMPORARY TABLE tmp_articles (
                    url TEXT,
                );
            """
            )

            con.executemany(
                """
                INSERT INTO tmp_articles (url)
                VALUES (?);
            """,
                [(url,) for url in urls],
            )

            result = con.execute(get_select_unprocessed_sql()).fetchall()
            logging.info(f"Found {len(result)} unprocessed articles.")

    elif db_type == "pg":
        try:
            import psycopg2
            from psycopg2.extras import execute_values
        except ImportError:
            raise ImportError(
                "psycopg2 is required for PostgreSQL support. "
                "Install it with: pip install psycopg2-binary"
            )

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
        description="Remove articles that have already been processed from a JSON file using a database."
    )

    # Create subparsers for each database type
    subparsers = parser.add_subparsers(
        dest="db_type", required=True, help="Database backend to use"
    )

    duckdb_parser = subparsers.add_parser(
        "duckdb", help="Use DuckDB as the database backend"
    )
    duckdb_parser = add_duckdb_arguments(duckdb_parser)
    duckdb_parser = add_input_articles_json_argument(duckdb_parser)
    duckdb_parser = add_output_argument(duckdb_parser)

    pg_parser = subparsers.add_parser(
        "pg", help="Use PostgreSQL as the database backend"
    )
    pg_parser = add_postgresql_arguments(pg_parser)
    pg_parser = add_input_articles_json_argument(pg_parser)
    pg_parser = add_output_argument(pg_parser)

    args = parser.parse_args()

    # Build connection string for PostgreSQL
    connection_string = None
    db_path = None
    if args.db_type == "pg":
        connection_string = build_pg_connection_string(args.user, args.host)
    else:  # duckdb
        db_path = args.db_path

    remove_unprocessed_articles(
        articles_json=args.articles_json,
        output_json=args.out,
        db_type=args.db_type,
        db_path=db_path,
        connection_string=connection_string,
    )
