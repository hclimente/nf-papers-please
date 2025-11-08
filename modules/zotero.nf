process ADVANCED_METADATA {

    container 'community.wave.seqera.io/library/pip_habanero_pgvector_sqlmodel:98d2da5778775e0e'
    secret 'USER_EMAIL'

    input:
    path ARTICLES_JSON

    output:
    path 'articles_with_extra_metadata.json'

    script:
    """
    crossref_annotate_doi.py \
--articles_json ${ARTICLES_JSON} \
--error_strategy include
    """

}

process REMOVE_PROCESSED {

    container 'community.wave.seqera.io/library/pip_pgvector_pyzotero_sqlmodel:e830732bfc803843'
    secret 'ZOTERO_API_KEY'

    input:
    path ARTICLES_JSON
    val ZOTERO_USER_ID
    val ZOTERO_COLLECTION_ID
    val ZOTERO_LIBRARY_TYPE

    output:
    path "unprocessed_articles.json", optional: true

    script:
    """
    zotero_remove_processed.py \
--articles_json ${ARTICLES_JSON} \
--zotero_user_id ${ZOTERO_USER_ID} \
--zotero_library_type ${ZOTERO_LIBRARY_TYPE} \
--zotero_collection_id ${ZOTERO_COLLECTION_ID}
    """

}


process SAVE {

    container 'community.wave.seqera.io/library/pip_pgvector_pyzotero_sqlmodel:e830732bfc803843'
    secret 'ZOTERO_API_KEY'

    input:
    path ARTICLES_JSON
    val ZOTERO_USER_ID
    val ZOTERO_COLLECTION_ID
    val ZOTERO_LIBRARY_TYPE

    script:
    """
    zotero_insert_article.py \
--articles_json ${ARTICLES_JSON} \
--zotero_user_id ${ZOTERO_USER_ID} \
--zotero_library_type ${ZOTERO_LIBRARY_TYPE} \
--zotero_collection_id ${ZOTERO_COLLECTION_ID}
    """

}
