process BASIC_METADATA {

    container 'community.wave.seqera.io/library/pip_google-genai_pgvector_sqlmodel:852aa324a19aa1fc'
    label 'gemini_api'
    secret 'GOOGLE_API_KEY'
    secret 'SPRINGER_META_API_KEY'
    secret 'USER_EMAIL'

    input:
    path ARTICLES_JSON
    path SYSTEM_PROMPT
    val MODEL
    val ALLOW_QC_ERRORS
    val DEBUG

    output:
    path "metadata_pass.json", emit: pass, optional: true
    path "metadata_fail.json", emit: fail, optional: true

    script:
    """
    llm_process_articles.py \
--articles_json ${ARTICLES_JSON} \
${DEBUG ? '--debug' : ''} \
metadata \
--system_prompt_path ${SYSTEM_PROMPT} \
--model ${MODEL} \
--allow_qc_errors ${ALLOW_QC_ERRORS}
    """

}

process TAG {

    container 'community.wave.seqera.io/library/pip_google-genai_pgvector_sqlmodel:852aa324a19aa1fc'
    label 'gemini_api'
    secret 'GOOGLE_API_KEY'
    secret 'SPRINGER_META_API_KEY'
    secret 'USER_EMAIL'

    input:
    path ARTICLES_JSON
    path SYSTEM_PROMPT
    path RESEARCH_INTERESTS_PATH
    val MODEL
    val ALLOW_QC_ERRORS
    val DEBUG

    output:
    path "tagging_pass.json", emit: pass, optional: true
    path "tagging_fail.json", emit: fail, optional: true

    script:
    """
    llm_process_articles.py \
--articles_json ${ARTICLES_JSON} \
${DEBUG ? '--debug' : ''} \
tagging \
--system_prompt_path ${SYSTEM_PROMPT} \
--research_interests_path ${RESEARCH_INTERESTS_PATH} \
--model ${MODEL} \
--allow_qc_errors ${ALLOW_QC_ERRORS}
    """
}

process SCORE {

    container 'community.wave.seqera.io/library/pip_feedparser_pgvector_python-dateutil_sqlmodel:393d59579a7a91cf'

    input:
    path ARTICLES_JSON
    path RESEARCH_INTERESTS_PATH
    val DEBUG

    output:
    path "scored_articles.json"

    script:
    """
    compute_article_score.py \
--articles_json ${ARTICLES_JSON} \
--research_interests_path ${RESEARCH_INTERESTS_PATH} \
--out scored_articles.json \
${DEBUG ? '--debug' : ''}
    """
}

process CLASSIFY {

    container 'community.wave.seqera.io/library/pip_google-genai_pgvector_sqlmodel:852aa324a19aa1fc'
    label 'gemini_api'
    secret 'GOOGLE_API_KEY'
    secret 'SPRINGER_META_API_KEY'
    secret 'USER_EMAIL'

    input:
    path ARTICLES_JSON
    path SYSTEM_PROMPT
    val MODEL
    val ALLOW_QC_ERRORS
    val DEBUG

    output:
    path "classify_pass.json", emit: pass, optional: true
    path "classify_fail.json", emit: fail, optional: true

    script:
    """
    llm_process_articles.py \
--articles_json ${ARTICLES_JSON} \
${DEBUG ? '--debug' : ''} \
classify \
--system_prompt_path ${SYSTEM_PROMPT} \
--model ${MODEL} \
--allow_qc_errors ${ALLOW_QC_ERRORS}
    """
}

process EMBED {

    container 'community.wave.seqera.io/library/pip_google-genai_pgvector_sqlmodel:852aa324a19aa1fc'
    label 'gemini_api'
    secret 'GOOGLE_API_KEY'

    input:
    path ARTICLES_JSON
    val MODEL
    val DEBUG

    output:
    path "embeddings.json"

    script:
    """
    llm_embed_articles.py \
--articles_json ${ARTICLES_JSON} \
--model ${MODEL} \
--task SEMANTIC_SIMILARITY \
--out embeddings.json \
${DEBUG ? '--debug' : ''}
    """
}
