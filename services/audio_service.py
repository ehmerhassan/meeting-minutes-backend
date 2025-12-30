"""
Audio file handling service.
Manages temporary file storage and cleanup.
"""
import os
import uuid
import logging
import tempfile
from pathlib import Path

import aiofiles

logger = logging.getLogger(__name__)


class AudioService:
    """
    Service for handling audio file operations.
    
    Manages temporary storage of uploaded audio files
    in the /tmp/ directory for processing.
    """
    
    def __init__(self, temp_dir: str = None):
        """
        Initialize the audio service.
        
        Args:
            temp_dir: Custom temporary directory (defaults to system temp)
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        
        # Ensure temp directory exists
        Path(self.temp_dir).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Audio service initialized with temp dir: {self.temp_dir}")
    
    async def save_temp_file(self, content: bytes, extension: str) -> str:
        """
        Save uploaded audio content to a temporary file.
        
        Args:
            content: Raw audio file bytes
            extension: File extension (e.g., '.mp3')
            
        Returns:
            Path to the temporary file
            
        Raises:
            IOError: If file cannot be saved
        """
        # Generate unique filename
        unique_id = uuid.uuid4().hex[:12]
        filename = f"audio_{unique_id}{extension}"
        file_path = os.path.join(self.temp_dir, filename)
        
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            
            logger.info(f"Saved temp file: {file_path} ({len(content)} bytes)")
            return file_path
            
        except IOError as e:
            logger.error(f"Failed to save temp file: {e}")
            raise
    
    async def delete_temp_file(self, file_path: str) -> bool:
        """
        Delete a temporary file.
        
        Args:
            file_path: Path to the file to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted temp file: {file_path}")
                return True
            else:
                logger.warning(f"Temp file not found: {file_path}")
                return False
                
        except OSError as e:
            logger.error(f"Failed to delete temp file: {e}")
            return False
    
    def get_file_size(self, file_path: str) -> int:
        """
        Get the size of a file in bytes.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File size in bytes, or -1 if file doesn't exist
        """
        try:
            return os.path.getsize(file_path)
        except OSError:
            return -1
    
    def validate_extension(self, filename: str, allowed: list) -> bool:
        """
        Check if a file has an allowed extension.
        
        Args:
            filename: Name of the file
            allowed: List of allowed extensions (e.g., ['.mp3', '.wav'])
            
        Returns:
            True if extension is allowed, False otherwise
        """
        extension = Path(filename).suffix.lower()
        return extension in allowed
    
    async def cleanup_old_files(self, max_age_seconds: int = 3600) -> int:
        """
        Clean up temporary audio files older than specified age.
        
        Args:
            max_age_seconds: Maximum age of files to keep (default: 1 hour)
            
        Returns:
            Number of files deleted
        """
        import time
        
        deleted_count = 0
        current_time = time.time()
        
        try:
            for filename in os.listdir(self.temp_dir):
                if filename.startswith("audio_"):
                    file_path = os.path.join(self.temp_dir, filename)
                    file_age = current_time - os.path.getmtime(file_path)
                    
                    if file_age > max_age_seconds:
                        if await self.delete_temp_file(file_path):
                            deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old temp files")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return deleted_count
