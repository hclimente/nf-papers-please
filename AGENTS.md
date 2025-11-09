# AGENTS.md - Code Assistant Guide

**Last Updated:** November 9, 2025
**Project:** Papers, Please - Agentic Literature Screening Workflow
**Current Branch:** feat/modelsql

---

## 📋 Project Overview

**Papers, Please** is an automated literature screening system that helps researchers stay current with scientific publications. It uses AI (Google Gemini) to extract metadata and tag articles based on research interests.

### Key Characteristics
- **Language Stack**: Nextflow (workflow orchestration) + Python (data processing/LLM interaction)
- **Architecture**: Modular, containerized pipeline with separate concerns
- **Execution**: Can run locally, on HPC clusters, or via GitHub Actions (weekly automation)
- **Modes**: Two operational modes - "learn" (from Zotero library) and "screen" (prioritize new articles)
- **Data Flow**: RSS feeds → Basic metadata → Advanced metadata → Tagging → Embedding → Output (JSON/PostgreSQL/DuckDB)

---

## 🏗️ Architecture

### High-Level Flow
```
Input Sources              Processing Pipeline                  Output Destinations
┌─────────────┐           ┌──────────────────┐                ┌─────────────┐
│ RSS Feeds   │──────────>│ Basic Metadata   │───────────────>│ JSON File   │
│ JSON File   │           │ Advanced Metadata│                │ PostgreSQL  │
│ DuckDB      │           │ Tag Articles     │                │ DuckDB      │
│ PostgreSQL  │           │ Embed Articles   │                │             │
└─────────────┘           └──────────────────┘                └─────────────┘
                                    │
                          (Screen mode: k-NN search)
```

### Directory Structure

```
papers_please/
├── main.nf                    # Main workflow entry point
├── nextflow.config            # Default parameters & configuration
├── nextflow_schema.json       # Parameter validation schema
│
├── config/                    # User configuration
│   ├── config.yaml           # Main config (can override nextflow.config)
│   ├── journals.tsv          # Journal list with RSS URLs
│   └── research_interests.md # User's research interests (hierarchical YAML structure)
│
├── workflows/                 # High-level workflow definitions
│   ├── articles.nf           # Main article processing pipeline
│   ├── duckdb.nf             # DuckDB input/output workflows
│   ├── json.nf               # JSON input/output workflows
│   ├── postgresql.nf         # PostgreSQL input/output workflows
│   ├── tabular.nf            # TSV/CSV input workflows (RSS feeds)
│   └── zotero.nf             # Zotero integration workflows
│
├── modules/                   # Nextflow process definitions
│   ├── agentic.nf            # LLM processes (metadata extraction, tagging, embedding)
│   ├── duckdb.nf             # DuckDB operations
│   ├── json.nf               # JSON manipulation utilities
│   ├── postgresql.nf         # PostgreSQL operations
│   ├── rss.nf                # RSS feed fetching
│   └── zotero.nf             # Zotero API operations
│
├── bin/                       # Python scripts (automatically in PATH)
│   ├── pyproject.toml        # Python dependencies (uv/pip)
│   ├── common/               # Shared Python modules
│   │   ├── models.py         # Pydantic/SQLModel data models
│   │   ├── llm.py            # LLM interaction logic
│   │   ├── validation.py     # Response validation
│   │   ├── parsers.py        # CLI argument parsers
│   │   ├── db.py             # Database connection utilities
│   │   └── utils.py          # Utility functions
│   ├── tests/                # Python unit tests (pytest)
│   ├── tools/                # Helper tools for metadata enrichment
│   ├── fetch_articles.py     # RSS feed fetching
│   ├── llm_process_articles.py  # LLM processing orchestrator
│   ├── llm_embed_articles.py    # Generate embeddings for articles
│   ├── compute_article_score.py # Score articles based on tags
│   ├── json_validate_articles.py # JSON schema validation
│   ├── crossref_annotate_doi.py # Annotate articles with CrossRef metadata
│   ├── db_*.py               # Database operations (insert, update, remove, find_nearest_neighbors)
│   └── zotero_*.py          # Zotero operations
│
├── prompts/                   # LLM system prompts
│   ├── metadata_extraction.md  # Extract title, abstract, DOI
│   └── tagging.md            # Tag articles based on research interests
│
├── assets/                    # Validation schemas
└── results/                   # Default output directory
```

---

## 🔑 Core Concepts

### 1. **Two Operational Modes**

