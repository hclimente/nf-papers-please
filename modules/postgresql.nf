process CREATE_ARTICLES_DB {

    container 'community.wave.seqera.io/library/pip_psycopg2-binary:6f4dafaf446c4354'
    secret 'PGPASSWORD'

    input:
    path JOURNALS_TSV
    val USER
    val HOST
    val GLOBAL_CUTOFF_DATE

    output:
    val true

    script:
    """
    db_create.py postgresql \
--journals_tsv ${JOURNALS_TSV} \
--user "${USER}" \
--host "${HOST}" \
--global_cutoff_date ${GLOBAL_CUTOFF_DATE}
    """

}

process FETCH_JOURNALS {

    container 'community.wave.seqera.io/library/pip_psycopg2-binary:6f4dafaf446c4354'
    secret 'PGPASSWORD'

    input:
    val USER
    val HOST

    output:
    path "journals.tsv"

    script:
    """
    db_extract_fields.py postgresql \
--user "${USER}" \
--host "${HOST}" \
--table sources \
--columns "name, feed_url, last_checked" \
--out journals.tsv
    """

}

process REMOVE_PROCESSED {

    container 'community.wave.seqera.io/library/pip_psycopg2-binary:6f4dafaf446c4354'
    secret 'PGPASSWORD'

    input:
    path ARTICLES_JSON
    val USER
    val HOST

    output:
    path "unprocessed_articles.json", optional: true

    script:
    """
    db_remove_processed.py postgresql \
--user "${USER}" \
--host "${HOST}" \
--articles_json ${ARTICLES_JSON} \
--out unprocessed_articles.json
    """

}


process SAVE {

    container 'community.wave.seqera.io/library/pip_psycopg2-binary:6f4dafaf446c4354'
    secret 'PGPASSWORD'

    input:
    path ARTICLES_JSON
    val USER
    val HOST

    output:
    val true

    script:
    """
    db_insert_article.py postgresql \
--user "${USER}" \
--host "${HOST}" \
--articles_json ${ARTICLES_JSON}
    """

}

process UPDATE_TIMESTAMPS {

    container 'community.wave.seqera.io/library/pip_psycopg2-binary:6f4dafaf446c4354'
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
    db_update_field.py postgresql \
--user "${USER}" \
--host "${HOST}" \
--table sources \
--set_clause "last_checked = '${today}'" \
--where_clause "1=1"
    """

}
}}
