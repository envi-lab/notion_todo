"""Notion API Client."""
from __future__ import annotations

import asyncio
import socket
import copy
import aiohttp
import async_timeout
from datetime import datetime

from .const import NOTION_URL, NOTION_VERSION, TASK_STATUS_PROPERTY, TASK_DATE_PROPERTY, TASK_DESCRIPTION_PROPERTY
from .notion_property_helper import NotionPropertyHelper as propHelper


class NotionApiClientError(Exception):
    """Exception to indicate a general API error."""


class NotionApiClientCommunicationError(
    NotionApiClientError
):
    """Exception to indicate a communication error."""


class NotionApiClientAuthenticationError(
    NotionApiClientError
):
    """Exception to indicate an authentication error."""


class NotionApiClient:
    """Notion API Client."""

    _headers = {
        'Authorization': 'Bearer <TOKEN>',
        'Content-Type': 'application/json',
        'Notion-Version': NOTION_VERSION
        }

    def __init__(
        self,
        token: str,
        database_id: str,
        session: aiohttp.ClientSession,
        project_property: str | None = None,
        project_filter: str | None = None,
    ) -> None:
        """Notion API Client.

        Args:
            token (str): Notion token with access to ToDo database
            database_id (str): id of the ToDo database
            session (aiohttp.ClientSession): the session

        """
        self._token = token
        self._session = session
        self._headers['Authorization'] = f'Bearer {token}'
        self._database_id = database_id
        self._project_property = project_property.strip() if project_property else None
        self._project_filter = project_filter.strip().lower() if project_filter else None
        self._related_page_title_cache: dict[str, str] = {}
        self._task_template = None
        self._status_cache_loaded = False
        self._active_status_ids = set()
        self._completed_status_ids = set()
        self._default_active_status_id = None
        self._default_completed_status_id = None

    @staticmethod
    def _name_looks_completed(value: str | None) -> bool:
        if not value:
            return False
        normalized = value.strip().lower()
        keywords = [
            'done',
            'complete',
            'completed',
            'archive',
            'archived',
            'erledigt',
            'abgeschlossen',
            'fertig'
        ]
        return any(keyword in normalized for keyword in keywords)

    def _cache_status_options(self, database: dict) -> None:
        if self._status_cache_loaded:
            return

        properties = database.get('properties', {})
        status_property = None
        for prop in properties.values():
            if prop.get('type') != 'status':
                continue
            if prop.get('id') == TASK_STATUS_PROPERTY:
                status_property = prop
                break
            if status_property is None:
                status_property = prop

        if not status_property:
            self._status_cache_loaded = True
            return

        status_meta = status_property.get('status', {})
        options = status_meta.get('options', [])
        groups = status_meta.get('groups', [])
        option_ids = {option.get('id') for option in options if option.get('id')}

        for group in groups:
            group_name = group.get('name')
            ids = set(group.get('option_ids') or [])
            if self._name_looks_completed(group_name):
                self._completed_status_ids.update(ids)
            else:
                self._active_status_ids.update(ids)

        for option in options:
            option_id = option.get('id')
            option_name = option.get('name')
            if not option_id:
                continue

            if option_id in ('done', 'archived') or self._name_looks_completed(option_name):
                self._completed_status_ids.add(option_id)

        self._active_status_ids = self._active_status_ids.intersection(option_ids)
        self._completed_status_ids = self._completed_status_ids.intersection(option_ids)

        if not self._active_status_ids:
            self._active_status_ids = option_ids - self._completed_status_ids

        if self._active_status_ids:
            self._default_active_status_id = next(iter(self._active_status_ids))
        if self._completed_status_ids:
            self._default_completed_status_id = next(iter(self._completed_status_ids))

        self._status_cache_loaded = True

    async def resolve_status_id(self, is_completed: bool, current_status_id: str | None = None) -> str:
        """Resolve a valid status id for the target completion state."""
        if not self._status_cache_loaded:
            database = await self._get_database()
            self._cache_status_options(database)

        if is_completed:
            if current_status_id and current_status_id in self._completed_status_ids:
                return current_status_id
            if self._default_completed_status_id:
                return self._default_completed_status_id
            if current_status_id:
                return current_status_id
            return 'done'

        if current_status_id and current_status_id in self._active_status_ids:
            return current_status_id
        if self._default_active_status_id:
            return self._default_active_status_id
        if current_status_id:
            return current_status_id
        return 'not-started'

    async def async_get_data(self) -> any:
        """Get data from the API."""
        results = []
        start_cursor = None
        while True:
            body = {}
            if start_cursor:
                body['start_cursor'] = start_cursor
            page = await self._api_wrapper(
                method="post",
                url=f"{NOTION_URL}/databases/{self._database_id}/query",
                headers=self._headers,
                data=body if body else None
            )
            results.extend(page.get('results', []))
            if not page.get('has_more'):
                break
            start_cursor = page.get('next_cursor')

        if self._project_filter:
            results = await self._filter_results_by_project(results)

        return {'results': results}

    async def _filter_results_by_project(self, tasks: list[dict]) -> list[dict]:
        """Filter tasks by related project title match."""
        filtered_tasks = []
        for task in tasks:
            properties = task.get('properties', {})
            relation_key = self._get_relation_property_key(properties)
            if not relation_key:
                continue

            relation_items = properties.get(relation_key, {}).get('relation') or []
            relation_ids = [item.get('id') for item in relation_items if item.get('id')]
            if not relation_ids:
                continue

            related_titles = await self._get_related_page_titles(relation_ids)
            if any(self._project_filter in title.lower() for title in related_titles if title):
                filtered_tasks.append(task)

        return filtered_tasks

    def _get_relation_property_key(self, properties: dict) -> str | None:
        """Get relation property key for project filtering."""
        if self._project_property:
            project_property_lower = self._project_property.lower()
            for name, prop in properties.items():
                if prop.get('type') != 'relation':
                    continue
                if name.strip().lower() == project_property_lower or prop.get('id') == self._project_property:
                    return name

        for name, prop in properties.items():
            if prop.get('type') == 'relation':
                return name

        return None

    async def _get_related_page_titles(self, page_ids: list[str]) -> list[str]:
        """Resolve related Notion page ids to page titles."""
        missing_ids = [page_id for page_id in page_ids if page_id not in self._related_page_title_cache]
        if missing_ids:
            responses = await asyncio.gather(
                *[self._api_wrapper(
                    method="get",
                    url=f"{NOTION_URL}/pages/{page_id}",
                    headers=self._headers,
                ) for page_id in missing_ids],
                return_exceptions=True,
            )
            for page_id, response in zip(missing_ids, responses):
                if isinstance(response, Exception):
                    self._related_page_title_cache[page_id] = ""
                    continue
                self._related_page_title_cache[page_id] = self._extract_page_title(response)

        return [self._related_page_title_cache.get(page_id, "") for page_id in page_ids]

    @staticmethod
    def _extract_page_title(page: dict) -> str:
        """Extract human-readable title from a Notion page response."""
        properties = page.get('properties', {})
        for prop in properties.values():
            if prop.get('type') != 'title':
                continue
            title_parts = prop.get('title') or []
            return ''.join(part.get('plain_text', '') for part in title_parts)
        return ''

    async def update_task(
        self,
        task_id: str,
        title: str,
        status: str,
        due: datetime,
        description: str
    ) -> any:
        """Update task in Notion.

        Args:
            task_id (str): id of the task
            title: (str): Title of the task
            status (str): Status of the task
            due (datetime): Due date of the task
            description (str): Description of the task

        """
        task_data = await self._get_task_template()
        update_properties = {}

        title_key = propHelper.get_property_key_by_id("title", task_data)
        if title_key and title is not None:
            update_properties[title_key] = {
                "title": [{"type": "text", "text": {"content": title}}]
            }

        status_key = propHelper.get_property_key_by_id(TASK_STATUS_PROPERTY, task_data)
        if status_key and status:
            update_properties[status_key] = {"status": {"id": status}}

        date_key = propHelper.get_property_key_by_id(TASK_DATE_PROPERTY, task_data)
        if date_key:
            if due:
                start_str = due.isoformat() if hasattr(due, "isoformat") else str(due)
                update_properties[date_key] = {"date": {"start": start_str}}
            else:
                update_properties[date_key] = {"date": None}

        description_key = propHelper.get_property_key_by_id(TASK_DESCRIPTION_PROPERTY, task_data)
        if description_key:
            if description:
                update_properties[description_key] = {
                    "rich_text": [{"type": "text", "text": {"content": description}}]
                }
            else:
                update_properties[description_key] = {"rich_text": []}

        return await self._api_wrapper(
            method="patch",
            url=f"{NOTION_URL}/pages/{task_id}",
            headers=self._headers,
            data={"properties": update_properties}
        )

    async def create_task(self, title: str, status: str) -> any:
        """Create a new task in Notion.

        Args:
            title (str): Title of the task
            status (str): Status of the task

        """
        task_template = await self._get_task_template()
        task_data = {"parent": task_template["parent"], "properties": {}}

        title_key = propHelper.get_property_key_by_id("title", task_template)
        if title_key:
            task_data["properties"][title_key] = {
                "title": [{"type": "text", "text": {"content": title}}]
            }

        status_key = propHelper.get_property_key_by_id(TASK_STATUS_PROPERTY, task_template)
        if status_key and status:
            task_data["properties"][status_key] = {"status": {"id": status}}

        return await self._api_wrapper(
            method="post",
            url=f"{NOTION_URL}/pages",
            headers=self._headers,
            data=task_data)

    async def delete_task(self,
                          task_id: str):
        """Delete a task in Notion.

        Args:
            task_id (str): id of the task

        Returns:
            _type_: _description_

        """
        return await self._api_wrapper(
            method="delete",
            url=f"{NOTION_URL}/blocks/{task_id}",
            headers=self._headers)

    async def _get_database(self):
        return await self._api_wrapper(
            method="get",
            url=f"{NOTION_URL}/databases/{self._database_id}",
            headers=self._headers
        )

    async def _get_task_template(self):
        if not self._task_template:
            database = await self._get_database()
            self._cache_status_options(database)
            properties = database['properties']
            selected_properties = {}
            for property_id in ("title", TASK_STATUS_PROPERTY, TASK_DATE_PROPERTY, TASK_DESCRIPTION_PROPERTY):
                key = propHelper.get_property_key_by_id(property_id, database)
                if key and key in properties:
                    selected_properties[key] = properties[key]
            self._task_template = {
                'parent': {'database_id': self._database_id},
                'properties': selected_properties
            }
        return copy.deepcopy(self._task_template)

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> any:
        """Get information from the API."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                )
                if response.status in (401, 403):
                    raise NotionApiClientAuthenticationError(
                        "Invalid credentials",
                    )

                if response.status >= 400:
                    error_text = await response.text()
                    raise NotionApiClientError(
                        f"Notion API error {response.status}: {error_text[:500]}"
                    )

                content_type = response.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    return await response.json()
                return {}

        except asyncio.TimeoutError as exception:
            raise NotionApiClientCommunicationError(
                "Timeout error fetching information",
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            raise NotionApiClientCommunicationError(
                "Error fetching information",
            ) from exception
        except NotionApiClientError:
            raise
        except Exception as exception:  # pylint: disable=broad-except
            raise NotionApiClientError(
                "Something really wrong happened!"
            ) from exception
