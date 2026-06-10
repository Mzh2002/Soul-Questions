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
- **User-configurable LLM** — choose model (GPT-4o, GPT-4, etc.) and enter your own API key from the UI
- **Configurable embeddings** — swap embeddings (sentence-transformers/OpenAI) and vector store (Chroma/FAISS) via `.env`
- **Production-ready** — Docker Compose with PostgreSQL, Nginx, Gunicorn, Whitenoise
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
- `OPENAI_API_KEY` — for LLM-powered answers (users can also provide their own key via the settings UI)

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
| `LLM_MODEL` | `gpt-4o-mini` | Default model name |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `DATABASE_URL` | — | PostgreSQL URL (empty = SQLite) |
| `CSRF_TRUSTED_ORIGINS` | — | Trusted origins for CSRF |
| `POSTGRES_PASSWORD` | `changeme` | PostgreSQL password (docker-compose) |
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

## Deployment (Docker + AWS)

### Local Docker

```bash
# Create production .env
cp .env.example .env
# Edit .env — set DJANGO_SECRET_KEY, OPENAI_API_KEY, POSTGRES_PASSWORD

# Build and start
docker compose up -d --build

# App is at http://localhost (Nginx on port 80)
# Direct app access at http://localhost:8000
```

### Deploy to AWS EC2

**1. Launch an EC2 instance**

- **AMI**: Amazon Linux 2023 or Ubuntu 22.04
- **Instance type**: `t3.medium` (2 vCPU, 4 GB RAM) minimum — the embedding model needs ~2 GB
- **Storage**: 30 GB gp3
- **Security group**: Allow inbound TCP ports 22 (SSH), 80 (HTTP), 443 (HTTPS)

**2. Install Docker on the instance**

```bash
# Amazon Linux 2023
sudo yum install -y docker git
sudo systemctl start docker && sudo systemctl enable docker
sudo usermod -aG docker $USER
# Log out and back in, then:
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Ubuntu 22.04
sudo apt update && sudo apt install -y docker.io docker-compose-v2 git
sudo usermod -aG docker $USER
# Log out and back in
```

**3. Clone and configure**

```bash
git clone https://github.com/Mzh2002/Soul-Questions.git
cd Soul-Questions

cp .env.example .env
# Edit .env with production values:
#   DJANGO_SECRET_KEY=<random 50-char string>
#   DJANGO_DEBUG=False
#   DJANGO_ALLOWED_HOSTS=your-domain.com,ec2-xx-xx-xx-xx.compute.amazonaws.com
#   CSRF_TRUSTED_ORIGINS=https://your-domain.com
#   OPENAI_API_KEY=sk-...
#   POSTGRES_PASSWORD=<strong password>
```

**4. Build and run**

```bash
docker compose up -d --build

# Check logs
docker compose logs -f web
```

The app is now at `http://<your-ec2-public-ip>`.

**5. (Optional) Build the vector index inside the container**

```bash
# Run ingestion pipeline
docker compose exec web python -m ingestion.collect_urls
docker compose exec web python -m ingestion.scrape_pages
docker compose exec web python -m ingestion.clean_docs
docker compose exec web python -m ingestion.chunk_docs
docker compose exec web python -m ingestion.build_index
```

### Deploy to AWS ECS (Fargate)

For a more scalable setup using ECS:

1. Push your Docker image to **ECR**:
   ```bash
   aws ecr create-repository --repository-name soul-questions
   # Tag and push your image
   docker tag soul-questions:latest <account-id>.dkr.ecr.<region>.amazonaws.com/soul-questions:latest
   docker push <account-id>.dkr.ecr.<region>.amazonaws.com/soul-questions:latest
   ```

2. Create an **RDS PostgreSQL** instance (db.t3.micro for dev, db.t3.small for production)

3. Create an **ECS cluster** with a Fargate service:
   - Task definition: your ECR image, 1 vCPU / 2 GB memory minimum
   - Environment variables: set `DATABASE_URL`, `DJANGO_SECRET_KEY`, `OPENAI_API_KEY`, etc.
   - Port mapping: 8000

4. Add an **Application Load Balancer** (ALB) with HTTPS (use ACM for a free SSL cert)

5. Point your domain's DNS to the ALB

### HTTPS with Let's Encrypt (EC2)

For HTTPS on a bare EC2 setup, install Certbot:

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx  # Ubuntu
# or
sudo yum install -y certbot python3-certbot-nginx   # Amazon Linux

# Get certificate (stop Nginx container first)
docker compose stop nginx
sudo certbot certonly --standalone -d your-domain.com
# Then update nginx.conf to use the certificates
docker compose up -d nginx
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
- Kubernetes Helm chart for large-scale deployments

## License

MIT
