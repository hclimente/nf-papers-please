#!/usr/bin/env python
import argparse
import logging
import pathlib

from common.models import Article, ArticleList, pprint
from common.parsers import (
    add_input_articles_json_argument,
    add_duckdb_arguments,
    add_postgresql_arguments,
    add_output_argument,
)
from common.db import (
    build_connection_string,
    setup_db,
)


def add_common_db_arguments(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """
    Add common database arguments to the parser.

    Args:
        parser (argparse.ArgumentParser): The argument parser to add arguments to.

    Returns:
        argparse.ArgumentParser: The updated argument parser.
    """
    parser.add_argument(
        "--table",
        type=str,
        required=True,
        help="Name of the table to extract from.",
    )
    parser.add_argument(
        "--columns",
        type=str,
        required=True,
        help="Clause specifying the columns to select (e.g., `id, title, summary`).",
    )
    parser.add_argument(
        "--clause",
        type=str,
        help="Clause specifying the condition for the extraction (e.g., `id_field = 'value'`).",
    )
    return parser


def fetch_articles(doi_list: str, db_type: str) -> list[Article]:
    article_list = []

    if db_type == "pg":
        try:
            import psycopg2
        except ImportError:
            raise ImportError(
                "psycopg2 is required for PostgreSQL support. "
                "Install it with: pip install psycopg2-binary"
            )

        with psycopg2.connect(connection_string) as conn:
            with conn.cursor() as cur:
                query = f"SELECT title, authors, summary, doi, url, journal_name, date, tags FROM articles WHERE doi IN ('{"', '".join(doi_list)}')"
                logging.debug(f"Executing query: {query}")
                cur.execute(query)
                result = cur.fetchall()

    for row in result:
        article = Article(
            title=row[0],
            authors=row[1],
            summary=row[2],
            doi=row[3],
            url=row[4],
            journal_name=row[5],
            date=row[6],
            tags=row[7],
        )
        article_list.append(article)

    return article_list


def extract_fields(
    articles_json: str,
    table: str,
    columns: str,
    out: str,
    db_type: str,
    db_path: str = None,
    connection_string: str = None,
    clause: str = "",
    sep: str = "\t",
) -> None:
    """
    Extract specific fields from a database table based on a condition.

    Args:
        articles_json (str): Path to the articles JSON file.
        table (str): Name of the table to extract from.
        columns (str): Columns to select (e.g., "id, title, summary").
        out (str): Path to the output TSV file.
        db_type (str): Database type ("duckdb" or "postgresql").
        db_path (str): Path to the DuckDB database file (required for duckdb).
        connection_string (str): PostgreSQL connection string (required for postgresql).
        clause (str): Clause specifying the condition for the extraction (e.g., "WHERE id_field = 'value'").
        sep (str): Separator for the output TSV file. Defaults to tab character.

    Returns:
        None
    """

    json_string = pathlib.Path(articles_json).read_text()
    articles = ArticleList.validate_json(json_string)
    logging.info(f"Loaded {len(articles)} articles.")

    for item in articles:
        article_clause = clause.format(embedding=item.embedding)

        if db_type == "duckdb":
            import duckdb

            with duckdb.connect(db_path) as con:
                query = f"SELECT {columns} FROM {table} {article_clause}"
                logging.debug(f"Executing query: {query}")
                result = con.execute(query).fetchall()

        elif db_type == "pg":
            try:
                import psycopg2
            except ImportError:
                raise ImportError(
                    "psycopg2 is required for PostgreSQL support. "
                    "Install it with: pip install psycopg2-binary"
                )

            with psycopg2.connect(connection_string) as conn:
                with conn.cursor() as cur:
                    query = f"SELECT {columns} FROM {table} {article_clause}"
                    logging.debug(f"Executing query: {query}")
                    cur.execute(query)
                    result = cur.fetchall()

        nearest_neighbors = fetch_articles([row[0] for row in result], db_type)
        setattr(item, "nearest_neighbors", nearest_neighbors)

    with open(out, "w") as f:
        f.write(pprint(articles))


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser(
        description="Extract fields from a database table to a TSV file."
    )

    subparsers = parser.add_subparsers(
        dest="db_type", required=True, help="Database backend to use"
    )

    duckdb_parser = subparsers.add_parser(
        "duckdb", help="Use DuckDB as the database backend"
    )
    duckdb_parser = add_input_articles_json_argument(duckdb_parser)
    duckdb_parser = add_duckdb_arguments(duckdb_parser)
    duckdb_parser = add_common_db_arguments(duckdb_parser)
    duckdb_parser = add_output_argument(duckdb_parser)

    pg_parser = subparsers.add_parser(
        "pg", help="Use PostgreSQL as the database backend"
    )
    pg_parser = add_input_articles_json_argument(pg_parser)
    pg_parser = add_postgresql_arguments(pg_parser)
    pg_parser = add_common_db_arguments(pg_parser)
    pg_parser = add_output_argument(pg_parser)

    args = parser.parse_args()

    # Build connection string for PostgreSQL
    connection_string = None
    db_path = None
    if args.db_type == "pg":
        connection_string = build_connection_string(args.user, args.host)
    else:  # duckdb
        db_path = args.db_path

    setup_db(connection_string)

    extract_fields(
        articles_json=args.articles_json,
        table=args.table,
        columns=args.columns,
        out=args.out,
        db_type=args.db_type,
        db_path=db_path,
        connection_string=connection_string,
        clause=args.clause or "",
    )
