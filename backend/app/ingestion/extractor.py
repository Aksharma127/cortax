import logging
import re
import unicodedata
from typing import Optional

logger = logging.getLogger(__name__)


class TextCleaner:
    """Text normalization and cleaning utilities."""

    @staticmethod
    def normalize_unicode(text: str) -> str:
        """Normalize Unicode to NFC form."""
        return unicodedata.normalize("NFC", text)

    @staticmethod
    def remove_control_characters(text: str) -> str:
        """Remove invisible control characters that break processing."""
        # Remove control characters except newline, tab
        text = "".join(
            char for char in text 
            if unicodedata.category(char)[0] != "C" or char in "\n\t"
        )
        return text

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Fix common whitespace issues from PDF extraction."""
        # Fix line breaks inside words
        text = re.sub(r'-\s*\n\s*', '', text)  # Remove hyphens at line breaks
        
        # Replace multiple spaces with single space
        text = re.sub(r' {2,}', ' ', text)
        
        # Replace multiple newlines with double newline (paragraph break)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text

    @staticmethod
    def remove_urls(text: str) -> bool:
        """Remove URLs (optional - can preserve if needed for context)."""
        return re.sub(
            r'https?://\S+|www\.\S+',
            '',
            text
        )

    @staticmethod
    def remove_emails(text: str) -> str:
        """Remove email addresses (optional)."""
        return re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)

    @staticmethod
    def remove_page_numbers(text: str) -> str:
        """
        Remove common page number patterns.
        
        Patterns:
        - "Page 5", "P. 5"
        - "5/10" (page 5 of 10)
        - Standalone numbers at line start/end
        """
        # Remove "Page X" patterns
        text = re.sub(r'\bPage\s*\d+\b', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\bP\.\s*\d+\b', '', text)
        
        # Remove "X/Y" page patterns
        text = re.sub(r'\b\d+/\d+\b', '', text)
        
        return text

    @staticmethod
    def remove_repeated_lines(text: str) -> str:
        """
        Remove repeated lines (common in PDFs with headers/footers).
        
        Example: Document header repeated on every page.
        """
        lines = text.split('\n')
        unique_lines = []
        prev_line = None

        for line in lines:
            stripped = line.strip()
            # Only add if not empty and different from previous
            if stripped and stripped != prev_line:
                unique_lines.append(line)
                prev_line = stripped

        return '\n'.join(unique_lines)

    @staticmethod
    def clean(
        text: str,
        remove_urls_flag: bool = False,
        remove_emails_flag: bool = False,
        remove_page_numbers_flag: bool = True,
        remove_repeated_flag: bool = True
    ) -> str:
        """
        Execute full cleaning pipeline.
        
        Order matters! Do these steps in sequence:
        1. Unicode normalization (essential)
        2. Remove control characters (essential)
        3. Normalize whitespace (essential)
        4. Remove page numbers (often desirable)
        5. Remove repeated lines (often desirable)
        6. Optional: URLs, emails
        """
        try:
            logger.debug(f"Cleaning text, input length: {len(text)}")

            # Essential cleaning
            text = TextCleaner.normalize_unicode(text)
            text = TextCleaner.remove_control_characters(text)
            text = TextCleaner.normalize_whitespace(text)

            # Optional cleaning
            if remove_page_numbers_flag:
                text = TextCleaner.remove_page_numbers(text)

            if remove_repeated_flag:
                text = TextCleaner.remove_repeated_lines(text)

            if remove_urls_flag:
                text = TextCleaner.remove_urls(text)

            if remove_emails_flag:
                text = TextCleaner.remove_emails(text)

            logger.debug(f"Cleaning complete, output length: {len(text)}")
            return text

        except Exception as e:
            logger.error(f"Text cleaning failed: {e}")
            raise


class TextExtractor:
    """
    High-level text extraction with cleaning.
    
    Combines document loading and cleaning into one interface.
    """

    @staticmethod
    def extract_and_clean(
        text: str,
        clean_options: Optional[dict] = None
    ) -> str:
        """
        Extract text from document and apply cleaning.
        
        Args:
            text: Raw text from document parser
            clean_options: Dict with cleaning flags
        """
        if clean_options is None:
            clean_options = {}

        cleaned_text = TextCleaner.clean(text, **clean_options)
        
        # Final validation: ensure we have something
        if not cleaned_text or len(cleaned_text) < 10:
            logger.warning("Extracted text is too short")
            
        return cleaned_text