**Learn Mode** (`--mode learn`):
- Input: Articles from your Zotero library or JSON file
- Goal: Learn from articles you've already curated
- Processing: Extract metadata → Tag articles → Generate embeddings
- Output: Store in database (PostgreSQL/DuckDB) for future reference
- Use case: Build a knowledge base from your existing library

**Screen Mode** (`--mode screen`):
- Input: New articles from RSS feeds or other sources
- Goal: Prioritize new articles based on learned interests
- Processing: Extract metadata → Tag articles → Generate embeddings → Find k-nearest neighbors from database
- Output: Articles with their nearest neighbors from the learned library
- Use case: Weekly screening of new publications
- Note: Requires PostgreSQL backend with existing embedded articles

### 2. **Four-Stage Processing Pipeline**

Each article goes through up to four processing stages:

1. **Basic Metadata Extraction** (`BASIC_METADATA`)
   - Input: Raw RSS feed content (URL + text snippet)
   - Output: Structured article (title, abstract, DOI, URL)
   - Tools: Can use CrossRef/Springer APIs to find missing DOIs/abstracts
   - Validation: Pydantic `MetadataResponse` model
   - LLM Function: `chat()` in `common/llm.py`
   - Process: `BASIC_METADATA` in `modules/agentic.nf`

2. **Advanced Metadata** (`ADVANCED_METADATA`)
   - Input: Articles with DOI
   - Output: Enhanced metadata (authors, journal info, dates, etc.)
   - Source: CrossRef API or Zotero API
   - Goal: Enrich articles with complete bibliographic information
   - Process: `ADVANCED_METADATA` in `modules/zotero.nf`

3. **Tagging** (`TAG`)
   - Input: Articles with metadata + research interests (YAML structure)
   - Output: List of categorical tags + reasoning for each article
   - Goal: Categorize articles based on research interest dimensions
   - Validation: Pydantic `TaggingResponse` model
   - LLM Function: `chat()` in `common/llm.py`
   - Process: `TAG` in `modules/agentic.nf`

4. **Embedding** (`EMBED`)
   - Input: Tagged articles
   - Output: Vector embeddings for semantic search
   - Model: Google gemini-embedding-001 (3072 dimensions)
   - Function: `embed()` in `common/llm.py`
   - Storage: PostgreSQL (pgvector) or DuckDB
   - Process: `EMBED` in `modules/agentic.nf`

**Scoring** (`SCORE` - currently defined but not used in workflows):
- Input: Tagged articles + research interests YAML
- Output: Numeric score based on tag weights
- Goal: Rank articles by alignment with research priorities
- Logic: Hierarchical scoring based on category tree structure
- Script: `compute_article_score.py`
- Note: The process exists in `modules/agentic.nf` but is not currently integrated into the main workflows

**Retry Logic**: Each LLM stage has a `_RETRY` process that re-processes failed articles with `allow_qc_errors=false`.

### 3. **Data Models**

Core Pydantic/SQLModel models in `bin/common/models.py`:

**Database Models (SQLModel - for PostgreSQL/DuckDB):**

- **`ArticleTable`**: Full article with all metadata and processing results
  - Core fields: title, summary, doi, url
  - Publication info: volume, issue, date, language
  - Processing fields: reasoning, score, zotero_key
  - Relationships: journal (via `ArticleJournalLink`), authors (via `ArticleAuthorLink`), tags (via `ArticleTagLink`)
  - Vector field: embedding (pgvector, 3072 dimensions)
  - Raw data: raw_contents, access_date

- **`AuthorTable`**: Individual or institutional author
  - Fields: first_name (optional), last_name
  - Relationship: articles (many-to-many)

- **`Tag`**: Tag for categorizing articles
  - Fields: name (unique)
  - Relationship: articles (many-to-many)

- **`JournalTable`**: Journal information
  - Fields: name (unique), short_name
  - Relationship: articles (many-to-many)

**Link Tables (for many-to-many relationships):**
- **`ArticleAuthorLink`**: Links articles to authors
- **`ArticleTagLink`**: Links articles to tags
- **`ArticleJournalLink`**: Links articles to journals

**In-Memory Models (Pydantic - for JSON serialization):**

- **`Article`**: JSON-serializable version of ArticleTable
  - All fields from `ArticleBase`
  - Lists instead of relationships: authors (list of Author), tags (list of str)
  - Fields: journal_name, journal_short_name, embedding (list of float)

- **`Author`**: Individual or institutional author (used in Article)
  - Fields: first_name (optional), last_name
  - Property: is_institutional (checks if first_name is None)

- **`ArticleList`**: Type adapter for `list[Article]` (for JSON validation)

