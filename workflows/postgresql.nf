include { FETCH_ARTICLES } from '../modules/rss'
include { REMOVE_PROCESSED; SAVE; UPDATE_TIMESTAMPS } from '../modules/postgresql'

include { batchArticles; filterAndBatch } from '../modules/json'

workflow REMOVE_ARTICLES_IN_POSTGRESQL {

    take:
        articles_json

    main:
        REMOVE_PROCESSED(
            batchArticles(articles_json, 1000),
            params.to_pg_user,
            params.to_pg_host
        )

        filtered_articles = batchArticles(REMOVE_PROCESSED.out, params.batch_size)

    emit:
        filtered_articles

}

workflow TO_POSTGRESQL {

    take:
        articles_json

    main:
        SAVE(
            articles_json,
            params.to_pg_user,
            params.to_pg_host
        )

    emit:
        true

}
