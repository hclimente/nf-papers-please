#!/usr/bin/env python
import argparse
import logging

from common.parsers import (
    add_duckdb_arguments,
    add_postgresql_arguments,
    add_output_argument,
)
from common.utils import build_pg_connection_string


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
        "--where_clause",
        type=str,
        help="Clause specifying the condition for the extraction (e.g., `id_field = 'value'`).",
    )
    return parser


def extract_fields(
    table: str,
    columns: str,
    out: str,
    db_type: str,
    db_path: str = None,
    connection_string: str = None,
    where_clause: str = "",
    sep: str = "\t",
) -> None:
    """
    Extract specific fields from a database table based on a condition.

    Args:
        table (str): Name of the table to extract from.
        columns (str): Columns to select (e.g., "id, title, summary").
        out (str): Path to the output TSV file.
        db_type (str): Database type ("duckdb" or "postgresql").
        db_path (str): Path to the DuckDB database file (required for duckdb).
        connection_string (str): PostgreSQL connection string (required for postgresql).
        where_clause (str): Clause specifying the condition for the extraction (e.g., "id_field = 'value'").
        sep (str): Separator for the output TSV file. Defaults to tab character.

    Returns:
        None
    """
    if where_clause:
        where_clause = f"WHERE {where_clause} "

    if db_type == "duckdb":
        import duckdb

        with duckdb.connect(db_path) as con:
            query = f"SELECT {columns} FROM {table} {where_clause}"
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
                query = f"SELECT {columns} FROM {table} {where_clause}"
                cur.execute(query)
                result = cur.fetchall()

    with open(out, "w") as f:
        header = columns.split(", ")
        f.write(f"{sep.join(header)}\n")
        for row in result:
            f.write(f"{sep.join(map(str, row))}\n")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description="Extract fields from a database table to a TSV file."
    )

    subparsers = parser.add_subparsers(
        dest="db_type", required=True, help="Database backend to use"
    )

    duckdb_parser = subparsers.add_parser(
        "duckdb", help="Use DuckDB as the database backend"
    )
    duckdb_parser = add_duckdb_arguments(duckdb_parser)
    duckdb_parser = add_common_db_arguments(duckdb_parser)
    duckdb_parser = add_output_argument(duckdb_parser)

    pg_parser = subparsers.add_parser(
        "pg", help="Use PostgreSQL as the database backend"
    )
    pg_parser = add_postgresql_arguments(pg_parser)
    pg_parser = add_common_db_arguments(pg_parser)
    pg_parser = add_output_argument(pg_parser)

    args = parser.parse_args()

    # Build connection string for PostgreSQL
    connection_string = None
    db_path = None
    if args.db_type == "pg":
        connection_string = build_pg_connection_string(args.user, args.host)
    else:  # duckdb
        db_path = args.db_path

    extract_fields(
        table=args.table,
        columns=args.columns,
        out=args.out,
        db_type=args.db_type,
        db_path=db_path,
        connection_string=connection_string,
        where_clause=args.where_clause or "",
    )
