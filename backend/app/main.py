
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List
import os
import requests
from bs4 import BeautifulSoup

from transformers import AutoTokenizer
from sentence_transformers import SentenceTransformer
import weaviate
from weaviate.classes.config import Configure, Property, DataType


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

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize models
tokenizer = None
embedder = None
client = None

def initialize_models():
    global tokenizer, embedder, client
    if tokenizer is None:
        tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
    if embedder is None:
        embedder = SentenceTransformer("all-MiniLM-L6-v2")
    if client is None:
        WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
        client = weaviate.connect_to_custom(
            http_host="weaviate",
            http_port=8080,
            http_secure=False,
            grpc_host="weaviate",
            grpc_port=50051,
            grpc_secure=False,
        )

CLASS_NAME = "HtmlChunk"


def ensure_schema() -> None:
    try:
        if client.collections.exists(CLASS_NAME):
            return
        
        client.collections.create(
            name=CLASS_NAME,
            properties=[
                Property(name="content", data_type=DataType.TEXT),
                Property(name="url", data_type=DataType.TEXT),
            ],
        )
    except Exception as e:
        print(f"Schema creation error: {e}")


def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    return text


def chunk_text(text: str, max_tokens: int = 500) -> List[str]:
    words = text.split()
    chunks: List[str] = []
    current_words: List[str] = []
    current_tokens = 0

    for word in words:
        tokenized = tokenizer.tokenize(word)
        token_len = len(tokenized)

        if current_tokens + token_len > max_tokens and current_words:
            chunks.append(" ".join(current_words))
            current_words = [word]
            current_tokens = token_len
        else:
            current_words.append(word)
            current_tokens += token_len

    if current_words:
        chunks.append(" ".join(current_words))

    return chunks


def index_chunks(url: str, chunks: List[str]) -> None:
    ensure_schema()
    collection = client.collections.get(CLASS_NAME)
    
    with collection.batch.dynamic() as batch:
        for chunk in chunks:
            vector = embedder.encode(chunk).tolist()
            batch.add_object(
                properties={"content": chunk, "url": url},
                vector=vector
            )


def search_chunks(query: str, limit: int = 10) -> List[ChunkResult]:
    query_vector = embedder.encode(query).tolist()
    
    collection = client.collections.get(CLASS_NAME)
    
    response = collection.query.near_vector(
        near_vector=query_vector,
        limit=limit,
        return_metadata=["distance"]
    )

    hits: List[ChunkResult] = []

    for item in response.objects:
        distance = item.metadata.distance if item.metadata.distance else 0.0
        score = 1.0 - float(distance)
        hits.append(
            ChunkResult(
                content=item.properties.get("content", ""),
                url=item.properties.get("url", ""),
                score=score,
            )
        )

    return hits


@app.on_event("startup")
async def startup_event():
    initialize_models()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/search", response_model=SearchResponse)
def search(request: SearchRequest):
    initialize_models()
    
    try:
        response = requests.get(str(request.url), timeout=10)
        response.raise_for_status()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch URL: {e}",
        )

    clean_text = clean_html(response.text)

    if not clean_text:
        raise HTTPException(
            status_code=400,
            detail="No readable text content found at the provided URL.",
        )

    chunks = chunk_text(clean_text, max_tokens=500)

    if not chunks:
        raise HTTPException(
            status_code=400,
            detail="Failed to chunk content from the provided URL.",
        )

    index_chunks(str(request.url), chunks)

    results = search_chunks(request.query, limit=10)

    return SearchResponse(results=results)
