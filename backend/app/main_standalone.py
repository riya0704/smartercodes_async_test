from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List
import requests
from bs4 import BeautifulSoup
from transformers import AutoTokenizer
from sentence_transformers import SentenceTransformer
import numpy as np

# Request/response models
class SearchRequest(BaseModel):
    url: HttpUrl
    query: str

class ChunkResult(BaseModel):
    content: str
    url: str
    score: float

class SearchResponse(BaseModel):
    results: List[ChunkResult]

app = FastAPI(title="Website DOM Search API")

# CORS - pretty open for dev, would lock this down in prod
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store chunks in memory - gets wiped on restart but that's fine for now
chunks_store = []

# ML models - lazy loaded on first request
tokenizer = None
embedder = None


def initialize_models():
    """Load the models if they haven't been loaded yet"""
    global tokenizer, embedder
    if tokenizer is None:
        print("Loading BERT tokenizer (first time takes a sec)...")
        tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
    if embedder is None:
        print("Loading sentence transformer model...")
        embedder = SentenceTransformer("all-MiniLM-L6-v2")


def clean_html(html: str) -> str:
    """Strip out all the junk from HTML and just get the text"""
    soup = BeautifulSoup(html, "html.parser")
    
    # Remove scripts, styles, and other non-content tags
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    
    text = soup.get_text(separator=" ", strip=True)
    return text


def chunk_text(text: str, max_tokens: int = 500, overlap_words: int = 50) -> List[str]:
    """
    Break text into chunks of ~500 tokens with some overlap between chunks.
    
    The overlap is important - if we just split at exactly 500 tokens, we might
    cut a sentence in half or lose context. By keeping the last 50 words from
    each chunk in the next one, we make sure related content stays together.
    """
    words = text.split()
    chunks = []
    current_chunk = []
    token_count = 0

    for word in words:
        # Count tokens for this word
        word_tokens = tokenizer.tokenize(word)
        word_token_count = len(word_tokens)

        # If adding this word would go over the limit, save current chunk
        if token_count + word_token_count > max_tokens and current_chunk:
            chunks.append(" ".join(current_chunk))
            
            # Keep some overlap - take last N words from previous chunk
            if len(current_chunk) > overlap_words:
                current_chunk = current_chunk[-overlap_words:]
                # Recount tokens for the overlap
                token_count = sum(len(tokenizer.tokenize(w)) for w in current_chunk)
            else:
                current_chunk = []
                token_count = 0
        
        current_chunk.append(word)
        token_count += word_token_count

    # Don't forget the last chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def index_chunks(url: str, chunks: List[str]) -> None:
    """Convert chunks to vectors and store them"""
    global chunks_store
    
    # Clear out any old chunks from this URL first
    chunks_store = [item for item in chunks_store if item["url"] != url]
    
    # Encode each chunk and add to store
    for chunk in chunks:
        embedding = embedder.encode(chunk, convert_to_numpy=True)
        chunks_store.append({
            "content": chunk,
            "url": url,
            "vector": embedding
        })
    
    print(f"Stored {len(chunks)} chunks from {url} (total in memory: {len(chunks_store)})")


def search_chunks(query: str, limit: int = 10) -> List[ChunkResult]:
    """Find the most similar chunks to the query using cosine similarity"""
    if not chunks_store:
        return []
    
    # Encode the search query
    query_vec = embedder.encode(query, convert_to_numpy=True)
    
    # Compare query to each chunk
    matches = []
    for item in chunks_store:
        chunk_vec = item["vector"]
        
        # Calculate cosine similarity (dot product / magnitudes)
        similarity = np.dot(query_vec, chunk_vec) / (
            np.linalg.norm(query_vec) * np.linalg.norm(chunk_vec)
        )
        
        matches.append({
            "content": item["content"],
            "url": item["url"],
            "score": float(similarity)
        })
    
    # Sort by best matches first
    matches.sort(key=lambda x: x["score"], reverse=True)
    
    # Return top results
    return [ChunkResult(**m) for m in matches[:limit]]


@app.on_event("startup")
async def startup_event():
    print("Starting up...")
    initialize_models()
    print("Ready to search!")


@app.get("/health")
def health():
    return {"status": "ok", "mode": "standalone", "message": "All systems go"}


@app.post("/api/search", response_model=SearchResponse)
def search(request: SearchRequest):
    initialize_models()
    
    # Fetch the webpage
    try:
        print(f"Fetching: {request.url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        resp = requests.get(str(request.url), headers=headers, timeout=30)
        resp.raise_for_status()
        print(f"Got {len(resp.text)} chars from {request.url}")
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=400, detail="Request timed out - site took too long to respond")
    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=400, detail=f"HTTP {e.response.status_code}: {e.response.reason}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Couldn't fetch URL: {str(e)}")

    # Extract text from HTML
    print("Extracting text from HTML...")
    text = clean_html(resp.text)
    
    if not text:
        raise HTTPException(status_code=400, detail="No text content found on that page")

    # Split into chunks
    print(f"Splitting into chunks (text is {len(text)} chars)...")
    chunks = chunk_text(text, max_tokens=500, overlap_words=50)
    
    if not chunks:
        raise HTTPException(status_code=400, detail="Couldn't create chunks from the content")

    # Debug: show chunk info
    print(f"Made {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks[:3], 1):
        tokens = len(tokenizer.tokenize(chunk))
        print(f"  Chunk {i}: {tokens} tokens, {len(chunk)} chars")
    if len(chunks) > 3:
        print(f"  ...plus {len(chunks) - 3} more")
    
    # Store chunks with embeddings
    print("Creating embeddings and storing...")
    index_chunks(str(request.url), chunks)

    # Search
    print(f"Searching for: '{request.query}'")
    results = search_chunks(request.query, limit=10)
    print(f"Found {len(results)} results")

    return SearchResponse(results=results)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
