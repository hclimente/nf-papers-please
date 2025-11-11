#!/usr/bin/env python
import argparse
import logging
import pathlib

from common.llm import chat
from common.models import ArticleList
from common.parsers import (
    add_input_articles_json_argument,
    add_debug_argument,
    add_llm_arguments,
)
from common.utils import get_env_variable, prune_article_for_classification
from common.validation import (
    save_validated_responses,
    validate_llm_response,
)
from tools.metadata_tools import (
    get_abstract_from_doi,
    springer_get_abstract_from_doi,
    get_doi_for_arxiv_url,
)


def llm_process_articles(
    stage: str,
    articles_json: str,
    system_prompt_path: str,
    research_interests_path: str,
    model: str,
    allow_qc_errors: bool,
    debug: bool = False,
):
    """
    Process articles using LLM based on the provided stage and prompt.

    Args:
        stage (str): The processing stage (e.g., "metadata", "tagging").
        articles_json (str): Path to the JSON file containing the articles to process.
        system_prompt_path (str): The path to the system prompt file.
        research_interests_path (str): The path to a text file containing the user's research interests.
        model (str): The model to use. One of 'gemini-1.5-flash', 'gemini-2.5-flash-lite', 'gemini-2.5-pro'.
        allow_qc_errors (bool): Whether to allow QC errors without failing the process.
        debug (bool): Whether to enable debug mode.
    """
    logging.info("-" * 20)
    logging.info("llm_process_articles called with the following arguments:")
    logging.info(f"stage                   : {stage}")
    logging.info(f"articles_json           : {articles_json}")
    logging.info(f"system_prompt_path      : {system_prompt_path}")
    logging.info(f"research_interests_path : {research_interests_path}")
    logging.info(f"model                   : {model}")
    logging.info(f"allow_qc_errors         : {allow_qc_errors}")
    logging.info(f"debug                   : {debug}")
    logging.info("-" * 20)

    json_string = pathlib.Path(articles_json).read_text()
    articles = ArticleList.validate_json(json_string)
    logging.info(f"Loaded {len(articles)} articles.")
    # logging.debug(f"Articles: {pprint(articles)}")

    # For classify stage, prune articles to only include relevant fields
    if stage == "classify":
        articles_for_llm = [
            prune_article_for_classification(article) for article in articles
        ]
        logging.info("Pruned articles for classification stage.")
    else:
        articles_for_llm = articles

    response_text = chat(
        articles=articles_for_llm,
        system_prompt_path=system_prompt_path,
        model=model,
        api_key=get_env_variable("GOOGLE_API_KEY"),
        research_interests_path=research_interests_path,
        tools=[
            get_abstract_from_doi,
            springer_get_abstract_from_doi,
            get_doi_for_arxiv_url,
        ],
    )

    # for debugging purposes, save the raw LLM response to a file
    pathlib.Path("llm_response_text.txt").write_text(response_text)

    merge_key = "url" if stage == "metadata" else "doi"
    response_pass = validate_llm_response(
        stage=stage,
        response_text=response_text,
        merge_key=merge_key,
        allow_qc_errors=allow_qc_errors,
    )

    save_validated_responses(
        articles=articles,
        response_pass=response_pass,
        allow_qc_errors=allow_qc_errors,
        stage=stage,
        merge_key=merge_key,
    )

    logging.info(f"✅ Done {stage} articles.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process articles based on the provided prompt."
    )
    parser = add_input_articles_json_argument(parser)
    parser = add_debug_argument(parser)
    subparsers = parser.add_subparsers(dest="command", required=True)

    metadata_parser = subparsers.add_parser("metadata")
    metadata_parser = add_llm_arguments(
        metadata_parser, include_research_interests=False
    )
    tagging_parser = subparsers.add_parser("tagging")
    tagging_parser = add_llm_arguments(tagging_parser, include_research_interests=True)
    classify_parser = subparsers.add_parser("classify")
    classify_parser = add_llm_arguments(
        classify_parser, include_research_interests=False
    )

    args = parser.parse_args()
    try:
        research_interests_path = args.research_interests_path
    except AttributeError:
        research_interests_path = None

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(message)s",
    )

    llm_process_articles(
        args.command,
        args.articles_json,
        args.system_prompt_path,
        research_interests_path,
        args.model,
        args.allow_qc_errors,
        args.debug,
    )
