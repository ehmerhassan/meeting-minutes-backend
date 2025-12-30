"""
Date extraction service for parsing dates from filenames.
Supports multiple common date formats.
"""
import re
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DateExtractor:
    """
    Extract dates from filenames using various format patterns.
    
    Supports formats like:
    - 2023-10-27_Meeting.mp3 (ISO format)
    - Meeting_10-27-2023.mp3 (US format)
    - 2023.10.27-standup.wav (Dotted format)
    - October 27 2023 meeting.m4a (Written format)
    """
    
    # Month name mappings
    MONTHS = {
        'january': '01', 'jan': '01',
        'february': '02', 'feb': '02',
        'march': '03', 'mar': '03',
        'april': '04', 'apr': '04',
        'may': '05',
        'june': '06', 'jun': '06',
        'july': '07', 'jul': '07',
        'august': '08', 'aug': '08',
        'september': '09', 'sep': '09', 'sept': '09',
        'october': '10', 'oct': '10',
        'november': '11', 'nov': '11',
        'december': '12', 'dec': '12'
    }
    
    # Regex patterns for different date formats
    PATTERNS = [
        # ISO format: 2023-10-27 or 2023_10_27
        (r'(\d{4})[-_](\d{1,2})[-_](\d{1,2})', 'ymd'),
        
        # Dotted ISO: 2023.10.27
        (r'(\d{4})\.(\d{1,2})\.(\d{1,2})', 'ymd'),
        
        # US format: 10-27-2023 or 10_27_2023
        (r'(\d{1,2})[-_](\d{1,2})[-_](\d{4})', 'mdy'),
        
        # Dotted US: 10.27.2023
        (r'(\d{1,2})\.(\d{1,2})\.(\d{4})', 'mdy'),
        
        # Compact ISO: 20231027
        (r'(\d{4})(\d{2})(\d{2})', 'ymd_compact'),
        
        # Written month: October 27 2023 or October-27-2023
        (r'([a-zA-Z]+)\s*[-_]?\s*(\d{1,2})\s*[-_,]?\s*(\d{4})', 'written'),
        
        # Written month reversed: 27 October 2023
        (r'(\d{1,2})\s+([a-zA-Z]+)\s+(\d{4})', 'written_reversed'),
    ]
    
    def extract_date(self, filename: str) -> Optional[str]:
        """
        Extract date from a filename.
        
        Args:
            filename: The filename to parse
            
        Returns:
            ISO format date string (YYYY-MM-DD) or None if not found
        """
        if not filename:
            return None
        
        # Try each pattern
        for pattern, format_type in self.PATTERNS:
            match = re.search(pattern, filename, re.IGNORECASE)
            
            if match:
                try:
                    date = self._parse_match(match, format_type)
                    if date:
                        logger.debug(f"Extracted date '{date}' from '{filename}' using pattern '{format_type}'")
                        return date
                except (ValueError, IndexError) as e:
                    logger.debug(f"Pattern '{format_type}' matched but failed to parse: {e}")
                    continue
        
        logger.debug(f"No date found in filename: {filename}")
        return None
    
    def _parse_match(self, match: re.Match, format_type: str) -> Optional[str]:
        """
        Parse a regex match into an ISO date string.
        
        Args:
            match: Regex match object
            format_type: Type of date format matched
            
        Returns:
            ISO format date string or None
        """
        groups = match.groups()
        
        if format_type == 'ymd':
            year, month, day = groups
            return self._format_date(int(year), int(month), int(day))
        
        elif format_type == 'ymd_compact':
            year, month, day = groups
            return self._format_date(int(year), int(month), int(day))
        
        elif format_type == 'mdy':
            month, day, year = groups
            return self._format_date(int(year), int(month), int(day))
        
        elif format_type == 'written':
            month_name, day, year = groups
            month = self._month_to_number(month_name)
            if month:
                return self._format_date(int(year), int(month), int(day))
        
        elif format_type == 'written_reversed':
            day, month_name, year = groups
            month = self._month_to_number(month_name)
            if month:
                return self._format_date(int(year), int(month), int(day))
        
        return None
    
    def _month_to_number(self, month_name: str) -> Optional[str]:
        """
        Convert month name to two-digit number.
        
        Args:
            month_name: Month name (e.g., 'October', 'Oct')
            
        Returns:
            Two-digit month string or None
        """
        return self.MONTHS.get(month_name.lower().strip())
    
    def _format_date(self, year: int, month: int, day: int) -> Optional[str]:
        """
        Format date components into ISO string with validation.
        
        Args:
            year: Four-digit year
            month: Month number (1-12)
            day: Day of month (1-31)
            
        Returns:
            ISO format date string or None if invalid
        """
        try:
            # Validate the date is real
            date_obj = datetime(year, month, day)
            
            # Return ISO format
            return date_obj.strftime('%Y-%m-%d')
            
        except ValueError as e:
            logger.debug(f"Invalid date: {year}-{month}-{day}: {e}")
            return None
    
    def get_supported_formats(self) -> list:
        """
        Get list of supported date format examples.
        
        Returns:
            List of example filename formats
        """
        return [
            "2023-10-27_Meeting.mp3",
            "Meeting_10-27-2023.mp3",
            "2023.10.27-standup.wav",
            "October 27 2023 meeting.m4a",
            "27 October 2023 standup.mp3",
            "20231027_call.wav"
        ]
