#!/usr/bin/env python
import argparse
import logging
from typing import List, Tuple

from common.parsers import (
    add_duckdb_arguments,
    add_postgresql_arguments,
)
from common.utils import build_pg_connection_string


def add_common_db_arguments(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """
    Add common database arguments to an argument parser.

    Args:
        parser (argparse.ArgumentParser): The argument parser to add arguments to.

    Returns:
        argparse.ArgumentParser: The modified parser.
    """
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
    return parser


def get_sources_table_schema() -> str:
    """
    Get the CREATE TABLE statement for the sources table.

    This schema is identical for both DuckDB and PostgreSQL.

    Returns:
        SQL CREATE TABLE statement
    """
    return """
        CREATE TABLE IF NOT EXISTS sources (
            name TEXT PRIMARY KEY,
            feed_url TEXT NOT NULL,
            last_checked TEXT NOT NULL
        )
    """


def get_articles_table_schema(db_type: str = "duckdb") -> str:
    """
    Get the CREATE TABLE statement(s) for the articles table.

    For DuckDB, this includes the sequence creation statement.
    For PostgreSQL, only the table creation (SERIAL handles sequence automatically).

    Args:
        db_type: Either 'duckdb' or 'postgresql'

    Returns:
        SQL statement(s) to create articles table (and sequence if needed)
    """
    if db_type == "duckdb":
        return """
            CREATE SEQUENCE IF NOT EXISTS article_id_seq START 1;
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER DEFAULT NEXTVAL('article_id_seq'),
                title TEXT NOT NULL,
                journal_name TEXT,
                summary TEXT NOT NULL,
                url TEXT NOT NULL,
                date DATE NOT NULL,
                doi TEXT DEFAULT NULL,
                tags TEXT[] DEFAULT NULL,
                reasoning TEXT DEFAULT NULL,
                embedding FLOAT[3072] DEFAULT NULL,
                FOREIGN KEY (journal_name) REFERENCES sources(name),
                PRIMARY KEY (url)
            )
        """
    elif db_type == "pg":
        return """
            CREATE TABLE IF NOT EXISTS articles (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                journal_name TEXT,
                summary TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                date DATE NOT NULL,
                doi TEXT DEFAULT NULL,
                tags TEXT[] DEFAULT NULL,
                reasoning TEXT DEFAULT NULL,
                embedding VECTOR(3072),
                FOREIGN KEY (journal_name) REFERENCES sources(name)
            )
        """
    else:
        raise ValueError(f"Unknown db_type: {db_type}")


def parse_journals_tsv(journals_tsv_path: str) -> List[Tuple[str, str]]:
    """
    Parse a journals TSV file and return a list of (name, feed_url) tuples.

    Args:
        journals_tsv_path: Path to the TSV file

    Returns:
        List of (journal_name, feed_url) tuples
    """
    journals = []
    with open(journals_tsv_path, "r") as f:
        f.readline()  # skip header
        for line in f:
            if line.strip() == "":
                continue
            name, feed_url = line.strip().split("\t")
            journals.append((name, feed_url))
    return journals


def get_insert_sources_sql(db_type: str = "duckdb") -> str:
    """
    Get SQL template for inserting sources with conflict handling.

    Args:
        db_type: Either 'duckdb' or 'pg'

    Returns:
        SQL INSERT statement with appropriate placeholder style
    """
    if db_type == "duckdb":
        return """
            INSERT OR IGNORE INTO sources (name, feed_url, last_checked)
            VALUES (?, ?, ?)
        """
    elif db_type == "pg":
        return """
            INSERT INTO sources (name, feed_url, last_checked)
            VALUES (%s, %s, %s)
            ON CONFLICT (name) DO NOTHING
        """
    else:
        raise ValueError(f"Unknown db_type: {db_type}")


def install_extensions(db_type: str = "duckdb") -> str:
    """
    Get SQL to install necessary extensions.

    Args:
        db_type: Either 'duckdb' or 'postgresql'

    Returns:
        SQL statement to install extensions
    """
    if db_type == "duckdb":
        pass
    elif db_type == "pg":
        return "CREATE EXTENSION vector;"
    else:
        raise ValueError(f"Unknown db_type: {db_type}")


def create_journal_table(
    journals_tsv: str,
    global_cutoff_date: str,
    db_type: str,
    db_path: str = None,
    connection_string: str = None,
) -> None:
    """
    Create and populate the sources table in the database.

    Args:
        journals_tsv (str): Path to the TSV file containing journal names and RSS feed URLs.
        global_cutoff_date (str): Global cutoff date for articles in ISO 8601 format (YYYY-MM-DD).
        db_type (str): Database type ("duckdb" or "postgresql").
        db_path (str): Path to the DuckDB database file (required for duckdb).
        connection_string (str): PostgreSQL connection string (required for postgresql).
    """
    logging.info("-" * 20)
    logging.info("Called create_journal_table with the following arguments:")
    logging.info(f"journals_tsv       : {journals_tsv}")
    logging.info(f"db_type            : {db_type}")
    logging.info(f"global_cutoff_date : {global_cutoff_date}")
    logging.info("-" * 20)

    journals = parse_journals_tsv(journals_tsv)
    sources = [(name, feed_url, global_cutoff_date) for name, feed_url in journals]

    if db_type == "duckdb":
        import duckdb

        with duckdb.connect(db_path) as con:
            logging.info("⌛ Began creating sources table...")
            con.execute(get_sources_table_schema())
            logging.info("✅ Done creating sources table")

            logging.info("⌛ Began inserting journal sources...")
            con.executemany(get_insert_sources_sql(db_type="duckdb"), sources)
            logging.info("✅ Done inserting journal sources")

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
                logging.info("⌛ Began creating sources table...")
                cur.execute(get_sources_table_schema())
                conn.commit()
                logging.info("✅ Done creating sources table")

                logging.info("⌛ Began inserting journal sources...")
                insert_sql = get_insert_sources_sql(db_type="pg")
                for source in sources:
                    cur.execute(insert_sql, source)
                conn.commit()
                logging.info("✅ Done inserting journal sources")

                logging.info("⌛ Installing extensions...")
                cur.execute(install_extensions(db_type="pg"))
                conn.commit()
                logging.info("✅ Done installing extensions")


def create_articles_table(
    db_type: str, db_path: str = None, connection_string: str = None
) -> None:
    """
    Create the articles table in the database.

    Args:
        db_type (str): Database type ("duckdb" or "postgresql").
        db_path (str): Path to the DuckDB database file (required for duckdb).
        connection_string (str): PostgreSQL connection string (required for postgresql).
    """
    logging.info("-" * 20)
    logging.info("Called create_articles_table with the following arguments:")
    logging.info(f"db_type : {db_type}")
    logging.info("-" * 20)

    if db_type == "duckdb":
        import duckdb

        with duckdb.connect(db_path) as con:
            logging.info("⌛ Began creating articles table...")
            con.execute(get_articles_table_schema(db_type="duckdb"))
            logging.info("✅ Done creating articles table")

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
                logging.info("⌛ Began creating articles table...")
                cur.execute(get_articles_table_schema(db_type="pg"))
                conn.commit()
                logging.info("✅ Done creating articles table")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description="Create database tables for storing articles from RSS feeds."
    )

    # Create subparsers for each database type
    subparsers = parser.add_subparsers(
        dest="db_type", required=True, help="Database backend to use"
    )

    # DuckDB subcommand
    duckdb_parser = subparsers.add_parser(
        "duckdb", help="Use DuckDB as the database backend"
    )
    duckdb_parser = add_duckdb_arguments(duckdb_parser)
    duckdb_parser = add_common_db_arguments(duckdb_parser)

    # PostgreSQL subcommand
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

    create_journal_table(
        journals_tsv=args.journals_tsv,
        global_cutoff_date=args.global_cutoff_date,
        db_type=args.db_type,
        db_path=db_path,
        connection_string=connection_string,
    )
    create_articles_table(
        db_type=args.db_type,
        db_path=db_path,
        connection_string=connection_string,
    )
