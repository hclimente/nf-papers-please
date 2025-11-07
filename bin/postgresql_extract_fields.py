#!/usr/bin/env python
import argparse

try:
    import psycopg2
except ImportError:
    raise ImportError(
        "psycopg2 is required for PostgreSQL support. "
        "Install it with: pip install psycopg2-binary"
    )

from common.parsers import add_postgresql_arguments


def extract_fields(
    connection_string: str,
    table: str,
    columns: str,
    output_tsv: str,
    where_clause: str = "",
    sep: str = "\t",
) -> None:
    """
    Extract specific fields from a PostgreSQL table based on a condition.

    Args:
        connection_string (str): PostgreSQL connection string.
        table (str): Name of the table to extract from.
        columns (str): Columns to select (e.g., "id, title, summary").
        output_tsv (str): Path to the output TSV file.
        where_clause (str): Clause specifying the condition for the extraction (e.g., "id_field = 'value'").
        sep (str): Separator for the output TSV file. Defaults to tab character.

    Returns:
        None
    """
    if where_clause:
        where_clause = f"WHERE {where_clause} "

    with psycopg2.connect(connection_string) as conn:
        with conn.cursor() as cur:
            query = f"SELECT {columns} FROM {table} {where_clause}"
            cur.execute(query)
            result = cur.fetchall()

    with open(output_tsv, "w") as f:
        header = columns.split(", ")
        f.write(f"{sep.join(header)}\n")
        for row in result:
            f.write(f"{sep.join(map(str, row))}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract specific fields from a PostgreSQL table based on a condition."
    )
    parser = add_postgresql_arguments(parser)
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
    parser.add_argument(
        "--output_tsv",
        type=str,
        default="output.tsv",
        help="Path to the output TSV file.",
    )

    args = parser.parse_args()

    extract_fields(
        args.connection_string,
        args.table,
        args.columns,
        args.output_tsv,
        args.where_clause,
    )
