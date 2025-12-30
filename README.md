# Meeting Notes Intelligence Suite - Backend API

FastAPI backend for transcribing, refining, and summarizing meeting audio using Google Gemini AI.

## Features

- 🎤 **Audio Transcription** - Upload audio files and get verbatim transcriptions with speaker identification
- ✏️ **Transcript Refinement** - Map speaker placeholders to real names with grammar corrections
- 📝 **Meeting Summaries** - Generate structured Markdown meeting summaries
- 🚀 **AWS App Runner Ready** - Optimized for managed Python runtime deployment

## Prerequisites

- Python 3.11+
- Google Gemini API key

## Local Development

### 1. Clone and Setup

```bash
git clone https://github.com/your-username/meeting-notes-backend.git
cd meeting-notes-backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
copy .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 3. Run Locally

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Verify

```bash
curl http://localhost:8000/
# Expected: {"status":"ok"}

# Open Swagger docs
start http://localhost:8000/docs
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check (returns `{"status": "ok"}`) |
| GET | `/health` | Detailed health status |
| POST | `/transcribe` | Upload audio file for transcription |
| POST | `/refine` | Refine transcript with speaker names |
| POST | `/summarize` | Generate meeting summary |

### POST /transcribe

Upload an audio file for transcription.

```bash
curl -X POST "http://localhost:8000/transcribe" \
  -F "file=@meeting.mp3"
```

**Response:**
```json
{
  "filename": "meeting.mp3",
  "detected_date": "2024-01-15",
  "transcript": "[Speaker A] [00:00]: Hello everyone...",
  "speakers_identified": ["Speaker A", "Speaker B"],
  "processing_time_seconds": 45.2
}
```

### POST /refine

Refine a transcript with speaker name mapping.

```bash
curl -X POST "http://localhost:8000/refine" \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "[Speaker A]: Hello...",
    "speaker_mapping": {"Speaker A": "Alice", "Speaker B": "Bob"},
    "feedback": "Speaker A is female"
  }'
```

**Response:**
```json
{
  "refined_transcript": "[Alice]: Hello...",
  "changes_made": ["Replaced 'Speaker A' with 'Alice' (5 occurrences)"],
  "processing_time_seconds": 3.5
}
```

### POST /summarize

Generate a structured meeting summary.

```bash
curl -X POST "http://localhost:8000/summarize" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Full transcript here...",
    "date": "2024-01-15",
    "title": "Weekly Standup"
  }'
```

**Response:**
```json
{
  "markdown": "# Meeting Notes: Weekly Standup\n\n...",
  "sections": ["Executive Summary", "Action Items", "Key Decisions"],
  "processing_time_seconds": 8.2
}
```

## AWS App Runner Deployment

### Quick Reference

| Setting | Value |
|---------|-------|
| **Runtime** | Python 3.11 |
| **Build command** | `pip3 install -r requirements.txt --target .` |
| **Start command** | `python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 300` |
| **Port** | 8000 |
| **Health check** | HTTP, Path: `/` |

### Step-by-Step Deployment

#### 1. Push to GitHub

```bash
git add .
git commit -m "Initial commit"
git push origin main
```

#### 2. Create App Runner Service

