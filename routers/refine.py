"""
Refinement router for transcript speaker name mapping.
"""
import time
import logging
from typing import List

from fastapi import APIRouter, HTTPException, status

from models import RefinementRequest, RefinementResponse
from services.gemini_service import GeminiService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize service
gemini_service = GeminiService()


def detect_changes(original: str, refined: str, mapping: dict) -> List[str]:
    """
    Detect and describe changes made during refinement.
    
    Args:
        original: Original transcript
        refined: Refined transcript
        mapping: Speaker mapping used
        
    Returns:
        List of change descriptions
    """
    changes = []
    
    # Check for each speaker replacement
    for placeholder, real_name in mapping.items():
        if placeholder in original and real_name in refined:
            # Count occurrences
            original_count = original.count(f"[{placeholder}]")
            if original_count == 0:
                original_count = original.count(placeholder)
            
            if original_count > 0:
                changes.append(f"Replaced '{placeholder}' with '{real_name}' ({original_count} occurrences)")
    
    # Check if the transcript was changed
    if original.strip() == refined.strip():
        changes.append("No changes were necessary")
    elif not changes:
        changes.append("Speaker names updated and grammar adjusted")
    
    return changes


@router.post(
    "/refine",
    response_model=RefinementResponse,
    summary="Refine Transcript",
    description="""
    Refine a transcript by replacing speaker placeholders with real names.
    
    This endpoint ONLY:
    - Replaces speaker placeholders (e.g., "Speaker A" → "Alice")
    - Fixes pronouns to match speaker gender
    - Corrects verb agreements if needed
    
    It does NOT modify any other content in the transcript.
    """,
    responses={
        200: {"description": "Successful refinement"},
        400: {"description": "Invalid request data"},
        500: {"description": "Internal server error"}
    }
)
async def refine_transcript(request: RefinementRequest) -> RefinementResponse:
    """
    Refine a transcript with speaker name mapping.
    
    The refinement process:
    1. Validates the speaker mapping
    2. Calls Gemini with strict refinement prompt
    3. Detects and reports changes made
    
    The AI is instructed to ONLY change speaker names and fix
    resulting pronoun/gender agreements, preserving all other content.
    """
    start_time = time.time()
    
    try:
        logger.info(f"Refining transcript with {len(request.speaker_mapping)} speaker mappings")
        logger.info(f"Speaker mapping: {request.speaker_mapping}")
        
        if request.feedback:
            logger.info(f"Additional feedback provided: {request.feedback}")
        
        # Validate speaker mapping
        if not request.speaker_mapping:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Speaker mapping cannot be empty"
            )
        
        # Check if any placeholder exists in the transcript
        found_any = False
        for placeholder in request.speaker_mapping.keys():
            if placeholder in request.transcript:
                found_any = True
                break
        
        if not found_any:
            logger.warning("No speaker placeholders found in transcript")
            # Still proceed - the AI might find variations
        
        # Refine using Gemini
        logger.info("Starting refinement with Gemini...")
        refined_transcript = await gemini_service.refine_transcript(
            transcript=request.transcript,
            speaker_mapping=request.speaker_mapping,
            feedback=request.feedback
        )
        
        # Detect changes made
        changes = detect_changes(
            original=request.transcript,
            refined=refined_transcript,
            mapping=request.speaker_mapping
        )
        
        processing_time = time.time() - start_time
        logger.info(f"Refinement completed in {processing_time:.2f} seconds")
        logger.info(f"Changes detected: {changes}")
        
        return RefinementResponse(
            refined_transcript=refined_transcript,
            changes_made=changes,
            processing_time_seconds=round(processing_time, 2)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Refinement error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Refinement failed: {str(e)}"
        )
