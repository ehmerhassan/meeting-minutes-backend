"""
Configuration management using pydantic-settings.
Handles all environment variables with validation and defaults.
"""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Uses pydantic-settings for automatic validation and type coercion.
    """
    
    # Required settings
    gemini_api_key: str = Field(
        ...,
        description="Google Gemini API key (required)",
        json_schema_extra={"env": "GEMINI_API_KEY"}
    )
    
    # Server settings
    port: int = Field(
        default=8000,
        description="Server port (default: 8000 for App Runner)",
        ge=1,
        le=65535
    )
    
    environment: str = Field(
        default="production",
        description="Environment name (development, staging, production)"
    )
    
    # File handling settings
    max_file_size_mb: int = Field(
        default=100,
        description="Maximum file size in megabytes",
        ge=1,
        le=500
    )
    
    request_timeout: int = Field(
        default=300,
        description="Request timeout in seconds",
        ge=30,
        le=600
    )
    
    allowed_audio_extensions: List[str] = Field(
        default=[".mp3", ".wav", ".m4a", ".ogg", ".webm"],
        description="Allowed audio file extensions"
    )
    
    # Gemini model settings
    gemini_model: str = Field(
        default="gemini-2.0-flash-exp",
        description="Gemini model to use for AI operations"
    )
    
    transcription_temperature: float = Field(
        default=0.1,
        description="Temperature for transcription (low for accuracy)",
        ge=0.0,
        le=1.0
    )
    
    summarization_temperature: float = Field(
        default=0.3,
        description="Temperature for summarization (slightly creative)",
        ge=0.0,
        le=1.0
    )
    
    max_output_tokens: int = Field(
        default=16384,
        description="Maximum output tokens for Gemini responses",
        ge=1000,
        le=65536
    )
    
    class Config:
        """Pydantic settings configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"
    
    @property
    def max_file_size_bytes(self) -> int:
        """Convert max file size from MB to bytes."""
        return self.max_file_size_mb * 1024 * 1024
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment.lower() == "production"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    Uses lru_cache to ensure settings are only loaded once.
    
    Returns:
        Settings: Application settings instance
    """
    return Settings()


# Expose settings instance for direct import
settings = get_settings()
