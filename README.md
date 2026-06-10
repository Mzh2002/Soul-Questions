# ⚔️ Soul Questions

A RAG-based chatbot for Souls-like games powered by **Django**, **LangGraph**, and **ChromaDB/FAISS**.

Ask questions about lore, bosses, items, builds, locations, quests, mechanics, endings, NPCs, weapons, armor, maps, and game progression across:

- Dark Souls 1 / 2 / 3
- Elden Ring & Elden Ring: Nightreign
- Bloodborne
- Sekiro: Shadows Die Twice
- Demon's Souls

## Features

- **ChatGPT-style UI** — dark theme, sidebar sessions, message bubbles
- **RAG pipeline via LangGraph** — query understanding → retrieval → reranking → answer generation → citations → follow-up recommendations
- **Session management** — create, rename, delete conversations; full message history
- **Source citations** — answers cite retrieved documents with `[Source N]` notation
- **Follow-up recommendations** — 3–5 contextual suggested questions after each answer
- **Configurable providers** — swap LLM (OpenAI/Ollama), embeddings (sentence-transformers/OpenAI), and vector store (Chroma/FAISS) via `.env`
- **Document ingestion pipeline** — URL collection, scraping, cleaning, chunking, indexing

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/Mzh2002/Soul-Questions.git
cd Soul-Questions
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your API keys and preferences
```

**Required for LLM answers:**
- `OPENAI_API_KEY` — if using OpenAI as the LLM provider
- Or configure Ollama for local inference (see `.env.example`)

### 3. Initialize Django

```bash
python manage.py migrate
python manage.py createsuperuser   # optional
```

### 4. Collect and process documents

```bash
# Step 1: Collect URLs from Fextralife wikis
python -m ingestion.collect_urls

# Step 2: Scrape pages (respects robots.txt, rate-limited)
python -m ingestion.scrape_pages

# Step 3: Clean raw HTML to plain text
python -m ingestion.clean_docs

# Step 4: Chunk documents for RAG
python -m ingestion.chunk_docs

# Step 5: Build vector index
python -m ingestion.build_index
# To rebuild from scratch:
python -m ingestion.build_index --rebuild
```

### 5. Run the app

```bash
python manage.py runserver
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

## Project Structure

```
Soul-Questions/
├── manage.py                  # Django management
├── requirements.txt           # Python dependencies
├── .env.example               # Environment template
├── pytest.ini                 # Test configuration
├── souls_rag/                 # Django project settings
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── chat/                      # Django chat app
│   ├── models.py              # ChatSession, ChatMessage, RetrievedSource, RecommendedQuestion
│   ├── views.py               # Web views + AJAX endpoints
│   ├── urls.py                # URL routing
│   ├── services.py            # RAG pipeline integration
│   ├── admin.py               # Django admin registration
│   ├── templates/chat/        # HTML templates
│   └── static/chat/           # CSS + JavaScript
├── rag/                       # RAG pipeline module
│   ├── graph.py               # LangGraph workflow (7 nodes)
│   ├── retriever.py           # Vector store retrieval (Chroma/FAISS)
│   ├── embeddings.py          # Configurable embedding functions
│   ├── reranker.py            # Keyword + semantic reranking
│   ├── prompts.py             # System/context/rewrite/recommendation prompts
│   ├── citations.py           # Source citation formatting
│   └── recommendations.py     # Follow-up question generation
├── ingestion/                 # Document ingestion pipeline
│   ├── collect_urls.py        # Seed URL discovery
│   ├── scrape_pages.py        # Rate-limited web scraping
│   ├── clean_docs.py          # HTML → clean text
│   ├── chunk_docs.py          # Text chunking with overlap
│   └── build_index.py         # Vector store indexing
├── tests/                     # Test suite
│   ├── test_chunking.py
│   ├── test_citations.py
│   ├── test_reranker.py
│   └── test_models.py
└── data/                      # Data directories (git-ignored)
    ├── raw/                   # Raw scraped HTML
    ├── processed/             # Cleaned text documents
    ├── chunks/                # JSONL chunk files
    └── vectorstore/           # Chroma/FAISS index
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DJANGO_SECRET_KEY` | `insecure-dev-key` | Django secret key |
| `DJANGO_DEBUG` | `True` | Debug mode |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Allowed hosts |
| `LLM_PROVIDER` | `openai` | `openai` or `ollama` |
| `LLM_MODEL` | `gpt-4o-mini` | Model name |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `EMBEDDING_PROVIDER` | `sentence-transformers` | `sentence-transformers` or `openai` |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Embedding model name |
| `VECTOR_STORE` | `chroma` | `chroma` or `faiss` |

## LangGraph RAG Pipeline

The pipeline consists of 7 nodes:

1. **Query Understanding** — detects game context, decides if rewrite needed
2. **Query Rewrite** (conditional) — rewrites ambiguous queries using conversation history
3. **Retrieve** — vector similarity search against Chroma/FAISS
4. **Rerank** — keyword overlap + semantic score combination
5. **Generate Answer** — LLM with system prompt enforcing citation rules
6. **Format Citations** — extracts `[Source N]` references from the answer
7. **Recommend Follow-ups** — generates 3–5 contextual follow-up questions

## Example Questions

Try these to test the system:

- "Who is the hardest boss in Dark Souls 3?"
- "Explain the lore of the Elden Ring and the Shattering"
- "What builds work best for a Bloodborne beginner?"
- "Compare the combat systems of Sekiro and Dark Souls"
- "Where can I find the Moonlight Greatsword in each game?"
- "What happens in Ranni's questline in Elden Ring?"
- "How does the Insight mechanic work in Bloodborne?"
- "What are the different endings in Dark Souls 3?"

## Running Tests

```bash
pytest
```

## Limitations

- **Data quality depends on scraping** — wiki pages change, and scraping may miss some content
- **Rate limiting on scraping** — initial data collection takes time to respect site limits
- **Reranker is basic** — uses keyword overlap; a cross-encoder model would improve relevance
- **No user authentication** — all sessions are public; add Django auth for multi-user deployments
- **No streaming responses** — answers appear after full generation; streaming would improve UX

## Future Improvements

- Add cross-encoder reranking (e.g., `ms-marco-MiniLM`)
- Implement streaming responses via Server-Sent Events
- Add user authentication and per-user sessions
- Support additional data sources (Reddit, YouTube transcripts)
- Add image/map display for location queries
- Implement conversation export
- Add Elden Ring: Nightreign-specific data sources
- PostgreSQL support for production deployments
- Docker Compose for one-command deployment

## License

MIT
