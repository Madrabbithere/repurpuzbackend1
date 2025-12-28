# YouTube Transcript Service

A FastAPI microservice that fetches YouTube video transcripts using the [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) Python library.

## Features

- **Plain text output** - Returns transcript as raw text, no JSON parsing needed
- **Fast and lightweight** - Built with FastAPI and uvicorn
- **CORS enabled** - Ready for cross-origin requests from your frontend

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/transcript` | POST | Fetch transcript (body: `{"videoId": "xxx"}`) |
| `/health` | GET | Health check |
| `/` | GET | API info |

## Local Development

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn main:app --reload --port 8000
```

## Deploy to Railway

1. Connect this repo to Railway
2. Railway auto-detects Python and uses `Procfile`
3. Set environment variable `ALLOWED_ORIGINS` if needed

## Usage

```bash
curl -X POST https://your-railway-url/transcript \
  -H "Content-Type: application/json" \
  -d '{"videoId": "dQw4w9WgXcQ"}'
```

Returns plain text transcript:
```
[♪♪♪] ♪ We're no strangers to love ♪ ♪ You know the rules and so do I ♪ ...
```
