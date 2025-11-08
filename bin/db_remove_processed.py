#!/usr/bin/env python
import argparse
import logging
import pathlib

from common.models import ArticleList, Article, pprint
from common.parsers import (
    add_input_articles_json_argument,
    add_duckdb_arguments,
    add_postgresql_arguments,
    add_output_argument,
)
from common.utils import build_connection_string


from sqlalchemy import Table, Column, String, text
from sqlmodel import Session, create_engine


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
        db_type: Either 'duckdb' or 'pg'

    Returns:
        SQL CREATE TABLE statement
    """
    if db_type == "duckdb":
        return """
        CREATE TEMPORARY TABLE tmp_articles (
            url TEXT
        )
    """
    elif db_type == "pg":
        return """
        CREATE TEMP TABLE IF NOT EXISTS tmp_articles (
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
        db_type (str): Database type ("duckdb" or "pg").
        db_path (str): Path to the DuckDB database file (required for duckdb).
        connection_string (str): PostgreSQL connection string (required for pg).

    Returns:
        None
    """

    logging.info("-" * 20)
    logging.info(f"articles_json : {articles_json}")
    logging.info(f"output_json   : {output_json}")
    logging.info(f"db_type       : {db_type}")
    logging.info("-" * 20)

    json_string = pathlib.Path(articles_json).read_text()
    articles = ArticleList.validate_json(json_string)
    logging.info(f"Loaded {len(articles)} articles from {articles_json}.")

    article_table = Article.__table__

    metadata = article_table.metadata

    # Create a temporary table with only the url column
    tmp_table = Table(
        "tmp_articles",
        metadata,
        Column("url", String, nullable=False),
        prefixes=["TEMPORARY"],
    )

    engine = create_engine(connection_string)

    with Session(engine) as session:
        # This executes the CREATE TEMPORARY TABLE statement
        tmp_table.create(bind=session.bind, checkfirst=True)
        print("Temporary table created in the current session.")

        # insert only the urls
        session.execute(
            tmp_table.insert(),
            [{"url": article.url} for article in articles],
        )
        logging.info(f"Inserted {len(articles)} articles into the temporary table.")

        # left join to find unprocessed articles (those not in the article table)
        result = session.exec(
            text("""
            SELECT a.url
            FROM tmp_articles a
            LEFT JOIN article p
            ON a.url = p.url
            WHERE p.url IS NULL
            """)
        ).all()

        logging.info(f"Found {len(result)} unprocessed articles.")

        session.commit()

        # Drop the temporary table to ensure cleanup
        tmp_table.drop(bind=session.bind, checkfirst=True)

    # Extract URLs from result tuples
    unprocessed_urls = {url for (url,) in result}
    unprocessed_articles = [a for a in articles if a.url in unprocessed_urls]

    with open(output_json, "w") as f:
        f.write(pprint(unprocessed_articles))


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
        connection_string = build_connection_string(args.user, args.host)
    else:  # duckdb
        db_path = args.db_path

    remove_unprocessed_articles(
        articles_json=args.articles_json,
        output_json=args.out,
        db_type=args.db_type,
        db_path=db_path,
        connection_string=connection_string,
    )
