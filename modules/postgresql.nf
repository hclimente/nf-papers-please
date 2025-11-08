process FETCH_JOURNALS {

    container 'community.wave.seqera.io/library/pip_pgvector_psycopg2-binary_sqlmodel:af6f8a5438d58434'
    secret 'PGPASSWORD'

    input:
    val USER
    val HOST

    output:
    path "journals.tsv"

    script:
    """
    db_extract_fields.py pg \
--user "${USER}" \
--host "${HOST}" \
--table sources \
--columns "name, feed_url, last_checked" \
--out journals.tsv
    """

}

process REMOVE_PROCESSED {

    container 'community.wave.seqera.io/library/pip_pgvector_psycopg2-binary_sqlmodel:af6f8a5438d58434'
    secret 'PGPASSWORD'

    input:
    path ARTICLES_JSON
    val USER
    val HOST

    output:
    path "unprocessed_articles.json", optional: true

    script:
    """
    db_remove_processed.py pg \
--user "${USER}" \
--host "${HOST}" \
--articles_json ${ARTICLES_JSON} \
--out unprocessed_articles.json
    """

}


process SAVE {

    container 'community.wave.seqera.io/library/pip_pgvector_psycopg2-binary_sqlmodel:af6f8a5438d58434'
    secret 'PGPASSWORD'

    input:
    path ARTICLES_JSON
    val USER
    val HOST

    output:
    val true

    script:
    """
    db_insert_article.py pg \
--user "${USER}" \
--host "${HOST}" \
--articles_json ${ARTICLES_JSON}
    """

}

process UPDATE_TIMESTAMPS {

    container 'community.wave.seqera.io/library/pip_pgvector_psycopg2-binary_sqlmodel:af6f8a5438d58434'
    secret 'PGPASSWORD'

    input:
    val COMPLETION_SIGNALS
    val USER
    val HOST

    output:
    val true

    script:
    today = new Date().format("yyyy-MM-dd")
    """
    db_update_field.py pg \
--user "${USER}" \
--host "${HOST}" \
--table sources \
--set_clause "last_checked = '${today}'" \
--where_clause "1=1"
    """

}

process FETCH_NEAREST_NEIGHBORS {

    container 'community.wave.seqera.io/library/pip_pgvector_psycopg2-binary_sqlmodel:af6f8a5438d58434'
    secret 'PGPASSWORD'

    input:
    path ARTICLES_JSON
    val USER
    val HOST

    output:
    path "knn.json"

    script:
    """
    db_extract_fields.py pg \
--articles_json ${ARTICLES_JSON} \
--user "${USER}" \
--host "${HOST}" \
--table articles \
--columns doi \
--clause "ORDER BY embedding <-> '{embedding}' LIMIT 5" \
--out knn.json
    """

}
