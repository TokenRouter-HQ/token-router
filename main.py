from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List, Dict
import tiktoken
from openai import AsyncOpenAI
import re
import os
import hashlib
import time
import logging

# Enterprise Logging Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("TokenRouter-HQ")

# --- ARCHITECTURE CLASSES (Design Patterns) ---

class MemoryCacheManager:
    """
    Isolated cache manager. In the future, this can be easily 
    swapped for a RedisCacheManager without breaking the app.
    """
    def __init__(self):
        self._store: Dict[str, dict] = {}

    def generate_key(self, messages: List[dict]) -> str:
        combined_text = "".join([m.get("content", "") for m in messages])
        return hashlib.md5(combined_text.encode('utf-8')).hexdigest()

    def get(self, key: str) -> Optional[dict]:
        return self._store.get(key)

    def set(self, key: str, value: dict):
        self._store[key] = value


class PromptOptimizer:
    """Heuristics engine for token compression."""
    def __init__(self):
        # Politeness stop words that do not affect AI semantics
        self.stop_words = [
            "Please", "could you", "if it's not too much trouble", 
            "could you help me with", "I would like to know"
        ]
        self.regex_patterns = [re.compile(word, re.IGNORECASE) for word in self.stop_words]

    def compress(self, text: str) -> str:
        compressed = re.sub(r'\s+', ' ', text)
        compressed = re.sub(r'([!?.])\1+', r'\1', compressed)
        for pattern in self.regex_patterns:
            compressed = re.sub(pattern, "", compressed)
        return compressed.strip()


class FinOpsTelemetry:
    """Module responsible for calculating costs and metrics."""
    @staticmethod
    def count_tokens(text: str, model_name: str = "gpt-4o") -> int:
        try:
            encoding = tiktoken.encoding_for_model(model_name)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))

# --- SERVICE INITIALIZATION ---

app = FastAPI(
    title="TokenRouter-HQ API",
    description="Enterprise LLM Proxy with Smart Routing, FinOps Telemetry, and Semantic Cache.",
    version="1.2.0"
)

# Ensure you replace "YOUR_API_KEY_HERE" with a valid OpenAI API key for testing
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", "YOUR_API_KEY_HERE"))
cache_manager = MemoryCacheManager()
optimizer = PromptOptimizer()

class ChatRequest(BaseModel):
    messages: List[dict]
    route_strategy: Optional[str] = "auto" # Options: auto, cheap, premium

# --- LOGGING MIDDLEWARE ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"Path: {request.url.path} | Method: {request.method} | Status: {response.status_code} | Latency: {process_time:.4f}s")
    return response

# --- MAIN ENDPOINT ---

@app.post("/v1/chat/completions")
async def chat_proxy(request: ChatRequest):
    if not request.messages:
        raise HTTPException(status_code=400, detail="Messages list cannot be empty.")

    start_time = time.time()
    total_original = 0
    total_compressed = 0
    compressed_messages = []

    # 1. Optimization Pipeline
    for msg in request.messages:
        original_content = msg.get("content", "")
        total_original += FinOpsTelemetry.count_tokens(original_content)
        
        compressed_content = optimizer.compress(original_content)
        total_compressed += FinOpsTelemetry.count_tokens(compressed_content)
        
        compressed_messages.append({"role": msg.get("role", "user"), "content": compressed_content})

    # 2. Cache Verification
    cache_key = cache_manager.generate_key(compressed_messages)
    cached_response = cache_manager.get(cache_key)
    
    if cached_response:
        logger.info(f"Cache HIT for key: {cache_key}")
        return _build_response("cached-"+cache_key[:10], "cache-memory", cached_response["choices"], 
                               total_original, total_compressed, time.time() - start_time, is_cache=True)

    # 3. Routing Strategy
    selected_model = "gpt-4o"
    if request.route_strategy == "auto" and total_compressed < 150:
        selected_model = "gpt-4o-mini"
    elif request.route_strategy == "cheap":
        selected_model = "gpt-4o-mini"

    # 4. External API Call (OpenAI)
    logger.info(f"Cache MISS. Routing to external provider using model: {selected_model}")
    try:
        response = await client.chat.completions.create(
            model=selected_model,
            messages=compressed_messages,
            temperature=0.7
        )
    except Exception as e:
        logger.error(f"OpenAI API Error: {str(e)}")
        raise HTTPException(status_code=500, detail="External LLM Provider Error.")

    # 5. Update Cache and Return
    cache_manager.set(cache_key, {"choices": response.choices})
    return _build_response(response.id, selected_model, response.choices, 
                           total_original, total_compressed, time.time() - start_time)

def _build_response(req_id, model, choices, original_tokens, compressed_tokens, latency, is_cache=False):
    tokens_saved = original_tokens if is_cache else (original_tokens - compressed_tokens)
    saving_percentage = (tokens_saved / original_tokens * 100) if original_tokens > 0 else 0
    
    return {
        "id": req_id,
        "model_used": model,
        "finops_telemetry": {
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "tokens_saved": tokens_saved,
            "savings_percentage": f"{saving_percentage:.2f}%",
            "latency_seconds": f"{latency:.4f}s"
        },
        "choices": choices
    }