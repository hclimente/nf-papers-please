# AGENTS.md - Code Assistant Guide

**Last Updated:** November 1, 2025
**Project:** Papers, Please - Agentic Literature Screening Workflow

---

## 📋 Project Overview

**Papers, Please** is an automated literature screening system that helps researchers stay current with scientific publications. It uses AI (Google Gemini) to extract metadata, screen articles for relevance, and prioritize them based on research interests.

### Key Characteristics
- **Language Stack**: Nextflow (workflow orchestration) + Python (data processing/LLM interaction)
- **Architecture**: Modular, containerized pipeline with separate concerns
- **Execution**: Can run locally, on HPC clusters, or via GitHub Actions (weekly automation)
- **Data Flow**: RSS feeds → Metadata extraction → Screening → Prioritization → Output (JSON/Zotero/DuckDB)

---

## 🏗️ Architecture

### High-Level Flow
```
Input Sources          Processing Pipeline           Output Destinations
┌─────────────┐       ┌──────────────────┐         ┌─────────────┐
│ RSS Feeds   │──────>│ Metadata Extract │────────>│ JSON File   │
│ JSON File   │       │ Screen Articles  │         │ Zotero API  │
│ DuckDB      │       │ Prioritize       │         │ DuckDB      │
└─────────────┘       └──────────────────┘         └─────────────┘
```

### Directory Structure

```
papers_please/
├── main.nf                    # Main workflow entry point
├── nextflow.config            # Default parameters & configuration
├── nextflow_schema.json       # Parameter validation schema
│
├── config/                    # User configuration
│   ├── config.yaml           # Main config (journals, interests, Zotero)
│   ├── journals.tsv          # Journal list with RSS URLs
│   └── research_interests.md # User's research interests (input to LLM)
│
├── workflows/                 # High-level workflow definitions
│   ├── articles.nf           # Main article processing pipeline
│   ├── duckdb.nf             # DuckDB input/output workflows
│   ├── json.nf               # JSON input/output workflows
│   ├── tabular.nf            # TSV/CSV input workflows
│   └── zotero.nf             # Zotero integration workflows
│
├── modules/                   # Nextflow process definitions
│   ├── agentic.nf            # LLM processes (metadata, screening, prioritization)
│   ├── db.nf                 # Database operations
│   ├── json.nf               # JSON manipulation utilities
│   ├── rss.nf                # RSS feed fetching
│   └── zotero.nf             # Zotero API operations
│
├── bin/                       # Python scripts (automatically in PATH)
│   ├── pyproject.toml        # Python dependencies (uv/pip)
│   ├── common/               # Shared Python modules
│   │   ├── models.py         # Pydantic data models
│   │   ├── llm.py            # LLM interaction logic
│   │   ├── validation.py     # Response validation
│   │   ├── parsers.py        # CLI argument parsers
│   │   └── utils.py          # Utility functions
│   ├── tests/                # Python unit tests (pytest)
│   ├── tools/                # Helper tools for metadata enrichment
│   ├── fetch_articles.py     # RSS feed fetching
│   ├── llm_process_articles.py  # LLM processing orchestrator
│   ├── json_validate_articles.py # JSON schema validation
│   ├── duckdb_*.py          # DuckDB operations
│   └── zotero_*.py          # Zotero operations
│
├── prompts/                   # LLM system prompts
│   ├── metadata_extraction.md  # Extract title, abstract, DOI
│   ├── screening.md          # Binary relevance filtering
│   └── prioritization.md     # Rank by research interest alignment
│
├── assets/                    # Validation schemas
└── results/                   # Default output directory
```

---

## 🔑 Core Concepts

### 1. **Three-Stage LLM Pipeline**

Each article goes through three AI-powered stages:

1. **Metadata Extraction** (`EXTRACT_METADATA`)
   - Input: Raw RSS feed content (URL + text snippet)
   - Output: Structured article (title, abstract, DOI, URL)
   - Tools: Can use CrossRef/Springer APIs to find missing DOIs
   - Validation: Pydantic `MetadataResponse` model

2. **Screening** (`SCREEN`)
   - Input: Articles with metadata + research interests
   - Output: Boolean decision (relevant/not relevant) + reasoning
   - Goal: High recall (80-90%) - filter out clear mismatches
   - Validation: Pydantic `ScreeningResponse` model

3. **Prioritization** (`PRIORITIZE`)
   - Input: Screened (relevant) articles + research interests
   - Output: Priority level (high/medium/low) + reasoning
   - Goal: Rank articles by alignment with interests
   - Validation: Pydantic `PriorityResponse` model

**Retry Logic**: Each stage has a `_RETRY` process that re-processes failed articles with `allow_qc_errors=false`.

### 2. **Data Models**

Core Pydantic models in `bin/common/models.py`:

