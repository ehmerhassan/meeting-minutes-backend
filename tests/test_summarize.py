"""
Tests for the summarization endpoint.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import os

os.environ["GEMINI_API_KEY"] = "test-api-key-for-testing"

from main import app
from routers.summarize import extract_sections

client = TestClient(app)


class TestExtractSections:
    """Test section extraction from Markdown."""
    
    def test_extract_h2_sections(self):
        """Test extraction of H2 headings."""
        markdown = """
# Meeting Notes

## Executive Summary
Content here.

## Action Items
More content.

## Key Decisions
Even more content.
"""
        sections = extract_sections(markdown)
        assert "Executive Summary" in sections
        assert "Action Items" in sections
        assert "Key Decisions" in sections
    
    def test_extract_no_sections(self):
        """Test when no H2 sections present."""
        markdown = "# Just a title\nSome content."
        sections = extract_sections(markdown)
        assert len(sections) == 0
    
    def test_extract_mixed_headings(self):
        """Test with mixed heading levels."""
        markdown = """
# H1 Title
## H2 Section One
### H3 Subsection
## H2 Section Two
"""
        sections = extract_sections(markdown)
        assert "H2 Section One" in sections
        assert "H2 Section Two" in sections
        assert len(sections) == 2


class TestSummarizeEndpoint:
    """Test the /summarize endpoint."""
    
    def test_summarize_missing_text(self):
        """Test error when text is missing."""
        response = client.post(
            "/summarize",
            json={
                "date": "2024-01-15"
            }
        )
        assert response.status_code == 422
    
    def test_summarize_missing_date(self):
        """Test error when date is missing."""
        response = client.post(
            "/summarize",
            json={
                "text": "Some meeting transcript content here."
            }
        )
        assert response.status_code == 422
    
    def test_summarize_short_transcript(self):
        """Test error for transcript that is too short."""
        response = client.post(
            "/summarize",
            json={
                "text": "Too short",
                "date": "2024-01-15"
            }
        )
        assert response.status_code == 422
    
    def test_summarize_invalid_date_format(self):
        """Test error for invalid date format."""
        response = client.post(
            "/summarize",
            json={
                "text": "A sufficiently long transcript for testing the endpoint properly.",
                "date": "not-a-date"
            }
        )
        assert response.status_code == 422
    
    @patch('routers.summarize.gemini_service')
    def test_summarize_success(self, mock_gemini):
        """Test successful summarization with mocked service."""
        mock_markdown = """
# Meeting Notes: Weekly Standup

**Date:** 2024-01-15
**Attendees:** Alice, Bob

## Executive Summary
- Point one
- Point two

## Action Items
| Item | Owner | Due Date |
|------|-------|----------|
| Task 1 | Alice | 2024-01-20 |

## Key Decisions
- Decision one
"""
        mock_gemini.generate_summary = AsyncMock(return_value=mock_markdown)
        
        response = client.post(
            "/summarize",
            json={
                "text": "[Alice] [00:00]: Hello everyone. [Bob] [00:05]: Hi there!",
                "date": "2024-01-15",
                "title": "Weekly Standup"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "markdown" in data
        assert "sections" in data
        assert "processing_time_seconds" in data
        assert "Executive Summary" in data["sections"]
    
    @patch('routers.summarize.gemini_service')
    def test_summarize_without_title(self, mock_gemini):
        """Test summarization without optional title."""
        mock_gemini.generate_summary = AsyncMock(
            return_value="# Meeting Notes\n\n## Executive Summary\n- Point"
        )
        
        response = client.post(
            "/summarize",
            json={
                "text": "A sufficiently long transcript content for testing purposes here.",
                "date": "2024-01-15"
            }
        )
        
        assert response.status_code == 200


class TestDateValidation:
    """Test date format validation."""
    
    @pytest.mark.parametrize("date", [
        "2024-01-15",
        "01/15/2024",
        "01-15-2024"
    ])
    def test_valid_date_formats(self, date):
        """Test that valid date formats are accepted."""
        from models import TranscriptRequest
        
        request = TranscriptRequest(
            text="A sufficiently long transcript content for testing purposes here.",
            date=date
        )
        assert request.date == date
    
    def test_invalid_date_rejected(self):
        """Test that invalid dates are rejected."""
        from models import TranscriptRequest
        
        with pytest.raises(ValueError):
            TranscriptRequest(
                text="A sufficiently long transcript content for testing purposes here.",
                date="invalid-date-format"
            )
