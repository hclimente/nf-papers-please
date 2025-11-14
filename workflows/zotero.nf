include { ADVANCED_METADATA; FETCH_ARTICLES; REMOVE_PROCESSED; SAVE } from '../modules/zotero'

include { batchArticles; filterAndBatch } from '../modules/json'

workflow COLLECTION_CHECK {

    take:
        articles_json

    main:
        REMOVE_PROCESSED(
            batchArticles(articles_json, 1000),
            params.zotero_user_id,
            params.to_zotero_collection_id,
            params.to_zotero_library_type
        )

        filtered_articles = batchArticles(REMOVE_PROCESSED.out, params.batch_size)

    emit:
        filtered_articles

}

workflow FROM_ZOTERO {

    take:
        zotero_user_id
        from_zotero_collection_id
        from_zotero_library_type

    main:
        FETCH_ARTICLES(
            zotero_user_id,
            from_zotero_collection_id,
            from_zotero_library_type
        )

    emit:
        FETCH_ARTICLES.out

}

workflow TO_ZOTERO {

    take:
        articles_json

    main:
        ADVANCED_METADATA(articles_json)
        SAVE(
            ADVANCED_METADATA.out,
            params.zotero_user_id,
            params.to_zotero_collection_id,
            params.to_zotero_library_type
        )

    emit:
        true

}
