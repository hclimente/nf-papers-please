#!/usr/bin/env python
import argparse
import logging

from common.parsers import (
    add_duckdb_arguments,
    add_postgresql_arguments,
)
from common.utils import build_pg_connection_string


def add_common_db_arguments(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """
    Add common database arguments to an argparse parser.

    Args:
        parser: An argparse.ArgumentParser instance

    Returns:
        The modified argparse.ArgumentParser instance
    """
    parser.add_argument(
        "--table",
        type=str,
        required=True,
        help="Name of the table to update.",
    )
    parser.add_argument(
        "--where_clause",
        type=str,
        required=True,
        help="Clause specifying the condition for the update (e.g., `id_field = 'value'`).",
    )
    parser.add_argument(
        "--set_clause",
        type=str,
        required=True,
        help="Clause specifying the update (e.g., `field_name = 'value'`).",
    )
    return parser


def get_update_field_sql(
    table: str, field: str, condition_field: str, db_type: str = "duckdb"
) -> str:
    """
    Get SQL template for updating a field.

    Note: This is a legacy function that uses string formatting.
    For production use, consider using parameterized queries.

    Args:
        table: Table name
        field: Field to update
        condition_field: Field to use in WHERE clause
        db_type: Either 'duckdb' or 'postgresql'

    Returns:
        SQL UPDATE statement with appropriate placeholder style
    """
    placeholder = "?" if db_type == "duckdb" else "%s"
    return f"""
        UPDATE {table}
        SET {field} = {placeholder}
        WHERE {condition_field} = {placeholder}
    """


def update_field(
    table: str,
    set_clause: str,
    where_clause: str,
    db_type: str,
    db_path: str = None,
    connection_string: str = None,
) -> None:
    """
    Update a specific field in a database table for multiple records.

    Args:
        table (str): Name of the table to update.
        set_clause (str): Clause specifying the update (e.g., "field_name = 'value'").
        where_clause (str): Clause specifying the condition for the update (e.g., "id_field = 'value'").
        db_type (str): Database type ("duckdb" or "postgresql").
        db_path (str): Path to the DuckDB database file (required for duckdb).
        connection_string (str): PostgreSQL connection string (required for postgresql).

    Returns:
        None
    """
    if db_type == "duckdb":
        import duckdb

        with duckdb.connect(db_path) as con:
            logging.info(
                f"⌛ Began updating {table} with {set_clause} where {where_clause}..."
            )
            con.execute(
                f"""
                UPDATE {table}
                SET {set_clause}
                WHERE {where_clause}
            """
            )
            logging.info("✅ Done updating field")

    elif db_type == "postgresql":
        try:
            import psycopg2
        except ImportError:
            raise ImportError(
                "psycopg2 is required for PostgreSQL support. "
                "Install it with: pip install psycopg2-binary"
            )

        with psycopg2.connect(connection_string) as conn:
            with conn.cursor() as cur:
                logging.info(
                    f"⌛ Began updating {table} with {set_clause} where {where_clause}..."
                )
                cur.execute(
                    f"""
                    UPDATE {table}
                    SET {set_clause}
                    WHERE {where_clause}
                """
                )
                conn.commit()
                logging.info("✅ Done updating field")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Update a specific field in a database table for multiple records."
    )

    # Create subparsers for each database type
    subparsers = parser.add_subparsers(
        dest="db_type", required=True, help="Database backend to use"
    )

    duckdb_parser = subparsers.add_parser(
        "duckdb", help="Use DuckDB as the database backend"
    )
    duckdb_parser = add_duckdb_arguments(duckdb_parser)
    duckdb_parser = add_common_db_arguments(duckdb_parser)

    pg_parser = subparsers.add_parser(
        "pg", help="Use PostgreSQL as the database backend"
    )
    pg_parser = add_postgresql_arguments(pg_parser)
    pg_parser = add_common_db_arguments(pg_parser)

    args = parser.parse_args()

    # Build connection string for PostgreSQL
    connection_string = None
    db_path = None
    if args.db_type == "pg":
        connection_string = build_pg_connection_string(args.user, args.host)
    else:  # duckdb
        db_path = args.db_path

    update_field(
        table=args.table,
        set_clause=args.set_clause,
        where_clause=args.where_clause,
        db_type=args.db_type,
        db_path=db_path,
        connection_string=connection_string,
    )