- **`Article`**: Full article with all metadata and processing results
  - Fields: title, authors, summary, doi, url, journal info, dates
  - LLM fields: screening_decision, screening_reasoning, priority_decision, priority_reasoning

- **`ArticleList`**: Type adapter for `list[Article]`

- **`MetadataResponse`**: LLM output for metadata extraction
- **`ScreeningResponse`**: LLM output for screening
- **`PriorityResponse`**: LLM output for prioritization

### 3. **Nextflow Workflow System**

**Key Concepts:**
- **Processes** (in `modules/`): Individual tasks (containerized)
- **Workflows** (in `workflows/`): Composition of processes
- **Channels**: Data streams between processes (immutable)
- **Operators**: Transform channels (e.g., `concat`, `splitCsv`)

**Main Entry Point**: `main.nf`
- Validates parameters
- Routes based on `--from` (input) and `--to` (output) backends
- Calls `PROCESS_ARTICLES` workflow
- Handles output routing

### 4. **Backend Flexibility**

**Input Backends** (`--from`):
- `journals_tsv`: Fetch from RSS feeds defined in TSV file
- `articles_json`: Read pre-fetched articles from JSON
- `duckdb`: Load articles from DuckDB database

**Output Backends** (`--to`):
- `articles_json`: Write to JSON file
- `zotero`: Upload to Zotero library via API
- `duckdb`: Store in DuckDB database

### 5. **Containerization**

All Python processes run in Wave containers:
- Base: `community.wave.seqera.io/library/pip_google-genai:*`
- Scripts in `bin/` are automatically available in container PATH
- Secrets (API keys) injected via Nextflow secrets system

---

## 🛠️ Development Workflows

### Adding a New LLM Stage

1. **Create prompt** in `prompts/new_stage.md`
2. **Define response model** in `bin/common/models.py`:
   ```python
   class NewStageResponse(BaseModel):
       doi: str
       new_field: str
   ```
3. **Add process** in `modules/agentic.nf`:
   ```nextflow
   process NEW_STAGE {
       container 'community.wave.seqera.io/library/pip_google-genai:2e5c0f1812c5cbda'
       label 'gemini_api'
       secret 'GOOGLE_API_KEY'

       input:
       path ARTICLES_JSON
       path SYSTEM_PROMPT
       val MODEL
       val ALLOW_QC_ERRORS
       val DEBUG

       output:
       path "new_stage_pass.json", emit: pass, optional: true
       path "new_stage_fail.json", emit: fail, optional: true

       script:
       """
       llm_process_articles.py \
       --articles_json ${ARTICLES_JSON} \
       ${DEBUG ? '--debug' : ''} \
       new_stage \
       --system_prompt_path ${SYSTEM_PROMPT} \
       --model ${MODEL} \
       --allow_qc_errors ${ALLOW_QC_ERRORS}
       """
   }
   ```
4. **Add logic** to `bin/llm_process_articles.py`
5. **Integrate** into `workflows/articles.nf`

### Adding a New Backend

1. **Create workflow** in `workflows/new_backend.nf`:
   ```nextflow
   workflow FROM_NEW_BACKEND { ... }
   workflow TO_NEW_BACKEND { ... }
   ```
2. **Create processes** in `modules/new_backend.nf`
3. **Add Python scripts** in `bin/` (e.g., `new_backend_fetch.py`)
4. **Register** in `main.nf`:
   ```nextflow
   if (params.from == "new_backend") {
       FROM_NEW_BACKEND(...)
   }
   ```
5. **Add parameters** to `nextflow.config` and `nextflow_schema.json`

### Testing Changes

**Python Unit Tests:**
```bash
cd bin
uv run pytest tests/
```

**Run Test Workflow:**
```bash
nextflow run main.nf \
    --from articles_json \
    --from_json_input test_articles.json \
    --to articles_json \
    --debug
```

**Check Specific Process:**
```bash
nextflow run main.nf -entry EXTRACT_METADATA --debug
```

---

## 🔍 Common Code Patterns

### Nextflow: Batching Articles

```nextflow
// Batch articles into groups of 10
batched = batchArticles(articles_channel, 10)

// Filter by field and batch
filtered = filterAndBatch(articles_channel, 10, "screening_decision", true)
// Returns: filtered.match, filtered.no_match
```

### Python: LLM Query

```python
from common.llm import llm_query
from common.validation import validate_llm_response, save_validated_responses

response = llm_query(
    system_prompt=system_prompt,
    user_prompt=user_prompt,
    model=model
)

validated = validate_llm_response(
    response,
    ResponseModel,
    allow_qc_errors=allow_qc_errors
)

save_validated_responses(validated, articles, "pass.json", "fail.json")
```

### Python: Article Manipulation

```python
from common.models import Article, ArticleList

# Load articles
with open("articles.json") as f:
    articles = ArticleList.validate_json(f.read())

# Update article
for article in articles:
    article.screening_decision = True
    article.screening_reasoning = "Relevant"

# Save articles
with open("output.json", "w") as f:
    f.write(ArticleList.dump_json(articles, indent=2).decode())
```

