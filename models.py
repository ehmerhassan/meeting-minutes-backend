"""
Pydantic models for request/response validation.
Defines all data structures used in the API.
"""
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Request Models
# =============================================================================

class RefinementRequest(BaseModel):
    """Request model for transcript refinement."""
    
    transcript: str = Field(
        ...,
        min_length=10,
        description="The original transcript to refine"
    )
    
    speaker_mapping: Dict[str, str] = Field(
        ...,
        min_length=1,
        description="Mapping of speaker placeholders to real names (e.g., {'Speaker A': 'Alice'})"
    )
    
    feedback: Optional[str] = Field(
        default=None,
        description="Additional feedback for refinement (e.g., 'Speaker A is female')"
    )
    
    @field_validator("speaker_mapping")
    @classmethod
    def validate_speaker_mapping(cls, v: Dict[str, str]) -> Dict[str, str]:
        """Validate that speaker mapping is not empty and has valid entries."""
        if not v:
            raise ValueError("speaker_mapping cannot be empty")
        
        for key, value in v.items():
            if not key.strip() or not value.strip():
                raise ValueError("Speaker mapping keys and values cannot be empty")
        
        return v


class TranscriptRequest(BaseModel):
    """Request model for meeting summarization."""
    
    text: str = Field(
        ...,
        min_length=50,
        description="The full transcript text to summarize"
    )
    
    date: str = Field(
        ...,
        description="Meeting date in ISO format (YYYY-MM-DD)"
    )
    
    title: Optional[str] = Field(
        default="Meeting",
        description="Meeting title (optional)"
    )
    
    @field_validator("date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate date format is ISO-like."""
        import re
        # Accept various date formats
        patterns = [
            r"^\d{4}-\d{2}-\d{2}$",  # YYYY-MM-DD
            r"^\d{2}/\d{2}/\d{4}$",  # MM/DD/YYYY
            r"^\d{2}-\d{2}-\d{4}$",  # MM-DD-YYYY
        ]
        
        if not any(re.match(pattern, v) for pattern in patterns):
            raise ValueError("Date must be in a valid format (e.g., YYYY-MM-DD)")
        
        return v


# =============================================================================
# Response Models
# =============================================================================

class TranscriptionResponse(BaseModel):
    """Response model for audio transcription."""
    
    filename: str = Field(
        ...,
        description="Original filename of the uploaded audio"
    )
    
    detected_date: Optional[str] = Field(
        default=None,
        description="Date extracted from filename (if found)"
    )
    
    transcript: str = Field(
        ...,
        description="The verbatim transcript of the audio"
    )
    
    speakers_identified: List[str] = Field(
        default=[],
        description="List of unique speaker identifiers found in the transcript"
    )
    
    processing_time_seconds: float = Field(
        ...,
        ge=0,
        description="Time taken to process the audio in seconds"
    )


class RefinementResponse(BaseModel):
    """Response model for transcript refinement."""
    
    refined_transcript: str = Field(
        ...,
        description="The refined transcript with speaker names replaced"
    )
    
    changes_made: List[str] = Field(
        default=[],
        description="List of changes made during refinement"
    )
    
    processing_time_seconds: float = Field(
        ...,
        ge=0,
        description="Time taken to refine the transcript in seconds"
    )


class SummaryResponse(BaseModel):
    """Response model for meeting summarization."""
    
    markdown: str = Field(
        ...,
        description="The complete Markdown-formatted meeting summary"
    )
    
    sections: List[str] = Field(
        default=[],
        description="List of section headings in the summary"
    )
    
    processing_time_seconds: float = Field(
        ...,
        ge=0,
        description="Time taken to generate the summary in seconds"
    )


class HealthResponse(BaseModel):
    """Response model for detailed health check."""
    
    status: str = Field(
        ...,
        description="Service health status"
    )
    
    service: str = Field(
        ...,
        description="Service name"
    )
    
    version: str = Field(
        ...,
        description="API version"
    )
    
    timestamp: str = Field(
        ...,
        description="Current server timestamp in ISO format"
    )
    
    environment: Optional[str] = Field(
        default=None,
        description="Current environment (development, staging, production)"
    )
    
    gemini_configured: Optional[bool] = Field(
        default=None,
        description="Whether Gemini API is configured"
    )


class ErrorResponse(BaseModel):
    """Standard error response model."""
    
    error: bool = Field(
        default=True,
        description="Indicates this is an error response"
    )
    
    status_code: int = Field(
        ...,
        description="HTTP status code"
    )
    
    detail: str = Field(
        ...,
        description="Error message"
    )
    
    path: Optional[str] = Field(
        default=None,
        description="Request path that caused the error"
    )
