"""
Tests for the refinement endpoint.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import os

os.environ["GEMINI_API_KEY"] = "test-api-key-for-testing"

from main import app
from routers.refine import detect_changes

client = TestClient(app)


class TestDetectChanges:
    """Test change detection logic."""
    
    def test_detect_speaker_replacement(self):
        """Test detection of speaker name replacements."""
        original = "[Speaker A]: Hello [Speaker B]."
        refined = "[Alice]: Hello [Bob]."
        mapping = {"Speaker A": "Alice", "Speaker B": "Bob"}
        
        changes = detect_changes(original, refined, mapping)
        assert any("Alice" in c for c in changes)
        assert any("Bob" in c for c in changes)
    
    def test_detect_no_changes(self):
        """Test when no changes are made."""
        text = "Some transcript text."
        changes = detect_changes(text, text, {"Speaker A": "Alice"})
        assert any("No changes" in c for c in changes)
    
    def test_detect_general_changes(self):
        """Test general change detection."""
        original = "Old text"
        refined = "New text"
        changes = detect_changes(original, refined, {})
        assert len(changes) >= 1


class TestRefineEndpoint:
    """Test the /refine endpoint."""
    
    def test_refine_missing_transcript(self):
        """Test error when transcript is missing."""
        response = client.post(
            "/refine",
            json={
                "speaker_mapping": {"Speaker A": "Alice"}
            }
        )
        assert response.status_code == 422
    
    def test_refine_missing_mapping(self):
        """Test error when speaker_mapping is missing."""
        response = client.post(
            "/refine",
            json={
                "transcript": "[Speaker A]: Hello world."
            }
        )
        assert response.status_code == 422
    
    def test_refine_empty_mapping(self):
        """Test error when speaker_mapping is empty."""
        response = client.post(
            "/refine",
            json={
                "transcript": "[Speaker A]: Hello world.",
                "speaker_mapping": {}
            }
        )
        assert response.status_code == 422
    
    def test_refine_short_transcript(self):
        """Test error for transcript that is too short."""
        response = client.post(
            "/refine",
            json={
                "transcript": "Hi",
                "speaker_mapping": {"Speaker A": "Alice"}
            }
        )
        assert response.status_code == 422
    
    @patch('routers.refine.gemini_service')
    def test_refine_success(self, mock_gemini):
        """Test successful refinement with mocked service."""
        mock_gemini.refine_transcript = AsyncMock(
            return_value="[Alice] [00:00]: Hello world."
        )
        
        response = client.post(
            "/refine",
            json={
                "transcript": "[Speaker A] [00:00]: Hello world.",
                "speaker_mapping": {"Speaker A": "Alice"},
                "feedback": "Speaker A is female"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "refined_transcript" in data
        assert "changes_made" in data
        assert "processing_time_seconds" in data
    
    @patch('routers.refine.gemini_service')
    def test_refine_without_feedback(self, mock_gemini):
        """Test refinement without optional feedback."""
        mock_gemini.refine_transcript = AsyncMock(
            return_value="[Bob] [00:00]: Hello there."
        )
        
        response = client.post(
            "/refine",
            json={
                "transcript": "[Speaker B] [00:00]: Hello there.",
                "speaker_mapping": {"Speaker B": "Bob"}
            }
        )
        
        assert response.status_code == 200


class TestSpeakerMappingValidation:
    """Test speaker mapping validation."""
    
    def test_valid_mapping(self):
        """Test that valid mappings are accepted."""
        from models import RefinementRequest
        
        request = RefinementRequest(
            transcript="[Speaker A]: Hello world testing.",
            speaker_mapping={"Speaker A": "Alice", "Speaker B": "Bob"}
        )
        
        assert len(request.speaker_mapping) == 2
    
    def test_empty_key_rejected(self):
        """Test that empty keys are rejected."""
        from models import RefinementRequest
        
        with pytest.raises(ValueError):
            RefinementRequest(
                transcript="[Speaker A]: Hello world testing.",
                speaker_mapping={"": "Alice"}
            )
    
    def test_empty_value_rejected(self):
        """Test that empty values are rejected."""
        from models import RefinementRequest
        
        with pytest.raises(ValueError):
            RefinementRequest(
                transcript="[Speaker A]: Hello world testing.",
                speaker_mapping={"Speaker A": ""}
            )
