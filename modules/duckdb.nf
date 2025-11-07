process CREATE_ARTICLES_DB {

    container 'community.wave.seqera.io/library/duckdb:1.4.1--3daff581f117ee85'
    publishDir "${DUCKDB_PARENT_DIR}", mode: 'link'

    input:
    path JOURNALS_TSV
    val DUCKDB_FILENAME
    val DUCKDB_PARENT_DIR
    val GLOBAL_CUTOFF_DATE

    output:
    path "${DUCKDB_FILENAME}"

    script:
    """
    duckdb_create.py \
--journals_tsv ${JOURNALS_TSV} \
--db_path ${DUCKDB_FILENAME} \
--global_cutoff_date ${GLOBAL_CUTOFF_DATE}
    """

}

process FETCH_JOURNALS {

    container 'community.wave.seqera.io/library/duckdb:1.4.1--3daff581f117ee85'

    input:
    path DUCKDB_PATH

    output:
    path "journals.tsv"

    script:
    """
    duckdb_extract_fields.py \
--db_path ${DUCKDB_PATH} \
--table sources \
--columns "name, feed_url, last_checked" \
--output_tsv journals.tsv
    """

}

process REMOVE_PROCESSED {

    container 'community.wave.seqera.io/library/duckdb:1.4.1--3daff581f117ee85'

    input:
    path ARTICLES_JSON
    path DUCKDB_PATH

    output:
    path "unprocessed_articles.json", optional: true

    script:
    """
    duckdb_remove_processed.py \
--db_path ${DUCKDB_PATH} \
--articles_json ${ARTICLES_JSON} \
--output_json unprocessed_articles.json
    """

}


process SAVE {

    container 'community.wave.seqera.io/library/duckdb:1.4.1--3daff581f117ee85'

    input:
    path ARTICLES_JSON
    path DUCKDB_PATH

    output:
    val true

    script:
    """
    duckdb_insert_article.py \
--db_path ${DUCKDB_PATH} \
--articles_json ${ARTICLES_JSON}
    """

}

process UPDATE_TIMESTAMPS {

    container 'community.wave.seqera.io/library/duckdb-cli:1.4.1--d924e68d63392ee0'

    input:
    val COMPLETION_SIGNALS
    path DUCKDB_PATH

    output:
    val true

    script:
    today = new Date().format("yyyy-MM-dd")
    """
    duckdb ${DUCKDB_PATH} "UPDATE sources SET last_checked = '${today}'"
    """

}
