"""
Transcription router for audio file uploads and processing.
"""
import os
import re
import time
import logging
import tempfile
from pathlib import Path
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException, status

from models import TranscriptionResponse
from config import settings
from services.gemini_service import GeminiService
from services.audio_service import AudioService
from services.date_extractor import DateExtractor

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
gemini_service = GeminiService()
audio_service = AudioService()
date_extractor = DateExtractor()


def extract_speakers(transcript: str) -> List[str]:
    """
    Extract unique speaker identifiers from the transcript.
    
    Args:
        transcript: The transcribed text
        
    Returns:
        List of unique speaker identifiers found
    """
    # Match patterns like [Speaker A], [Speaker B], [John], etc.
    pattern = r'\[([^\]]+)\](?:\s*\[\d{1,2}:\d{2}\])?:'
    matches = re.findall(pattern, transcript)
    
    # Extract unique speakers (excluding timestamps)
    speakers = set()
    for match in matches:
        # Skip if it looks like a timestamp
        if not re.match(r'^\d{1,2}:\d{2}$', match):
            speakers.add(match)
    
    return sorted(list(speakers))


@router.post(
    "/transcribe",
    response_model=TranscriptionResponse,
    summary="Transcribe Audio File",
    description="""
    Upload an audio file for verbatim transcription with speaker identification.
    
    Supported formats: MP3, WAV, M4A, OGG, WebM
    Maximum file size: 100 MB (configurable)
    Processing time: Varies based on audio length (up to 5 minutes)
    """,
    responses={
        200: {"description": "Successful transcription"},
        400: {"description": "Invalid file format or size"},
        408: {"description": "Processing timeout"},
        500: {"description": "Internal server error"}
    }
)
async def transcribe_audio(
    file: UploadFile = File(..., description="Audio file to transcribe")
) -> TranscriptionResponse:
    """
    Transcribe an uploaded audio file using Google Gemini.
    
    The transcription process:
    1. Validates file extension and size
    2. Saves file temporarily to /tmp/
    3. Uploads to Google GenAI Files API
    4. Calls Gemini with verbatim transcription prompt
    5. Extracts speaker identifiers
    6. Cleans up temporary files
    
    Returns a structured response with the transcript and metadata.
    """
    start_time = time.time()
    temp_path = None
    
    try:
        # Validate file
        filename = file.filename or "audio_file"
        logger.info(f"Received file for transcription: {filename}")
        
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in settings.allowed_audio_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file format. Allowed formats: {', '.join(settings.allowed_audio_extensions)}"
            )
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Check file size
        if file_size > settings.max_file_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size: {settings.max_file_size_mb} MB"
            )
        
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file uploaded"
            )
        
        logger.info(f"File size: {file_size / 1024 / 1024:.2f} MB")
        
        # Save to temporary file
        temp_path = await audio_service.save_temp_file(content, file_ext)
        logger.info(f"Saved to temporary file: {temp_path}")
        
        # Extract date from filename
        detected_date = date_extractor.extract_date(filename)
        if detected_date:
            logger.info(f"Detected date from filename: {detected_date}")
        
        # Transcribe using Gemini
        logger.info("Starting transcription with Gemini...")
        transcript = await gemini_service.transcribe_audio(temp_path)
        
        # Extract speakers from transcript
        speakers = extract_speakers(transcript)
        logger.info(f"Identified {len(speakers)} speakers: {speakers}")
        
        processing_time = time.time() - start_time
        logger.info(f"Transcription completed in {processing_time:.2f} seconds")
        
        return TranscriptionResponse(
            filename=filename,
            detected_date=detected_date,
            transcript=transcript,
            speakers_identified=speakers,
            processing_time_seconds=round(processing_time, 2)
        )
        
    except HTTPException:
        raise
    except TimeoutError:
        logger.error("Transcription timed out")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Transcription timed out. Please try with a shorter audio file."
        )
    except Exception as e:
        logger.error(f"Transcription error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                logger.info(f"Cleaned up temporary file: {temp_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp file: {e}")
