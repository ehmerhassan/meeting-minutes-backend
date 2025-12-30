"""
Summarization router for generating structured meeting summaries.
"""
import re
import time
import logging
from typing import List

from fastapi import APIRouter, HTTPException, status

from models import TranscriptRequest, SummaryResponse
from services.gemini_service import GeminiService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize service
gemini_service = GeminiService()


def extract_sections(markdown: str) -> List[str]:
    """
    Extract section headings from the generated Markdown.
    
    Args:
        markdown: The Markdown content
        
    Returns:
        List of section heading names
    """
    # Match Markdown headings (## Heading)
    pattern = r'^##\s+(.+)$'
    matches = re.findall(pattern, markdown, re.MULTILINE)
    
    return matches


@router.post(
    "/summarize",
    response_model=SummaryResponse,
    summary="Generate Meeting Summary",
    description="""
    Generate a structured Markdown summary from a meeting transcript.
    
    The summary includes:
    - Meeting metadata header
    - Executive Summary (3-5 bullet points)
    - Action Items (with assignees if identifiable)
    - Key Decisions
    - Discussion Topics
    - Full transcript section
    """,
    responses={
        200: {"description": "Successful summarization"},
        400: {"description": "Invalid request data"},
        500: {"description": "Internal server error"}
    }
)
async def summarize_transcript(request: TranscriptRequest) -> SummaryResponse:
    """
    Generate a structured Markdown meeting summary.
    
    The summarization process:
    1. Validates the transcript content
    2. Calls Gemini with summarization prompt
    3. Extracts section headings for metadata
    
    Returns a complete Markdown document suitable for
    documentation or sharing.
    """
    start_time = time.time()
    
    try:
        title = request.title or "Meeting"
        logger.info(f"Summarizing transcript for: {title} on {request.date}")
        logger.info(f"Transcript length: {len(request.text)} characters")
        
        # Validate transcript has sufficient content
        if len(request.text.strip()) < 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transcript too short for meaningful summary (minimum 50 characters)"
            )
        
        # Generate summary using Gemini
        logger.info("Starting summarization with Gemini...")
        markdown = await gemini_service.generate_summary(
            transcript=request.text,
            date=request.date,
            title=title
        )
        
        # Extract sections for metadata
        sections = extract_sections(markdown)
        logger.info(f"Generated summary with {len(sections)} sections: {sections}")
        
        processing_time = time.time() - start_time
        logger.info(f"Summarization completed in {processing_time:.2f} seconds")
        
        return SummaryResponse(
            markdown=markdown,
            sections=sections,
            processing_time_seconds=round(processing_time, 2)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Summarization error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summarization failed: {str(e)}"
        )
