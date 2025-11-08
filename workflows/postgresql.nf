include { FETCH_ARTICLES } from '../modules/rss'
include { CREATE_ARTICLES_DB; FETCH_JOURNALS; REMOVE_PROCESSED; SAVE; UPDATE_TIMESTAMPS } from '../modules/postgresql'

include { batchArticles; filterAndBatch } from '../modules/json'

workflow FROM_POSTGRESQL {

    take:
        journals_tsv

    main:
        if ( params.from_pg_create_tables ) {
            println "Creating PostgreSQL database tables."

            global_cutoff_date = new Date(System.currentTimeMillis() - params.days_back * 24 * 60 * 60 * 1000).format("yyyy-MM-dd")
            println "Global cutoff date set to ${params.days_back} days back (${global_cutoff_date})."

            CREATE_ARTICLES_DB(
                file(params.journals_tsv),
                params.from_pg_user,
                params.from_pg_host,
                global_cutoff_date
            )
        }

        FETCH_JOURNALS(
            params.from_pg_user,
            params.from_pg_host
        )

        journals = FETCH_JOURNALS.out
            .splitCsv(header: true, sep: '\t')

        FETCH_ARTICLES(journals, 50)

    emit:
        FETCH_ARTICLES.out

}

workflow REMOVE_ARTICLES_IN_POSTGRESQL {

    take:
        articles_json

    main:
        REMOVE_PROCESSED(
            batchArticles(articles_json, 1000),
            params.from_pg_user,
            params.from_pg_host
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

        UPDATE_TIMESTAMPS(
            SAVE.out.collect(),
            params.to_pg_user,
            params.to_pg_host
        )

    emit:
        true

}
