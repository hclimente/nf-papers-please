include { FETCH_ARTICLES } from '../modules/rss'
include { FETCH_JOURNALS; REMOVE_PROCESSED; SAVE; UPDATE_TIMESTAMPS } from '../modules/duckdb'

include { batchArticles; filterAndBatch } from '../modules/json'

workflow REMOVE_ARTICLES_IN_DUCKDB {

    take:
        articles_json

    main:
        REMOVE_PROCESSED(
            batchArticles(articles_json, 1000),
            db
        )

        filtered_articles = batchArticles(REMOVE_PROCESSED.out, params.batch_size)

    emit:
        filtered_articles

}

workflow TO_DUCKDB {

    take:
        articles_json

    main:
        db = file(params.from_duckdb_input)

        SAVE(articles_json, db)
        UPDATE_TIMESTAMPS(SAVE.out.collect(), db)

    emit:
        true

}
