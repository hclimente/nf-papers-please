#!/usr/bin/env python
import argparse
import logging
import pathlib

from sqlmodel import Session, create_engine

from common.models import ArticleList
from common.parsers import (
    add_input_articles_json_argument,
    add_postgresql_arguments,
)
from common.db import (
    build_connection_string,
    setup_db,
)


def insert_article(
    articles_json: str,
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

    json_string = pathlib.Path(articles_json).read_text()
    articles = ArticleList.validate_json(json_string)

    engine = create_engine(connection_string, echo=True)

    with Session(engine) as session:
        session.add_all(articles)
        session.commit()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description="Insert articles from a JSON file into a database."
    )

    subparsers = parser.add_subparsers(
        dest="db_type", required=True, help="Database backend to use"
    )

    pg_parser = subparsers.add_parser(
        "pg", help="Use PostgreSQL as the database backend"
    )
    pg_parser = add_postgresql_arguments(pg_parser)
    pg_parser = add_input_articles_json_argument(pg_parser)

    args = parser.parse_args()

    connection_string = build_connection_string(args.user, args.host)
    setup_db(connection_string)

    insert_article(
        articles_json=args.articles_json,
        connection_string=connection_string,
    )