**LLM Response Models:**

- **`MetadataResponse`**: LLM output for metadata extraction
  - Fields: title, summary, url, doi
  - Validators: doi format (10.xxxx/...), url format

- **`TaggingResponse`**: LLM output for tagging
  - Fields: doi, tags (list of str), reasoning

### 4. **Nextflow Workflow System**

**Key Concepts:**
- **Processes** (in `modules/`): Individual tasks (containerized)
- **Workflows** (in `workflows/`): Composition of processes
- **Channels**: Data streams between processes (immutable)
- **Operators**: Transform channels (e.g., `concat`, `splitCsv`)

**Main Entry Point**: `main.nf`
- Validates parameters
- Routes based on `--mode` (learn/screen)
- Calls `LEARN` or `SCREEN` workflows
- Both workflows call `EMBED_ARTICLES` for processing

**LEARN Workflow**:
```nextflow
Input (from JSON/Zotero) → Remove duplicates (if outputting to DB) → EMBED_ARTICLES → Save to DB
```

**SCREEN Workflow**:
```nextflow
Input (from RSS/JSON) → Remove duplicates (if outputting to DB) → EMBED_ARTICLES → SCREEN_ARTICLES (k-NN via PostgreSQL) → Output
```
Note: The SCREEN workflow currently uses `FETCH_NEAREST_NEIGHBORS` to query the PostgreSQL database for similar articles. The full screening pipeline with retry logic is partially implemented.

**EMBED_ARTICLES Workflow** (in `workflows/articles.nf`):
```nextflow
BASIC_METADATA → BASIC_METADATA_RETRY
     ↓
ADVANCED_METADATA (for articles without DOI)
     ↓
TAG → TAG_RETRY
     ↓
EMBED → Batch and emit
```

### 5. **Backend Flexibility**

**Input Backends** (`--from`):
- `journals_tsv`: Fetch from RSS feeds defined in TSV file (screen mode)
- `articles_json`: Read pre-fetched articles from JSON
- `duckdb`: Load articles from DuckDB database (not yet implemented)
- `pg` (PostgreSQL): Load from PostgreSQL database (learn mode)
- `zotero`: Fetch from Zotero library (learn mode)

**Output Backends** (`--to`):
- `articles_json`: Write to JSON file
- `zotero`: Upload to Zotero library via API (not yet implemented in current version)
- `duckdb`: Store in DuckDB database
- `pg` (PostgreSQL): Store in PostgreSQL database (with pgvector)

### 6. **Containerization**

All Python processes run in Wave containers:
- **LLM processes**: `community.wave.seqera.io/library/pip_google-genai_pgvector_sqlmodel:*`
- **Database processes**: `community.wave.seqera.io/library/pip_pgvector_psycopg2-binary_sqlmodel:*`
- **Scoring**: `community.wave.seqera.io/library/pip_pyyaml_pydantic:*`
- Scripts in `bin/` are automatically available in container PATH
- Secrets (API keys) injected via Nextflow secrets system

### 7. **Database Schema**

**PostgreSQL/DuckDB** uses the SQLModel-defined schema with:
- **pgvector extension**: For storing and querying embeddings
- **Many-to-many relationships**: Via link tables
- **Normalized structure**: Authors, journals, and tags are separate tables
- **Vector similarity search**: Efficient k-NN queries on embeddings

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
       container 'community.wave.seqera.io/library/pip_google-genai_pgvector_sqlmodel:852aa324a19aa1fc'
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
4. **Add subcommand** to `bin/llm_process_articles.py`:
   ```python
   new_stage_parser = subparsers.add_parser("new_stage")
   new_stage_parser = add_llm_arguments(new_stage_parser, include_research_interests=False)
   ```
5. **Update validation logic** in `bin/common/validation.py` to handle the new response type
6. **Integrate** into `workflows/articles.nf`

### Adding a New Backend

1. **Create workflow** in `workflows/new_backend.nf`:
   ```nextflow
   workflow FROM_NEW_BACKEND { ... }
   workflow TO_NEW_BACKEND { ... }
   ```
2. **Create processes** in `modules/new_backend.nf`
3. **Add Python scripts** in `bin/` (e.g., `new_backend_fetch.py`, `db_*.py` pattern)
4. **Register** in `main.nf`:
   ```nextflow
   if (params.from == "new_backend") {
       FROM_NEW_BACKEND(...)
   }
   ```
5. **Add parameters** to `nextflow.config` and `nextflow_schema.json`
6. **Add database connection logic** to `bin/common/db.py` if needed

### Adding a New Database Model