---

## ⚙️ Configuration

### Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `from` | `journals_tsv` | Input backend |
| `to` | `articles_json` | Output backend |
| `days_back` | `8` | Days to look back for articles |
| `batch_size` | `10` | Articles per batch for LLM |
| `metadata_extraction_model` | `gemini-2.5-flash-lite` | LLM for metadata |
| `screening_model` | `gemini-2.5-flash-lite` | LLM for screening |
| `prioritization_model` | `gemini-2.5-flash-lite` | LLM for prioritization |
| `debug` | `false` | Enable debug logging |

### Secrets Required

- `GOOGLE_API_KEY`: Google AI Studio API key (required)
- `USER_EMAIL`: Email for CrossRef/NCBI APIs (required)
- `SPRINGER_META_API_KEY`: Springer API key (optional)
- `ZOTERO_API_KEY`: Zotero API key (optional, for `--to zotero`)

Set secrets:
```bash
nextflow secrets set GOOGLE_API_KEY "your-key"
```

---

## 🐛 Debugging Tips

### 1. Enable Debug Mode
```bash
nextflow run main.nf --debug
```
This adds verbose logging to Python scripts.

### 2. Check Work Directory
```bash
ls -la work/*/
```
Each task's work directory contains:
- `.command.sh`: Executed script
- `.command.out`: stdout
- `.command.err`: stderr
- Input/output files

### 3. Resume Failed Runs
```bash
nextflow run main.nf -resume
```
Nextflow caches successful tasks.

### 4. Inspect LLM Responses
Failed LLM responses are saved to `*_fail.json` files with validation errors.

### 5. Test Python Scripts Directly
```bash
cd bin
uv run python llm_process_articles.py \
    --articles_json ../test_articles.json \
    metadata \
    --system_prompt_path ../prompts/metadata_extraction.md \
    --model gemini-2.5-flash-lite
```

---

## 📝 Code Style & Conventions

### Nextflow
- **Naming**: UPPERCASE for processes, PascalCase for workflows
- **Channels**: lowercase with underscores (`articles_json`)
- **Labels**: Use for resource allocation (`label 'gemini_api'`)

### Python
- **Style**: Follow PEP 8
- **Type Hints**: Required for all functions
- **Models**: Use Pydantic for data validation
- **Logging**: Use `logging` module (not `print`)
- **Error Handling**: Raise specific exceptions, don't catch generic `Exception`

### File Organization
- One process/workflow per logical unit
- Group related processes in same `.nf` file
- Keep Python scripts focused (single responsibility)
- Put shared utilities in `bin/common/`

---

## 🚀 Performance Considerations

- **Batching**: LLM processes batch articles (default: 10) to reduce API calls
- **Retry Logic**: Failed articles are retried once with relaxed validation
- **Parallel Execution**: Nextflow runs independent tasks in parallel
- **Caching**: Use `-resume` to skip completed tasks
- **Rate Limiting**: Gemini API has rate limits; batch size and concurrency are tuned

---

## 📚 Additional Resources

- **Nextflow Docs**: https://www.nextflow.io/docs/latest/
- **Pydantic Docs**: https://docs.pydantic.dev/
- **Google Gemini API**: https://ai.google.dev/
- **Zotero API**: https://www.zotero.org/support/dev/web_api/v3/start

---

## ⚠️ Important Notes

1. **This is NOT for workflow agents**: This file is for code assistants (like GitHub Copilot) helping with development, not for the LLM agents that process articles.

2. **Branch**: Currently on `feat/add_tests` - working branch for adding test coverage.

3. **Database**: DuckDB files (`.duckdb`) store processed articles to avoid re-processing.

4. **GitHub Actions**: `.github/workflows/` contains automation for weekly runs.

5. **Secrets Management**: Never commit API keys. Use Nextflow secrets or GitHub secrets.

6. **Containerization**: All processes are containerized. Test locally with Docker before deploying.

---

## 🤝 Making Changes

### Before Editing
1. Read relevant sections of this guide
2. Check existing tests in `bin/tests/`
3. Review similar implementations in codebase
4. Understand data flow through pipeline

### After Editing
1. Run Python tests: `cd bin && uv run pytest`
2. Test workflow: `nextflow run main.nf -resume`
3. Check for errors in work directories
4. Update documentation if adding new features
5. Commit with descriptive message

### Common Pitfalls
- Forgetting to add new Python scripts to `bin/` (must be in PATH)
- Not handling optional outputs in Nextflow processes
- Mixing up channel operators (concat vs mix vs join)
- Not validating LLM responses with Pydantic
- Hardcoding paths instead of using parameters
- Not testing with `--debug` flag first

---

**Happy Coding! 🎉**
