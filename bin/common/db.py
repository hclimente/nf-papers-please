"""
Database utilities shared between DuckDB and PostgreSQL implementations.

This module provides common schema definitions, field extractors, and SQL templates
that can be used by both database backends.
"""

from typing import Dict, List, Tuple


# Schema definitions as constants
SOURCES_TABLE_COLUMNS = ["name", "feed_url", "last_checked"]
ARTICLES_TABLE_COLUMNS = [
    "id",
    "title",
    "journal_name",
    "summary",
    "url",
    "date",
    "doi",
    "tags",
    "reasoning",
]

# Field names for insertion (excluding auto-generated id)
ARTICLE_INSERT_FIELDS = [
    "title",
    "summary",
    "url",
    "journal_name",
    "date",
    "doi",
    "tags",
    "reasoning",
]


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
                FOREIGN KEY (journal_name) REFERENCES sources(name),
                PRIMARY KEY (url)
            )
        """
    elif db_type == "postgresql":
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


def extract_article_fields(article: Dict, fields: List[str] = None) -> Tuple:
    """
    Extract fields from an article dictionary for database insertion.

    Args:
        article: Dictionary containing article data
        fields: List of field names to extract (defaults to ARTICLE_INSERT_FIELDS)

    Returns:
        Tuple of field values in the same order as fields
    """
    if fields is None:
        fields = ARTICLE_INSERT_FIELDS

    values = []
    for field in fields:
        if field in ["tags", "reasoning"]:
            # These fields might not exist, use get() with None default
            values.append(article.get(field, None))
        else:
            values.append(article[field])
    return tuple(values)


def get_insert_sources_sql(db_type: str = "duckdb") -> str:
    """
    Get SQL template for inserting sources with conflict handling.

    Args:
        db_type: Either 'duckdb' or 'postgresql'

    Returns:
        SQL INSERT statement with appropriate placeholder style
    """
    if db_type == "duckdb":
        return """
            INSERT OR IGNORE INTO sources (name, feed_url, last_checked)
            VALUES (?, ?, ?)
        """
    elif db_type == "postgresql":
        return """
            INSERT INTO sources (name, feed_url, last_checked)
            VALUES (%s, %s, %s)
            ON CONFLICT (name) DO NOTHING
        """
    else:
        raise ValueError(f"Unknown db_type: {db_type}")


def get_insert_article_sql(db_type: str = "duckdb") -> str:
    """
    Get SQL template for inserting an article.

    Args:
        db_type: Either 'duckdb' or 'postgresql'

    Returns:
        SQL INSERT statement with appropriate placeholder style
    """
    placeholders = (
        "?, ?, ?, ?, ?, ?, ?, ?"
        if db_type == "duckdb"
        else "%s, %s, %s, %s, %s, %s, %s, %s"
    )
    return f"""
        INSERT INTO articles (title, summary, url, journal_name, date, doi, tags, reasoning)
        VALUES ({placeholders})
    """


def get_update_field_sql(
    table: str, field: str, condition_field: str, db_type: str = "duckdb"
) -> str:
    """
    Get SQL template for updating a field.

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


def get_placeholder_style(db_type: str = "duckdb") -> str:
    """
    Get the placeholder style for the database type.

    Args:
        db_type: Either 'duckdb' or 'postgresql'

    Returns:
        Placeholder string ('?' for duckdb, '%s' for postgresql)
    """
    if db_type == "duckdb":
        return "?"
    elif db_type == "postgresql":
        return "%s"
    else:
        raise ValueError(f"Unknown db_type: {db_type}")
