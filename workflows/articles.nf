include { BASIC_METADATA; SCORE } from '../modules/agentic'
include { BASIC_METADATA as BASIC_METADATA_RETRY } from '../modules/agentic'
include { ADVANCED_METADATA; REMOVE_PROCESSED; SAVE } from '../modules/zotero'
include { SCORE as SCORE_RETRY } from '../modules/agentic'

include { batchArticles; filterAndBatch } from '../modules/json'

workflow PROCESS_ARTICLES {

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

        SCORE(
            ADVANCED_METADATA.out,
            file(params.scoring_system_prompt),
            file(params.research_interests),
            params.scoring_model,
            true,
            params.debug
        )

        SCORE_RETRY(
            SCORE.out.fail,
            file(params.scoring_system_prompt),
            file(params.research_interests),
            params.scoring_model,
            false,
            params.debug
        )

        scored_articles = SCORE.out.pass
            .concat(SCORE_RETRY.out.pass)
        all_articles = scored_articles
            .concat(SCORE_RETRY.out.fail)
        final_batches = batchArticles(all_articles, 100)

    emit:
        scored_articles = scored_articles
        all_articles = final_batches
}
