"""
Tests for the transcription endpoint.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
import os
import io

os.environ["GEMINI_API_KEY"] = "test-api-key-for-testing"

from main import app
from routers.transcribe import extract_speakers

client = TestClient(app)


class TestSpeakerExtraction:
    """Test speaker extraction from transcripts."""
    
    def test_extract_basic_speakers(self):
        """Test extraction of basic speaker format."""
        transcript = """
        [Speaker A] [00:00]: Hello everyone.
        [Speaker B] [00:05]: Hi there!
        [Speaker A] [00:10]: Let's get started.
        """
        speakers = extract_speakers(transcript)
        assert "Speaker A" in speakers
        assert "Speaker B" in speakers
        assert len(speakers) == 2
    
    def test_extract_named_speakers(self):
        """Test extraction of named speakers."""
        transcript = """
        [John] [00:00]: Hello everyone.
        [Sarah] [00:05]: Hi there!
        """
        speakers = extract_speakers(transcript)
        assert "John" in speakers
        assert "Sarah" in speakers
    
    def test_extract_no_speakers(self):
        """Test extraction when no speakers present."""
        transcript = "Just some plain text without speakers."
        speakers = extract_speakers(transcript)
        assert len(speakers) == 0
    
    def test_extract_ignores_timestamps(self):
        """Test that timestamps are not extracted as speakers."""
        transcript = "[Speaker A] [00:00]: Hello."
        speakers = extract_speakers(transcript)
        assert "00:00" not in speakers
        assert "Speaker A" in speakers


class TestTranscribeEndpoint:
    """Test the /transcribe endpoint."""
    
    def test_transcribe_missing_file(self):
        """Test error when no file is uploaded."""
        response = client.post("/transcribe")
        assert response.status_code == 422
    
    def test_transcribe_invalid_extension(self):
        """Test error for invalid file extension."""
        file_content = b"fake audio content"
        response = client.post(
            "/transcribe",
            files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
        )
        assert response.status_code == 400
        assert "Invalid file format" in response.json()["detail"]
    
    def test_transcribe_empty_file(self):
        """Test error for empty file."""
        response = client.post(
            "/transcribe",
            files={"file": ("test.mp3", io.BytesIO(b""), "audio/mpeg")}
        )
        assert response.status_code == 400
        assert "Empty file" in response.json()["detail"]
    
    @patch('routers.transcribe.gemini_service')
    @patch('routers.transcribe.audio_service')
    def test_transcribe_success(self, mock_audio, mock_gemini):
        """Test successful transcription with mocked services."""
        mock_audio.save_temp_file = AsyncMock(return_value="/tmp/test.mp3")
        mock_gemini.transcribe_audio = AsyncMock(
            return_value="[Speaker A] [00:00]: Hello world."
        )
        
        file_content = b"fake audio content for testing"
        response = client.post(
            "/transcribe",
            files={"file": ("2024-01-15_meeting.mp3", io.BytesIO(file_content), "audio/mpeg")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "transcript" in data
        assert "speakers_identified" in data
        assert data["filename"] == "2024-01-15_meeting.mp3"


class TestFileValidation:
    """Test file validation logic."""
    
    @pytest.mark.parametrize("extension", [".mp3", ".wav", ".m4a", ".ogg", ".webm"])
    def test_valid_extensions_accepted(self, extension):
        """Test that valid extensions are handled."""
        from config import settings
        assert extension in settings.allowed_audio_extensions
    
    def test_invalid_extensions_rejected(self):
        """Test that invalid extensions are rejected."""
        invalid_exts = [".txt", ".pdf", ".doc", ".exe"]
        from config import settings
        for ext in invalid_exts:
            assert ext not in settings.allowed_audio_extensions
