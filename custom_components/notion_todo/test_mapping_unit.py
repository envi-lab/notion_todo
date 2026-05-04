"""Unit tests for static mapping configuration."""

from custom_components.notion_todo.const import (
    COMPLETED_STATUS_KEYWORDS,
    DATE_FALLBACK_PROPERTY_NAMES,
    DESCRIPTION_FALLBACK_PROPERTY_NAMES,
)


def test_due_date_fallbacks_loaded_from_mapping() -> None:
    """Ensure due date fallback keywords are present."""
    assert "due" in DATE_FALLBACK_PROPERTY_NAMES
    assert "fällig" in DATE_FALLBACK_PROPERTY_NAMES


def test_description_fallbacks_loaded_from_mapping() -> None:
    """Ensure description fallback keywords are present."""
    assert "description" in DESCRIPTION_FALLBACK_PROPERTY_NAMES
    assert "summary" in DESCRIPTION_FALLBACK_PROPERTY_NAMES


def test_completed_keywords_loaded_from_mapping() -> None:
    """Ensure completion keywords are present."""
    assert "done" in COMPLETED_STATUS_KEYWORDS
    assert "erledigt" in COMPLETED_STATUS_KEYWORDS