1. **Define SQLModel class** in `bin/common/models.py`:
   ```python
   class NewTable(SQLModel, table=True):
       __tablename__ = "new_table"
       id: int | None = Field(default=None, primary_key=True)
       name: str = Field(index=True, unique=True)
   ```
2. **Create link table** if many-to-many relationship:
   ```python
   class ArticleNewLink(SQLModel, table=True):
       __tablename__ = "article_new_link"
       article_id: int = Field(default=None, foreign_key="articles.id", primary_key=True)
       new_id: int = Field(default=None, foreign_key="new_table.id", primary_key=True)
   ```
3. **Add relationship** to `ArticleTable`:
   ```python
   new_items: List["NewTable"] = Relationship(
       back_populates="articles", link_model=ArticleNewLink
   )
   ```
4. **Update `setup_db()`** in `bin/common/db.py` if special initialization needed
5. **Run migration**: The schema is auto-created via `SQLModel.metadata.create_all(engine)`

### Database Scripts

The project includes several `db_*.py` scripts for database operations:

- **`db_insert_article.py`**: Insert articles into PostgreSQL or DuckDB
- **`db_update_field.py`**: Update specific fields in database records
- **`db_remove_processed.py`**: Remove duplicate/already-processed articles from input
- **`db_find_nearest_neighbors.py`**: Find k-nearest neighbors using vector similarity
  - Uses pgvector's `cosine_distance` function for similarity search
  - Adds `nearest_neighbors` field to each article with formatted text of similar articles
  - Example usage:
    ```bash
    db_find_nearest_neighbors.py pg \
        --articles_json input.json \
        --user myuser \
        --host localhost:5432/mydb \
        --out output.json
    ```

### Testing Changes

**Python Unit Tests:**
```bash
cd bin
uv run pytest tests/
```

**Run Test Workflow:**
```bash
nextflow run main.nf \
    --mode screen \
    --from articles_json \
    --from_json_input test_articles.json \
    --to articles_json \
    --debug
```

**Test Specific Process:**
```bash
nextflow run main.nf -entry EMBED_ARTICLES --debug
```

**Test Database Connection:**
```bash
cd bin
uv run python -c "from common.db import setup_db, build_connection_string; \
    setup_db(build_connection_string('user', 'localhost:5432/dbname'))"
```

---

## 🔍 Common Code Patterns

### Nextflow: Batching Articles

```nextflow
// Batch articles into groups of 10
batched = batchArticles(articles_channel, 10)

// Filter by field and batch
filtered = filterAndBatch(articles_channel, 10, "doi", null)
// Returns: filtered.match (articles where field != value), filtered.no_match (articles where field == value)
```

### Python: LLM Chat

```python
from common.llm import chat
from common.validation import validate_llm_response, save_validated_responses

response = chat(
    articles=articles,
    system_prompt_path=system_prompt_path,
    research_interests_path=research_interests_path,
    model=model,
    api_key=api_key,
    tools=tools  # Optional: for metadata extraction
)

# Validate response
response_pass = validate_llm_response(
    stage=stage,
    response_text=response,
    merge_key=merge_key,  # "url" for metadata, "doi" for tagging
    allow_qc_errors=allow_qc_errors
)

# Save to pass/fail JSON files
save_validated_responses(
    articles=articles,
    response_pass=response_pass,
    allow_qc_errors=allow_qc_errors,
    stage=stage,
    merge_key=merge_key
)
```

### Python: Generate Embeddings

```python
from common.llm import embed

embeddings = embed(
    texts=["Article title and abstract", "Another article"],
    model="gemini-embedding-001",
    api_key=api_key,
    task="CLASSIFICATION"  # or "RETRIEVAL_QUERY", "RETRIEVAL_DOCUMENT"
)
```

### Python: Database Operations

```python
from common.db import build_connection_string, setup_db
from sqlmodel import create_engine, Session, select
from common.models import ArticleTable, Tag

# Connect to database
connection_string = build_connection_string(user="myuser", host="localhost:5432/mydb")
setup_db(connection_string)  # Create tables if needed
engine = create_engine(connection_string)

# Insert article
with Session(engine) as session:
    article = ArticleTable(
        title="Sample Article",
        url="https://example.com/article",
        doi="10.1234/example",
        ...
    )
    session.add(article)
    session.commit()

# Query articles
with Session(engine) as session:
    statement = select(ArticleTable).where(ArticleTable.doi == "10.1234/example")
    article = session.exec(statement).first()

# Find k-nearest neighbors using vector similarity
with Session(engine) as session:
    statement = (
        select(ArticleTable)
        .order_by(ArticleTable.embedding.cosine_distance(target_embedding))
        .limit(5)
    )
    neighbors = session.exec(statement).all()
```

