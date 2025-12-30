"""
Google Gemini AI service for transcription, refinement, and summarization.
Uses the google-generativeai library with retry logic and error handling.
"""
import os
import logging
import asyncio
from typing import Optional

import google.generativeai as genai
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from config import settings
from prompts.templates import (
    TRANSCRIPTION_PROMPT,
    REFINEMENT_PROMPT,
    SUMMARIZATION_PROMPT
)

logger = logging.getLogger(__name__)


class GeminiService:
    """
    Service for interacting with Google Gemini AI.
    
    Handles audio transcription, transcript refinement, and
    meeting summarization with proper error handling and retries.
    """
    
    def __init__(self):
        """Initialize the Gemini service with API key."""
        self.api_key = settings.gemini_api_key
        genai.configure(api_key=self.api_key)
        
        # Model configuration
        self.model_name = settings.gemini_model
        
        # Generation configs for different tasks
        self.transcription_config = genai.GenerationConfig(
            temperature=settings.transcription_temperature,
            max_output_tokens=settings.max_output_tokens
        )
        
        self.refinement_config = genai.GenerationConfig(
            temperature=settings.transcription_temperature,  # Low for accuracy
            max_output_tokens=settings.max_output_tokens
        )
        
        self.summarization_config = genai.GenerationConfig(
            temperature=settings.summarization_temperature,
            max_output_tokens=settings.max_output_tokens
        )
        
        logger.info(f"Gemini service initialized with model: {self.model_name}")
    
    def _get_model(self, config: genai.GenerationConfig) -> genai.GenerativeModel:
        """Get a configured Gemini model instance."""
        return genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=config
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((TimeoutError, ConnectionError))
    )
    async def transcribe_audio(self, file_path: str) -> str:
        """
        Transcribe an audio file using Gemini.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Verbatim transcript with speaker identification
            
        Raises:
            Exception: If transcription fails after retries
        """
        logger.info(f"Uploading audio file: {file_path}")
        
        try:
            # Upload file to Gemini
            audio_file = genai.upload_file(file_path)
            logger.info(f"File uploaded successfully: {audio_file.name}")
            
            # Wait for file to be processed
            while audio_file.state.name == "PROCESSING":
                logger.info("Waiting for file processing...")
                await asyncio.sleep(2)
                audio_file = genai.get_file(audio_file.name)
            
            if audio_file.state.name == "FAILED":
                raise Exception(f"File processing failed: {audio_file.state.name}")
            
            logger.info("File ready for transcription")
            
            # Generate transcription
            model = self._get_model(self.transcription_config)
            
            response = await asyncio.to_thread(
                model.generate_content,
                [audio_file, TRANSCRIPTION_PROMPT]
            )
            
            # Clean up uploaded file
            try:
                genai.delete_file(audio_file.name)
                logger.info("Uploaded file cleaned up")
            except Exception as e:
                logger.warning(f"Failed to delete uploaded file: {e}")
            
            transcript = response.text.strip()
            logger.info(f"Transcription complete: {len(transcript)} characters")
            
            return transcript
            
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((TimeoutError, ConnectionError))
    )
    async def refine_transcript(
        self,
        transcript: str,
        speaker_mapping: dict,
        feedback: Optional[str] = None
    ) -> str:
        """
        Refine a transcript by replacing speaker placeholders.
        
        Args:
            transcript: Original transcript text
            speaker_mapping: Dict mapping placeholders to real names
            feedback: Optional additional instructions
            
        Returns:
            Refined transcript with speaker names replaced
            
        Raises:
            Exception: If refinement fails after retries
        """
        logger.info("Starting transcript refinement")
        
        try:
            # Format speaker mapping for prompt
            mapping_str = "\n".join(
                f"  - {placeholder} → {name}"
                for placeholder, name in speaker_mapping.items()
            )
            
            # Build prompt
            prompt = REFINEMENT_PROMPT.format(
                speaker_mapping=mapping_str,
                feedback=feedback or "None provided",
                transcript=transcript
            )
            
            # Generate refined transcript
            model = self._get_model(self.refinement_config)
            
            response = await asyncio.to_thread(
                model.generate_content,
                prompt
            )
            
            refined = response.text.strip()
            logger.info(f"Refinement complete: {len(refined)} characters")
            
            return refined
            
        except Exception as e:
            logger.error(f"Refinement error: {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((TimeoutError, ConnectionError))
    )
    async def generate_summary(
        self,
        transcript: str,
        date: str,
        title: str
    ) -> str:
        """
        Generate a structured Markdown meeting summary.
        
        Args:
            transcript: Full transcript text
            date: Meeting date
            title: Meeting title
            
        Returns:
            Structured Markdown summary
            
        Raises:
            Exception: If summarization fails after retries
        """
        logger.info(f"Starting summarization for: {title}")
        
        try:
            # Build prompt
            prompt = SUMMARIZATION_PROMPT.format(
                date=date,
                title=title,
                transcript=transcript
            )
            
            # Generate summary
            model = self._get_model(self.summarization_config)
            
            response = await asyncio.to_thread(
                model.generate_content,
                prompt
            )
            
            summary = response.text.strip()
            logger.info(f"Summarization complete: {len(summary)} characters")
            
            return summary
            
        except Exception as e:
            logger.error(f"Summarization error: {str(e)}")
            raise
