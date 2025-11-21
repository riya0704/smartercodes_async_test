# Website Semantic Search

A full-stack app that lets you search through any website using AI-powered semantic search. Just paste a URL and your search query, and it'll find the most relevant content chunks.

## Demo Video

**Note:** The demo video is a screen recording showing the application in action. Since this is a visual demonstration of the UI and functionality, there's no audio narration - the video speaks for itself by showing the search process, results display, and interaction flow.

## What it does

- Fetches and parses HTML from any URL
- Breaks content into ~500 token chunks with overlap
- Uses sentence transformers to create embeddings
- Finds top 10 most relevant chunks using cosine similarity
- Shows match scores and lets you expand to see full content

## Tech Stack

- **Frontend**: React with Vite (fast dev server)
- **Backend**: FastAPI (Python web framework)
- **NLP**: BERT tokenizer for chunking, Sentence Transformers for embeddings
- **Storage**: In-memory (standalone mode) or Weaviate vector DB (optional)

## What you need

- Python 3.10 or newer
- Node.js 18 or newer
- At least 4GB RAM
- Internet (models download on first run, ~500MB)

## Getting Started

### Backend

First, set up the Python environment:

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
```

Then start the server:

```bash
# Windows
.\run_server.bat

# Mac/Linux
python -m uvicorn app.main_standalone:app --reload --host 0.0.0.0 --port 8000
```

**First run takes a few minutes** because it downloads the ML models (~500MB). After that it starts instantly.

The API will be running at `http://localhost:8000`

### Frontend

Open a new terminal and:

```bash
cd frontend
npm install
npm run dev
```

This starts the dev server at `http://localhost:5173`

### Try it out

1. Go to `http://localhost:5173` in your browser
2. Paste a URL (try `https://en.wikipedia.org/wiki/Python_(programming_language)`)
3. Enter a search query (like `programming language features`)
4. Hit Search
5. Check out the top 10 matching chunks

## Dependencies

### Backend (`requirements.txt`)

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
requests==2.31.0
beautifulsoup4==4.12.2
transformers==4.35.2
sentence-transformers==2.7.0
weaviate-client==4.4.0
pydantic==2.5.0
torch==2.1.1
numpy==1.24.3
lxml==4.9.3
huggingface-hub==0.23.0
```

### Frontend (`package.json`)

```json
{
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "vite": "^5.0.0"
}
```

## Vector Database Setup (Optional)

### Standalone Mode (Default)
- In-memory storage
- No setup required
- Data cleared on restart

### Weaviate Mode (Persistent Storage)

```bash
# Start Weaviate
docker-compose up weaviate -d

# Verify
curl http://localhost:8080/v1/.well-known/ready

# Use Weaviate backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Schema** (auto-created):
```json
{
  "class": "HtmlChunk",
  "properties": [
    {"name": "content", "dataType": ["text"]},
    {"name": "url", "dataType": ["text"]}
  ]
}
```

## API Endpoints

### POST `/api/search`

```bash
curl -X POST "http://localhost:8000/api/search" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "query": "search term"
  }'
```

**Response:**
```json
{
  "results": [
    {
      "content": "Content chunk (up to 500 tokens)...",
      "url": "https://example.com",
      "score": 0.95
    }
  ]
}
```

### GET `/health`

```bash
curl http://localhost:8000/health
```

## Testing

Some URLs to try:

**Small site** (few chunks):
- URL: `https://smarter.codes/`
- Query: `AI`

**Larger site** (many chunks):
- URL: `https://en.wikipedia.org/wiki/Python_(programming_language)`
- Query: `programming language`

You can also run the test script:

```bash
cd backend
python test_api.py
```

## Troubleshooting

### Port in use
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

### Models not downloading
- Check internet connection
- Wait 2-5 minutes for first download
- Models cached in `~/.cache/huggingface/`

### CORS errors
- Ensure backend is running on port 8000
- Restart backend server
- Clear browser cache

## How it works

The search process:

1. Fetch the HTML from the URL you provide
2. Strip out scripts, styles, and other junk
3. Use BERT tokenizer to count tokens
4. Split text into chunks of ~500 tokens (with 50 words of overlap so we don't cut sentences awkwardly)
5. Generate embeddings for each chunk using Sentence Transformers
6. Store chunks with their embeddings in memory
7. When you search, encode your query and compare it to all chunks using cosine similarity
8. Return the top 10 best matches

## Docker (Optional)

If you want to use Docker:

```bash
# Start backend with Weaviate
docker-compose up --build -d

# Frontend still needs to run locally
cd frontend
npm install
npm run dev

# Stop everything
docker-compose down
```

## Notes

This was built as a learning project to understand semantic search and vector embeddings. The standalone version keeps everything in memory which is fine for demos but you'd want to use Weaviate or another vector DB for production.
