# Website DOM Search - Semantic Search Application

A full-stack application that performs AI-powered semantic search on website content. Enter any URL and search query to find the top 10 most relevant content chunks.

## Features

- Semantic search using Sentence Transformers
- Chunks content into up to 500 tokens each
- Returns top 10 results sorted by relevance
- Clean UI with collapsible HTML preview
- Match percentage indicators

## Tech Stack

- **Frontend**: React + Vite
- **Backend**: FastAPI (Python)
- **NLP**: BERT tokenizer + Sentence Transformers
- **Vector DB**: Weaviate (optional) or In-Memory

## Prerequisites

- Python 3.10+
- Node.js 18+
- 4GB RAM minimum
- Internet connection (for first-time model downloads)

## Quick Start

### 1. Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac
pip install -r requirements.txt
```

### 2. Start Backend

```bash
# Windows
.\run_server.bat

# Linux/Mac
python -m uvicorn app.main_standalone:app --reload --host 0.0.0.0 --port 8000
```

**Note**: First startup downloads models (~500MB, takes 2-5 minutes). Subsequent starts are instant.

Backend runs at: `http://localhost:8000`

### 3. Frontend Setup

Open new terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: `http://localhost:5173`

### 4. Use Application

1. Open browser: `http://localhost:5173`
2. Enter URL: `https://en.wikipedia.org/wiki/Python_(programming_language)`
3. Enter query: `programming language features`
4. Click Search
5. View top 10 results

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

### Test URLs

**Small** (1-3 chunks):
```
URL: https://smarter.codes/
Query: AI
```

**Large** (10+ chunks):
```
URL: https://en.wikipedia.org/wiki/Python_(programming_language)
Query: programming language
```

### Run Test Script

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

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py              # Weaviate version
│   │   └── main_standalone.py   # In-memory version
│   ├── requirements.txt
│   ├── Dockerfile
│   └── run_server.bat
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   └── styles.css
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml
└── README.md
```

## How It Works

1. **Fetch** HTML from URL
2. **Clean** content (remove scripts, styles)
3. **Tokenize** using BERT
4. **Chunk** into 500-token segments with 50-word overlap
5. **Embed** chunks using Sentence Transformers
6. **Index** in vector store
7. **Search** using cosine similarity
8. **Return** top 10 results

## Configuration

### Environment Variables

Create `.env` (optional):
```env
WEAVIATE_URL=http://weaviate:8080
API_PORT=8000
VITE_API_BASE=http://localhost:8000
```

### CORS Settings

Edit `backend/app/main_standalone.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Docker Deployment

```bash
# Start all services
docker-compose up --build -d

# Start frontend
cd frontend
npm install
npm run dev

# Stop services
docker-compose down
```

## Documentation

- `CHUNKING_STRATEGY.md` - Chunking implementation details
- `TESTING_GUIDE.md` - Comprehensive testing guide
- `backend/TROUBLESHOOTING.md` - Detailed error solutions

## License

Educational project for fullstack development assignment.
# smartercodes_async_test
