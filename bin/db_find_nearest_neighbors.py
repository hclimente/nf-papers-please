#!/usr/bin/env python
import argparse
import logging
import pathlib

from sqlmodel import Session, create_engine, select

from common.models import ArticleList, ArticleTable, pprint
from common.parsers import (
    add_input_articles_json_argument,
    add_postgresql_arguments,
    add_output_argument,
)
from common.db import (
    build_connection_string,
    setup_db,
)
from common.utils import (
    article_table_to_article,
    prune_article_for_classification,
)


def find_k_nearest_neighbors(
    articles_json: str,
    out: str,
    k: int = 5,
    connection_string: str = None,
) -> None:
    """
    Extract specific fields from a database table based on a condition.

    Args:
        articles_json (str): Path to the articles JSON file.
        out (str): Path to the output TSV file.
        db_type (str): Database type ("duckdb" or "postgresql").
        connection_string (str): PostgreSQL connection string (required for postgresql).
        k (int): Number of nearest neighbors to fetch based on embedding similarity. Defaults to 5.

    Returns:
        None
    """

    json_string = pathlib.Path(articles_json).read_text()
    articles = ArticleList.validate_json(json_string)
    logging.info(f"Loaded {len(articles)} articles.")

    engine = create_engine(connection_string, echo=True)
    # store articles in pruned form to simplify outputs
    pruned_articles = []

    with Session(engine) as session:
        for item in articles:
            statement = (
                select(ArticleTable)
                .order_by(ArticleTable.embedding.cosine_distance(item.embedding))
                .limit(k)
            )
            results = session.exec(statement).all()

            setattr(
                item,
                "nearest_neighbors",
                [article_table_to_article(a) for a in results],
            )
            pruned_article = prune_article_for_classification(item)
            pruned_articles.append(pruned_article)

    with open(out, "w") as f:
        f.write(pprint(pruned_articles))


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser(
        description="Extract fields from a database table to a TSV file."
    )

    subparsers = parser.add_subparsers(
        dest="db_type", required=True, help="Database backend to use"
    )

    pg_parser = subparsers.add_parser(
        "pg", help="Use PostgreSQL as the database backend"
    )
    pg_parser = add_input_articles_json_argument(pg_parser)
    pg_parser = add_postgresql_arguments(pg_parser)
    pg_parser = add_output_argument(pg_parser)

    args = parser.parse_args()

    connection_string = build_connection_string(args.user, args.host)

    setup_db(connection_string)

    find_k_nearest_neighbors(
        articles_json=args.articles_json,
        out=args.out,
        connection_string=connection_string,
    )
