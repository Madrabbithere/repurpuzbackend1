from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from youtube_transcript_api import YouTubeTranscriptApi
from pydantic import BaseModel
import os

app = FastAPI(title="YouTube Transcript Service")

# Get allowed origins from environment or use defaults
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS", 
    "https://repurpuzai.com,http://localhost:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

class TranscriptRequest(BaseModel):
    videoId: str

@app.post("/transcript", response_class=PlainTextResponse)
def get_transcript(req: TranscriptRequest):
    """Fetch transcript for a YouTube video. Returns plain text."""
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(req.videoId)
        
        # Join all text segments into one plain text block
        full_text = " ".join(snippet.text for snippet in transcript)
        
        return full_text
    
    except Exception as e:
        error_msg = str(e)
        print(f"[Transcript Error] Video: {req.videoId}, Error: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "youtube-transcript"}

@app.get("/")
def root():
    """Root endpoint with API info."""
    return {
        "service": "YouTube Transcript API",
        "endpoints": {
            "POST /transcript": "Fetch transcript as plain text",
            "GET /health": "Health check"
        }
    }
