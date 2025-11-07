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

from common.parsers import add_postgresql_arguments


def update_postgresql_field(
    connection_string: str, table: str, set_clause: str, where_clause: str
):
    """
    Update a specific field in a PostgreSQL table for multiple records.

    Args:
        connection_string (str): PostgreSQL connection string.
        table (str): Name of the table to update.
        set_clause (str): Clause specifying the update (e.g., "field_name = 'value'").
        where_clause (str): Clause specifying the condition for the update (e.g., "id_field = 'value'").

    Returns:
        None
    """
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
        description="Update a specific field in a PostgreSQL table for multiple records."
    )
    parser = add_postgresql_arguments(parser)
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

    args = parser.parse_args()

    update_postgresql_field(
        args.connection_string, args.table, args.set_clause, args.where_clause
    )
