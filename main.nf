include { validateParameters } from 'plugin/nf-schema'

include { REMOVE_ARTICLES_IN_DUCKDB; TO_DUCKDB } from './workflows/duckdb'
include { FROM_JSON; TO_JSON } from './workflows/json'
include { REMOVE_ARTICLES_IN_POSTGRESQL; TO_POSTGRESQL } from './workflows/postgresql'
include { FROM_TABULAR } from './workflows/tabular'
include { COLLECTION_CHECK; FROM_ZOTERO; TO_ZOTERO } from './workflows/zotero'

include { EMBED_ARTICLES; SCREEN_ARTICLES } from './workflows/articles'

include { batchArticles; filterAndBatch } from './modules/json'

workflow LEARN {

    if (params.from == "articles_json") {
        FROM_JSON(file(params.from_json_input))
        fetched_articles = FROM_JSON.out
    } else if (params.from == "zotero") {
        FROM_ZOTERO(params.zotero_user_id, params.from_zotero_collection_id, params.from_zotero_library_type)
        fetched_articles = FROM_ZOTERO.out
    } else {
        error "Unsupported from: ${params.from}. Supported backends: 'articles_json', 'zotero'."
    }

    if (params.to == "duckdb") {
        REMOVE_ARTICLES_IN_DUCKDB(fetched_articles)
        articles_to_process = REMOVE_ARTICLES_IN_DUCKDB.out
    } else if (params.to == "pg") {
        REMOVE_ARTICLES_IN_POSTGRESQL(fetched_articles)
        articles_to_process = REMOVE_ARTICLES_IN_POSTGRESQL.out
    } else {
        articles_to_process = fetched_articles
    }

    EMBED_ARTICLES(articles_to_process)

    if (params.to == "duckdb") {
        TO_DUCKDB(EMBED_ARTICLES.out.all_articles)
    } else if (params.to == "pg") {
        TO_POSTGRESQL(EMBED_ARTICLES.out.all_articles)
    } else {
        error "Unsupported to: ${params.to}. Supported backends: 'duckdb', 'pg'."
    }

}

workflow SCREEN {

    if (params.from == "articles_json") {
        FROM_JSON(file(params.from_json_input))
        fetched_articles = FROM_JSON.out
    } else if (params.from == "journals_tsv") {
        FROM_TABULAR(file(params.journals_tsv))
        fetched_articles = FROM_TABULAR.out
    } else {
        error "Unsupported from: ${params.from}. Supported backends: 'articles_json', 'journals_tsv'."
    }

    if (params.to == "duckdb") {
        REMOVE_ARTICLES_IN_DUCKDB(fetched_articles)
        articles_to_process = REMOVE_ARTICLES_IN_DUCKDB.out
    } else if (params.to == "pg") {
        REMOVE_ARTICLES_IN_POSTGRESQL(fetched_articles)
        articles_to_process = REMOVE_ARTICLES_IN_POSTGRESQL.out
    } else {
        articles_to_process = fetched_articles
    }

    EMBED_ARTICLES(articles_to_process)
    SCREEN_ARTICLES(EMBED_ARTICLES.out.all_articles)

    if (params.to == "pg") {
        TO_POSTGRESQL(SCREEN_ARTICLES.out)
    }

}

workflow {

    validateParameters()

    if (params.mode == "learn") {
        LEARN()
    } else if (params.mode == "screen") {
        SCREEN()
    } else {
        error "Unsupported mode: ${params.mode}. Supported modes: 'learn', 'screen'."
    }

}