1. Go to [AWS App Runner Console](https://console.aws.amazon.com/apprunner)
2. Click **Create service**

#### 3. Source Configuration

| Setting | Value |
|---------|-------|
| Repository type | Source code repository |
| Provider | GitHub |
| Repository | your-username/meeting-notes-backend |
| Branch | main |
| Deployment trigger | Automatic |

#### 4. Build Configuration (⚠️ CRITICAL)

| Setting | Value |
|---------|-------|
| Configuration source | Configure all settings here |
| Runtime | **Python 3.11** |
| Build command | `pip3 install -r requirements.txt --target .` |
| Start command | `python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 300` |
| Port | 8000 |

> ⚠️ **Common Mistakes to Avoid:**
> - Use `pip3` not `pip`
> - Use `python3` not `python`
> - Include `--target .` in build command
> - Include `--host 0.0.0.0` in start command

#### 5. Service Configuration

| Setting | Value |
|---------|-------|
| CPU | 1 vCPU |
| Memory | 2 GB |

**Environment Variables:**

| Key | Value |
|-----|-------|
| `GEMINI_API_KEY` | your-actual-api-key |
| `PYTHONUNBUFFERED` | 1 |

#### 6. Health Check Configuration

| Setting | Value |
|---------|-------|
| Protocol | **HTTP** (not TCP!) |
| Path | `/` |
| Interval | 10 seconds |
| Timeout | 5 seconds |
| Healthy threshold | 1 |
| Unhealthy threshold | 5 |

#### 7. Deploy

Click **Create & deploy**. Expected time: 5-10 minutes.

### Troubleshooting

| Problem | Solution |
|---------|----------|
| `pip: command not found` | Use `pip3` instead of `pip` |
| `No module named uvicorn` | Add `--target .` to build command |
| `python: executable file not found` | Use `python3` instead of `python` |
| Health check failing | Change Protocol to HTTP (not TCP), verify Path is `/` |
| 504 Gateway Timeout | Add `--timeout-keep-alive 300` to start command |

## Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_main.py

# Run with coverage
pytest --cov=. --cov-report=html
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes | - | Google Gemini API key |
| `PORT` | No | 8000 | Server port |
| `ENVIRONMENT` | No | production | Environment name |
| `MAX_FILE_SIZE_MB` | No | 100 | Max upload file size |
| `REQUEST_TIMEOUT` | No | 300 | Request timeout in seconds |
| `GEMINI_MODEL` | No | gemini-2.0-flash-exp | Gemini model to use |
| `PYTHONUNBUFFERED` | No | - | Set to 1 for better logging |

## Project Structure

```
meeting-notes-backend/
├── main.py                 # FastAPI application entry point
├── config.py               # Configuration and environment variables
├── models.py               # Pydantic request/response models
├── routers/
│   ├── __init__.py
│   ├── transcribe.py       # /transcribe endpoint
│   ├── refine.py           # /refine endpoint
│   └── summarize.py        # /summarize endpoint
├── services/
│   ├── __init__.py
│   ├── gemini_service.py   # Google Gemini API integration
│   ├── audio_service.py    # Audio file handling
│   └── date_extractor.py   # Filename date extraction
├── prompts/
│   ├── __init__.py
│   └── templates.py        # AI prompt templates
├── tests/
│   ├── __init__.py
│   ├── test_main.py
│   ├── test_transcribe.py
│   ├── test_refine.py
│   └── test_summarize.py
├── requirements.txt        # Python dependencies
├── .env.example
├── .gitignore
└── README.md
```

## Critical Deployment Commands Reference

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                    APP RUNNER CONFIGURATION REFERENCE                      ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                           ║
║  BUILD COMMAND:                                                           ║
║  pip3 install -r requirements.txt --target .                              ║
║                                                                           ║
║  START COMMAND:                                                           ║
║  python3 -m uvicorn main:app --host 0.0.0.0 --port 8000                   ║
║          --timeout-keep-alive 300                                         ║
║                                                                           ║
║  PORT: 8000                                                               ║
║                                                                           ║
║  HEALTH CHECK: HTTP protocol, Path: /                                     ║
║                                                                           ║
╠═══════════════════════════════════════════════════════════════════════════╣
║  COMMON MISTAKES:                                                         ║
║  ✗ pip           → ✓ pip3                                                 ║
║  ✗ python        → ✓ python3                                              ║
║  ✗ pip3 install  → ✓ pip3 install --target .                              ║
║  ✗ TCP health    → ✓ HTTP health check                                    ║
║  ✗ Port 8080     → ✓ Port 8000                                            ║
║  ✗ Dockerfile    → ✓ No Dockerfile (managed runtime)                      ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

## License

MIT
