#!/usr/bin/env python
import argparse
import logging
import pathlib

from sqlmodel import Session, create_engine, select

from common.models import (
    ArticleList,
    ArticleTable,
    Author,
    AuthorTable,
    JournalTable,
    Tag,
)
from common.parsers import (
    add_input_articles_json_argument,
    add_postgresql_arguments,
)
from common.db import (
    build_connection_string,
    setup_db,
)


def get_or_create_journal(
    session: Session, name: str, short_name: str | None
) -> "JournalTable":
    """
    Find an existing journal or create a new one.

    Args:
        session: SQLModel session.
        name: Journal name string.
        short_name: Journal short name string or None.
    Returns:
        JournalTable instance.
    """
    from common.models import JournalTable

    statement = select(JournalTable).where(JournalTable.name == name)
    journal = session.exec(statement).first()

    if not journal:
        journal = JournalTable(name=name, short_name=short_name)
        session.add(journal)

    return journal


def get_or_create_author(session: Session, author_data: Author) -> AuthorTable:
    """
    Find an existing author or create a new one.

    Args:
        session: SQLModel session.
        author_data: author data

    Returns:
        AuthorTable instance.
    """
    statement = select(AuthorTable).where(
        AuthorTable.first_name == author_data.first_name,
        AuthorTable.last_name == author_data.last_name,
    )
    author = session.exec(statement).first()

    if not author:
        author = AuthorTable(**author_data.model_dump())
        session.add(author)

    return author


def get_or_create_tag(session: Session, tag_name: str) -> Tag:
    """
    Find an existing tag or create a new one.

    Args:
        session: SQLModel session.
        tag_name: Tag name string.

    Returns:
        Tag instance.
    """
    statement = select(Tag).where(Tag.name == tag_name)
    tag = session.exec(statement).first()

    if not tag:
        tag = Tag(name=tag_name)
        session.add(tag)

    return tag


def convert_article_to_table(article, session: Session) -> ArticleTable:
    """
    Convert Article (Pydantic) to ArticleTable (SQLModel) with relationships.

    Args:
        article: Article instance (Pydantic model).
        session: SQLModel session.

    Returns:
        ArticleTable instance with authors and tags linked.
    """
    # Convert Article to ArticleTable
    article_table = ArticleTable(
        **article.model_dump(exclude={"authors", "tags", "embedding"})
    )

    if article.journal_name:
        article_table.journal = get_or_create_journal(
            session, article.journal_name, article.journal_short_name
        )

    if article.authors:
        for author_data in article.authors:
            author = get_or_create_author(session, author_data)
            article_table.authors.append(author)

    if article.embedding:
        article_table.embedding = article.embedding

    if article.tags:
        for tag_name in article.tags:
            tag = get_or_create_tag(session, tag_name)
            article_table.tags.append(tag)

    return article_table


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
        for article in articles:
            article_table = convert_article_to_table(article, session)
            session.add(article_table)

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
