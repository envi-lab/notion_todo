"""Constants for notion_todo."""
import json
from logging import Logger, getLogger
from pathlib import Path


def _normalize_words(values: list[str]) -> tuple[str, ...]:
    return tuple(value.strip().lower() for value in values if value and value.strip())


def _load_mapping() -> dict:
    mapping_path = Path(__file__).with_name("mapping.json")
    with mapping_path.open(encoding="utf-8") as handle:
        return json.load(handle)

LOGGER: Logger = getLogger(__package__)

NAME = "Notion ToDo"
DOMAIN = "notion_todo"
VERSION = "0.0.1"
ATTRIBUTION = "Data provided by https://api.notion.com/v1"
NOTION_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
CONF_DATABASE_ID = "database_id"
CONF_PROJECT_PROPERTY = "project_property"
CONF_PROJECT_FILTER = "project_filter"
TASK_DATE_PROPERTY = "notion%3A%2F%2Ftasks%2Fdue_date_property"
TASK_ASSIGNEE_PROPERTY = "notion%3A%2F%2Ftasks%2Fassign_property"
TASK_STATUS_PROPERTY = "notion%3A%2F%2Ftasks%2Fstatus_property"
TASK_DESCRIPTION_PROPERTY = "notion%3A%2F%2Ftasks%2Fai_summary_property"

MAPPING = _load_mapping()
PROPERTY_FALLBACK_NAMES = MAPPING.get("property_fallback_names", {})
DATE_FALLBACK_PROPERTY_NAMES = _normalize_words(PROPERTY_FALLBACK_NAMES.get("due_date", []))
DESCRIPTION_FALLBACK_PROPERTY_NAMES = _normalize_words(PROPERTY_FALLBACK_NAMES.get("description", []))
STATUS_MAPPING = MAPPING.get("status", {})
COMPLETED_STATUS_KEYWORDS = _normalize_words(STATUS_MAPPING.get("completed_keywords", []))
