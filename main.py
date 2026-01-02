import logging
import sys
import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from youtube_transcript_api import YouTubeTranscriptApi
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
    
    try:
        logger.info(f"[Transcript] Creating YouTubeTranscriptApi instance...")
        ytt_api = YouTubeTranscriptApi()
        
        logger.info(f"[Transcript] Fetching transcript for: {req.videoId}")
        transcript = ytt_api.fetch(req.videoId)
        
        logger.info(f"[Transcript] Got {len(list(transcript))} segments, joining text...")
        
        # Need to re-fetch since we consumed the iterator
        transcript = ytt_api.fetch(req.videoId)
        full_text = " ".join(snippet.text for snippet in transcript)
        
        logger.info(f"[Transcript] Success! Returning {len(full_text)} chars")
        return full_text
    
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        logger.error(f"[Transcript Error] Type: {error_type}, Video: {req.videoId}, Error: {error_msg}")
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
