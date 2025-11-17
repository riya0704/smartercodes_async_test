"""
Standalone version of the backend that works without Weaviate.
Uses in-memory storage for testing purposes.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List
import requests
from bs4 import BeautifulSoup
from transformers import AutoTokenizer
from sentence_transformers import SentenceTransformer
import numpy as np


class SearchRequest(BaseModel):
    url: HttpUrl
    query: str


class ChunkResult(BaseModel):
    content: str
    url: str
    score: float


class SearchResponse(BaseModel):
    results: List[ChunkResult]


app = FastAPI(title="Website DOM Search API (Standalone)")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Global storage for chunks (in-memory)
chunks_store = []

# Initialize models
tokenizer = None
embedder = None


def initialize_models():
    global tokenizer, embedder
    if tokenizer is None:
        print("Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
    if embedder is None:
        print("Loading embedder...")
        embedder = SentenceTransformer("all-MiniLM-L6-v2")


def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    return text


def chunk_text(text: str, max_tokens: int = 500, overlap_words: int = 50) -> List[str]:
    """Split text into overlapping chunks of up to 500 tokens for better search coverage"""
    words = text.split()
    chunks: List[str] = []
    current_words: List[str] = []
    current_tokens = 0

    for word in words:
        tokenized = tokenizer.tokenize(word)
        token_len = len(tokenized)

        if current_tokens + token_len > max_tokens and current_words:
            # Save current chunk
            chunks.append(" ".join(current_words))
            # Create overlap: keep last N words for next chunk
            if len(current_words) > overlap_words:
                current_words = current_words[-overlap_words:]
                current_tokens = sum(len(tokenizer.tokenize(w)) for w in current_words)
            else:
                current_words = []
                current_tokens = 0
            # Add current word
            current_words.append(word)
            current_tokens += token_len
        else:
            current_words.append(word)
            current_tokens += token_len

    # Add remaining words as final chunk
    if current_words:
        chunks.append(" ".join(current_words))

    return chunks


def index_chunks(url: str, chunks: List[str]) -> None:
    """Store chunks with their embeddings in memory"""
    global chunks_store
    
    # Remove old chunks from the same URL
    chunks_store = [item for item in chunks_store if item["url"] != url]
    
    # Add new chunks
    for chunk in chunks:
        vector = embedder.encode(chunk, convert_to_numpy=True)
        chunks_store.append({
            "content": chunk,
            "url": url,
            "vector": vector
        })
    print(f"Indexed {len(chunks)} new chunks (total: {len(chunks_store)} chunks)")


def search_chunks(query: str, limit: int = 10) -> List[ChunkResult]:
    """Search chunks using cosine similarity"""
    if not chunks_store:
        return []
    
    query_vector = embedder.encode(query, convert_to_numpy=True)
    
    # Calculate cosine similarity for each chunk
    results = []
    for item in chunks_store:
        chunk_vector = item["vector"]
        # Cosine similarity
        similarity = np.dot(query_vector, chunk_vector) / (
            np.linalg.norm(query_vector) * np.linalg.norm(chunk_vector)
        )
        results.append({
            "content": item["content"],
            "url": item["url"],
            "score": float(similarity)
        })
    
    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    
    # Return top N results
    return [
        ChunkResult(
            content=r["content"],
            url=r["url"],
            score=r["score"]
        )
        for r in results[:limit]
    ]


@app.on_event("startup")
async def startup_event():
    print("Starting up...")
    initialize_models()
    print("Models loaded successfully!")


@app.get("/health")
def health():
    return {"status": "ok", "mode": "standalone"}


@app.post("/api/search", response_model=SearchResponse)
def search(request: SearchRequest):
    initialize_models()
    
    try:
        print(f"Fetching URL: {request.url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(str(request.url), headers=headers, timeout=30)
        response.raise_for_status()
        print(f"Successfully fetched {len(response.text)} characters")
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=400,
            detail=f"Request timed out. The website took too long to respond.",
        )
    except requests.exceptions.HTTPError as e:
        raise HTTPException(
            status_code=400,
            detail=f"HTTP Error {e.response.status_code}: {e.response.reason}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch URL: {str(e)}",
        )

    print("Cleaning HTML...")
    clean_text = clean_html(response.text)

    if not clean_text:
        raise HTTPException(
            status_code=400,
            detail="No readable text content found at the provided URL.",
        )

    print(f"Chunking text... (text length: {len(clean_text)} chars)")
    chunks = chunk_text(clean_text, max_tokens=500, overlap_words=50)

    if not chunks:
        raise HTTPException(
            status_code=400,
            detail="Failed to chunk content from the provided URL.",
        )

    # Log token counts for each chunk
    print(f"Created {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks[:3], 1):  # Show first 3
        token_count = len(tokenizer.tokenize(chunk))
        print(f"  Chunk {i}: {token_count} tokens, {len(chunk)} chars")
    if len(chunks) > 3:
        print(f"  ... and {len(chunks) - 3} more chunks")
    
    print("Indexing chunks...")
    index_chunks(str(request.url), chunks)

    print(f"Searching for: '{request.query}'")
    results = search_chunks(request.query, limit=10)
    print(f"Returning top {len(results)} results (max 10)")

    return SearchResponse(results=results)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
