import logging
import sys
import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import GenericProxyConfig
from pydantic import BaseModel

# Configure logging to stdout for Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Log startup info
logger.info("=" * 50)
logger.info("Starting YouTube Transcript Service")
logger.info(f"Python version: {sys.version}")
logger.info(f"PORT env: {os.getenv('PORT', 'not set')}")
logger.info(f"ALLOWED_ORIGINS env: {os.getenv('ALLOWED_ORIGINS', 'not set')}")
logger.info("=" * 50)

# Proxy configuration for youtube-transcript-api
proxy_username = os.getenv("PROXY_USERNAME")
proxy_password = os.getenv("PROXY_PASSWORD")
proxy_host = os.getenv("PROXY_HOST", "geo.iproyal.com")
proxy_port = os.getenv("PROXY_PORT", "12321")

proxy_config = None
if proxy_username and proxy_password:
    proxy_url = f"http://{proxy_username}:{proxy_password}@{proxy_host}:{proxy_port}"
    proxy_config = GenericProxyConfig(
        http_url=proxy_url,
        https_url=proxy_url,
    )
    logger.info(f"Proxy configured: {proxy_host}:{proxy_port}")
else:
    logger.warning("No proxy configured - requests will use server IP")

app = FastAPI(title="YouTube Transcript Service")

# Get allowed origins from environment or use defaults
allowed_origins_str = os.getenv(
    "ALLOWED_ORIGINS", 
    "https://repurpuzai.com,http://localhost:3000,*"
)
allowed_origins = [o.strip() for o in allowed_origins_str.split(",")]
logger.info(f"CORS allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TranscriptRequest(BaseModel):
    videoId: str

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

@app.post("/transcript", response_class=PlainTextResponse)
def get_transcript(req: TranscriptRequest):
    """Fetch transcript for a YouTube video. Returns plain text."""
    logger.info(f"[Transcript] Received request for video: {req.videoId}")
    
    max_retries = 3
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"[Transcript] Attempt {attempt}/{max_retries} for video: {req.videoId}")
            ytt_api = YouTubeTranscriptApi(proxy_config=proxy_config)

            transcript = ytt_api.fetch(req.videoId)

            snippets = list(transcript)
            logger.info(f"[Transcript] Got {len(snippets)} segments, joining text...")

            full_text = " ".join(snippet.text for snippet in snippets)

            logger.info(f"[Transcript] Success on attempt {attempt}! Returning {len(full_text)} chars")
            return full_text

        except Exception as e:
            last_error = e
            error_type = type(e).__name__
            logger.warning(f"[Transcript] Attempt {attempt} failed ({error_type}): {e}")
            if attempt < max_retries:
                logger.info(f"[Transcript] Retrying with new proxy IP...")

    error_msg = str(last_error)
    error_type = type(last_error).__name__
    logger.error(f"[Transcript Error] All {max_retries} attempts failed for video: {req.videoId}, Last error: {error_type}: {error_msg}")
    raise HTTPException(status_code=500, detail=f"{error_type}: {error_msg}")

@app.get("/health")
def health():
    """Health check endpoint."""
    logger.info("[Health] Health check requested")
    return {"status": "ok", "service": "youtube-transcript"}

@app.get("/")
def root():
    """Root endpoint with API info."""
    logger.info("[Root] API info requested")
    return {
        "service": "YouTube Transcript API",
        "status": "running",
        "endpoints": {
            "POST /transcript": "Fetch transcript as plain text (body: {videoId: 'xxx'})",
            "GET /health": "Health check"
        }
    }

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Application startup complete!")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("👋 Application shutting down...")
