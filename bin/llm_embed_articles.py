#!/usr/bin/env python
import argparse
import logging
import pathlib

from common.llm import embed
from common.models import ArticleList, pprint
from common.parsers import (
    add_input_articles_json_argument,
    add_output_argument,
    add_debug_argument,
)
from common.utils import (
    get_env_variable,
)


def llm_process_articles(
    articles_json: str,
    model: str,
    task: str,
    out: str,
    debug: bool = False,
):
    """
    Process articles using LLM based on the provided stage and prompt.

    Args:
        articles_json (str): Path to the JSON file containing the articles to process.
        model (str): The model to use. One of 'gemini-1.5-flash', 'gemini-2.5-flash-lite', 'gemini-2.5-pro'.
        task (str): The task to perform.
        out (str): Path to the output file.
        debug (bool): Whether to enable debug mode.
    """
    logging.info("-" * 20)
    logging.info("llm_process_articles called with the following arguments:")
    logging.info(f"articles_json           : {articles_json}")
    logging.info(f"model                   : {model}")
    logging.info(f"task                    : {task}")
    logging.info(f"out                     : {out}")
    logging.info(f"debug                   : {debug}")
    logging.info("-" * 20)

    json_string = pathlib.Path(articles_json).read_text()
    articles = ArticleList.validate_json(json_string)
    logging.info(f"Loaded {len(articles)} articles.")
    logging.debug(f"Articles: {pprint(articles)}")

    texts = [article.to_embedding_text() for article in articles]

    embeddings = embed(
        texts=texts,
        model=model,
        api_key=get_env_variable("GOOGLE_API_KEY"),
        task=task,
    )

    for item, embedding in zip(articles, embeddings):
        setattr(item, "embedding", embedding.values)

    with open(out, "w") as f:
        f.write(pprint(articles))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process articles based on the provided prompt."
    )
    parser = add_input_articles_json_argument(parser)
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="The model to use. One of 'gemini-embedding-001'.",
    )
    parser.add_argument(
        "--task",
        type=str,
        required=True,
        help="The task to perform. One of 'SEMANTIC_SIMILARITY', 'CLASSIFICATION', "
        "'CLUSTERING', 'RETRIEVAL_DOCUMENT', 'RETRIEVAL_QUERY', 'CODE_RETRIEVAL_QUERY',"
        "'QUESTION_ANSWERING', 'FACT_VERIFICATION'",
    )
    parser = add_output_argument(parser)
    parser = add_debug_argument(parser)

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(message)s",
    )

    llm_process_articles(
        articles_json=args.articles_json,
        model=args.model,
        task=args.task,
        out=args.out,
        debug=args.debug,
    )
