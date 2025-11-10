include { BASIC_METADATA; TAG; SCORE; EMBED; CLASSIFY } from '../modules/agentic'
include { BASIC_METADATA as BASIC_METADATA_RETRY } from '../modules/agentic'
include { ADVANCED_METADATA; REMOVE_PROCESSED; SAVE } from '../modules/zotero'
include { TAG as TAG_RETRY } from '../modules/agentic'
include { CLASSIFY as CLASSIFY_RETRY } from '../modules/agentic'

include { FETCH_NEAREST_NEIGHBORS } from '../modules/postgresql'

include { batchArticles; filterAndBatch } from '../modules/json'

workflow EMBED_ARTICLES {

    take:
        articles_json

    main:
        BASIC_METADATA(
            batchArticles(articles_json, params.batch_size),
            file(params.metadata_extraction_system_prompt),
            params.metadata_extraction_model,
            true,
            params.debug
        )

        failed_metadata = batchArticles(BASIC_METADATA.out.fail, params.batch_size)
        BASIC_METADATA_RETRY(
            failed_metadata,
            file(params.metadata_extraction_system_prompt),
            params.metadata_extraction_model,
            false,
            params.debug
        )

        metadata_articles = BASIC_METADATA.out.pass
            .concat(BASIC_METADATA_RETRY.out.pass)
        articles_with_doi = filterAndBatch(metadata_articles, params.batch_size, "doi", null)

        ADVANCED_METADATA(articles_with_doi.no_match)

        TAG(
            ADVANCED_METADATA.out,
            file(params.tagging_system_prompt),
            file(params.research_interests),
            params.tagging_model,
            true,
            params.debug
        )

        TAG_RETRY(
            TAG.out.fail,
            file(params.tagging_system_prompt),
            file(params.research_interests),
            params.tagging_model,
            false,
            params.debug
        )

        tagged_articles = TAG.out.pass
            .concat(TAG_RETRY.out.pass)

        EMBED(
            tagged_articles,
            params.embedding_model,
            params.debug
        )

        all_articles = EMBED.out
            .concat(TAG_RETRY.out.fail)
        final_batches = batchArticles(all_articles, 100)

    emit:
        embedded_articles = EMBED.out
        all_articles = final_batches
}

workflow SCREEN_ARTICLES {

    take:
        articles_json

    main:

        FETCH_NEAREST_NEIGHBORS(
            batchArticles(articles_json, params.batch_size),
            params.to_pg_user,
            params.to_pg_host
        )

        CLASSIFY(
            FETCH_NEAREST_NEIGHBORS.out,
            file(params.classification_system_prompt),
            params.classification_model,
            true,
            params.debug
        )

        CLASSIFY_RETRY(
            CLASSIFY.out.fail,
            file(params.classification_system_prompt),
            params.classification_model,
            false,
            params.debug
        )

        prioritized_articles = CLASSIFY.out.pass
            .concat(CLASSIFY_RETRY.out.pass)

    emit:
        prioritized_articles

}
