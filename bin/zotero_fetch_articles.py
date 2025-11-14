#!/usr/bin/env python
import argparse
import logging

from pyzotero import zotero

from common.models import (
    Article,
    pprint,
)
from common.parsers import (
    add_output_argument,
    add_debug_argument,
)
from common.utils import get_env_variable


def fetch_articles(
    zotero_user_id: str,
    zotero_library_type: str,
    zotero_collection_id: str,
    output: str,
) -> None:
    """
    Insert articles from a JSON file into Zotero.

    Args:
        zotero_user_id (str): Zotero user ID.
        zotero_library_type (str): Zotero library type ('user' or 'group').
        zotero_collection_id (str): Zotero collection ID to add articles to.
        output (str): Path to output file for articles.

    Returns:
        None
    """
    logging.info("-" * 20)
    logging.info(f"zotero_user_id       : {zotero_user_id}")
    logging.info(f"zotero_library_type  : {zotero_library_type}")
    logging.info(f"zotero_collection_id : {zotero_collection_id}")
    logging.info(f"output               : {output}")
    logging.info("-" * 20)

    zot = zotero.Zotero(
        zotero_user_id, zotero_library_type, get_env_variable("ZOTERO_API_KEY")
    )

    articles = zot.collection_items(zotero_collection_id)
    logging.info(f"Retrieved {len(articles)} items from Zotero collection.")

    # Filter for journal articles only
    journal_articles = [
        item
        for item in articles
        if item.get("data", {}).get("itemType") == "journalArticle"
    ]
    logging.info(f"Found {len(journal_articles)} journal articles.")

    articles = [Article.from_zotero_item(item) for item in journal_articles]

    if articles:
        with open(output, "w") as f:
            f.write(pprint(articles))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Insert articles from a TSV file into a DuckDB database."
    )

    parser = add_output_argument(parser)
    parser = add_debug_argument(parser)
    parser.add_argument(
        "--zotero_user_id",
        type=str,
        required=True,
        help="Zotero user ID.",
    )
    parser.add_argument(
        "--zotero_library_type",
        type=str,
        required=True,
        help="Zotero library type ('user' or 'group').",
    )
    parser.add_argument(
        "--zotero_collection_id",
        type=str,
        required=True,
        help="Zotero collection ID.",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(message)s",
    )

    fetch_articles(
        zotero_user_id=args.zotero_user_id,
        zotero_library_type=args.zotero_library_type,
        zotero_collection_id=args.zotero_collection_id,
        output=args.out,
    )
