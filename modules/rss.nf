process FETCH_ARTICLES {

    container 'community.wave.seqera.io/library/pip_feedparser_pgvector_python-dateutil_sqlmodel:393d59579a7a91cf'
    tag { JOURNAL_NAME }

    input:
    tuple val(JOURNAL_NAME), val(FEED_URL), val(LAST_CHECKED)
    val MAX_ITEMS

    output:
    path "articles.json", optional: true

    script:
    """
    fetch_articles.py \
--journal_name "${JOURNAL_NAME}" \
--feed_url "${FEED_URL}" \
--cutoff_date "${LAST_CHECKED}" \
--max_items ${MAX_ITEMS}
    """
}