### Python: Article Text Representation

```python
from common.utils import article_to_text

# Convert article to text for embedding or display
text = article_to_text(article)
# Returns formatted text with title, journal, authors, summary, and tags
```

### Python: Article Manipulation

```python
from common.models import Article, ArticleList
import pathlib

# Load articles
json_string = pathlib.Path("articles.json").read_text()
articles = ArticleList.validate_json(json_string)

# Update article
for article in articles:
    article.reasoning = "Relevant to my interests"
    article.tags = ["Computational Biology", "Drug Discovery"]

# Save articles
pathlib.Path("output.json").write_text(
    ArticleList.dump_json(articles, indent=2).decode()
)
```

### Python: Research Interests Parsing

```python
from compute_article_score import load_research_interests, compute_article_score

# Load hierarchical research interests
research_interests = load_research_interests("config/research_interests.md")
# Returns dict with "field", "applications", "preferred_article_types", "preferred_journals" keys
# Each with list of categories with name, description, points, and optional subcategories

# Compute score based on tags
score = compute_article_score(article, research_interests)
# Score is sum of points for matching tags, respecting hierarchy
```

**Research Interests Structure:**
The `research_interests.md` file uses a hierarchical YAML structure with:
- **field**: Research fields (e.g., "Computational Biology") with optional subcategories (e.g., "Network Biology")
- **applications**: Applications of interest (e.g., "Drug Discovery") with optional subcategories
- **preferred_article_types**: Types of articles (e.g., "Review", "New Computational Method")
- **preferred_journals**: Preferred journals with their own point values

Each category has:
- `name`: The category name (used as a tag)
- `description`: Detailed description for LLM guidance
- `points`: Weight for scoring (can be negative for penalties)
- `subcategories` (optional): Nested categories with their own points

---

## ⚙️ Configuration

### Configuration Files

The project uses two configuration files:

1. **`nextflow.config`**: Default parameter values and process configuration
2. **`config/config.yaml`**: User-specific overrides (not committed to git)

Parameters in `config.yaml` override those in `nextflow.config`. Command-line parameters override both.

### Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `mode` | `learn` | Operational mode (`learn` or `screen`) |
| `from` | `journals_tsv` | Input backend |
| `to` | `articles_json` | Output backend |
| `from_json_input` | `articles.json` | JSON input file path |
| `from_duckdb_input` | `papers_please.duckdb` | DuckDB input file path |
| `from_pg_user` | `null` | PostgreSQL username (input) |
| `from_pg_host` | `null` | PostgreSQL host:port/db (input) |
| `to_json_outdir` | `./results` | Output directory for JSON |
| `to_pg_user` | `null` | PostgreSQL username (output) |
| `to_pg_host` | `null` | PostgreSQL host:port/db (output) |
| `journals_tsv` | (from config) | Path to journals TSV file |
| `research_interests` | (from config) | Path to research interests MD file |
| `days_back` | `8` | Days to look back for articles |
| `batch_size` | `10` | Articles per batch for LLM |
| `metadata_extraction_model` | `gemini-2.5-flash-lite` | LLM for metadata extraction |
| `metadata_extraction_system_prompt` | `prompts/metadata_extraction.md` | Prompt for metadata |
| `tagging_model` | `gemini-2.5-flash-lite` | LLM for tagging articles |
| `tagging_system_prompt` | `prompts/tagging.md` | Prompt for tagging |
| `embedding_model` | `gemini-embedding-001` | Model for generating embeddings |
| `zotero_user_id` | `null` | Zotero user ID |
| `zotero_collection_id` | `null` | Zotero collection ID |
| `zotero_library_type` | `user` | Zotero library type |
| `debug` | `false` | Enable debug logging |

### Secrets Required

- `GOOGLE_API_KEY`: Google AI Studio API key (required)
- `USER_EMAIL`: Email for CrossRef/NCBI APIs (required)
- `SPRINGER_META_API_KEY`: Springer API key (optional)
- `ZOTERO_API_KEY`: Zotero API key (optional, for `--to zotero`)
- `PGPASSWORD`: PostgreSQL password (optional, for PostgreSQL backends)

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

2. **Branch**: Currently on `feat/modelsql` - working branch for integrating SQLModel and database backends.

3. **Database**: DuckDB and PostgreSQL backends store processed articles with full relational structure and vector embeddings.

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
