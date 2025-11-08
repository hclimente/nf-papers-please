#!/usr/bin/env python
import argparse
import logging
import sys
from pathlib import Path

import yaml

from common.models import Article, ArticleList
from common.parsers import add_debug_argument, add_output_argument


def load_research_interests(config_path: Path) -> dict:
    """
    Load research interests from YAML configuration.

    Args:
        config_path: Path to research_interests.md or config.yaml file

    Returns:
        dict: Parsed research interests structure with categories and points
    """
    with open(config_path, "r") as f:
        content = f.read()

    # Parse YAML content (skip markdown headers if present)
    yaml_content = content
    if content.startswith("#"):
        # Extract YAML from markdown file
        lines = content.split("\n")
        yaml_lines = []
        in_yaml = False
        for line in lines:
            if line.strip() and not line.startswith("#"):
                in_yaml = True
            if in_yaml:
                yaml_lines.append(line)
        yaml_content = "\n".join(yaml_lines)

    return yaml.safe_load(yaml_content)


def build_category_index(research_interests: dict) -> dict[str, dict]:
    """
    Build an index of all categories with their metadata.

    For each category, stores:
    - points: the point value
    - aliases: list of alternative names
    - parent: name of parent category (None for top-level)
    - has_subcategories: whether this category has children

    Args:
        research_interests: Parsed research interests structure

    Returns:
        dict: Mapping from category name to category metadata
    """
    index = {}

    for dimension_key, dimension_items in research_interests.items():
        if not isinstance(dimension_items, list):
            continue

        for item in dimension_items:
            category = item.get("name")
            if not category:
                continue

            # Add parent category
            parent_info = {
                "points": item.get("points", 0),
                "aliases": item.get("aliases", []),
                "parent": None,
                "has_subcategories": "subcategories" in item,
            }
            index[category] = parent_info

            # Add aliases for parent
            for alias in parent_info["aliases"]:
                index[alias] = parent_info.copy()
                index[alias]["is_alias_of"] = category

            # Add subcategories
            if "subcategories" in item:
                for subitem in item["subcategories"]:
                    subcategory = subitem.get("name")
                    if not subcategory:
                        continue

                    sub_info = {
                        "points": subitem.get("points", 0),
                        "aliases": subitem.get("aliases", []),
                        "parent": category,
                        "has_subcategories": False,
                    }
                    index[subcategory] = sub_info

                    # Add aliases for subcategory
                    for alias in sub_info["aliases"]:
                        index[alias] = sub_info.copy()
                        index[alias]["is_alias_of"] = subcategory

    return index


def compute_article_score(article: Article, research_interests: dict) -> int:
    """
    Compute the score for an article based on its tags.

    Rules:
    - Add points for every matching tag at the same hierarchical level
    - Do NOT add points for parent categories if a subcategory matches
    - Example: If "Network Biology" is tagged, add 3 points
              Do NOT also add 1 point for "Computational Biology"

    Args:
        article: Article with tags to score
        research_interests: Parsed research interests structure

    Returns:
        int: Computed score for the article
    """
    if not article.tags:
        return 0

    # Build category index
    category_index = build_category_index(research_interests)

    # Identify which categories are actually tagged
    tagged_categories = set()
    for tag in article.tags:
        if tag in category_index:
            # Resolve alias to canonical name
            canonical_tag = category_index[tag].get("is_alias_of", tag)
            tagged_categories.add(canonical_tag)

    # Identify parent categories that should be excluded
    # A parent is excluded if ANY of its children are tagged
    excluded_parents = set()
    for tag in tagged_categories:
        if tag not in category_index:
            continue
        parent = category_index[tag].get("parent")
        if parent is not None:
            excluded_parents.add(parent)

    # Calculate score: add points for all tagged categories except excluded parents
    score = 0
    scored_categories = []

    for tag in tagged_categories:
        if tag not in category_index:
            continue

        # Skip if this is a parent that should be excluded
        if tag in excluded_parents:
            continue

        points = category_index[tag].get("points", 0)
        score += points
        scored_categories.append((tag, points))

    return score


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Compute article score based on tags and research interests"
    )
    parser.add_argument(
        "--research_interests_path",
        type=Path,
        required=True,
        help="Path to research_interests.md file",
    )
    parser.add_argument(
        "--articles_json",
        type=Path,
        required=True,
        help="Path to JSON file containing articles to score",
    )
    parser = add_output_argument(parser)
    parser = add_debug_argument(parser)
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed scoring breakdown to console",
    )

    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(message)s",
    )

    # Load research interests
    research_interests = load_research_interests(args.research_interests_path)

    # Parse articles
    json_string = args.articles_json.read_text()
    articles = ArticleList.validate_json(json_string)
    logging.info(f"Loaded {len(articles)} articles.")

    # Score all articles and update the article objects
    for article in articles:
        score = compute_article_score(article, research_interests)
        article.score = score

        # Optional verbose output to console
        if args.verbose:
            category_index = build_category_index(research_interests)
            tagged_categories = set()
            for tag in article.tags or []:
                if tag in category_index:
                    canonical_tag = category_index[tag].get("is_alias_of", tag)
                    tagged_categories.add(canonical_tag)

            # Identify excluded parents
            excluded_parents = set()
            for tag in tagged_categories:
                if tag not in category_index:
                    continue
                parent = category_index[tag].get("parent")
                if parent is not None:
                    excluded_parents.add(parent)

            logging.info(f"Article: {article.title}")
            logging.info(f"DOI: {article.doi}")
            logging.info(f"Tags: {', '.join(article.tags or [])}")
            logging.info("\nScore Breakdown:")
            for tag in sorted(tagged_categories):
                if tag not in category_index:
                    continue
                tag_info = category_index[tag]
                points = tag_info.get("points", 0)
                if tag in excluded_parents:
                    logging.info(
                        f"  {tag}: 0 points (excluded because child category is tagged)"
                    )
                else:
                    logging.info(f"  {tag}: +{points} points")
            logging.info(f"\nTotal Score: {score}")
            logging.info("-" * 60)

    # Write scored articles to output JSON file
    output_path = Path(args.out)
    with open(output_path, "w") as f:
        f.write(ArticleList.dump_json(articles, indent=2).decode())

    logging.info(f"✅ Wrote {len(articles)} scored articles to {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
