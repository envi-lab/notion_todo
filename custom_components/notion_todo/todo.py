"""A todo platform for Notion."""

import asyncio
from typing import cast

from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    TASK_STATUS_PROPERTY,
    TASK_DESCRIPTION_PROPERTY,
    TASK_DATE_PROPERTY,
)
from .coordinator import NotionDataUpdateCoordinator
from .notion_property_helper import NotionPropertyHelper as propHelper

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the todo platform config entry."""
    coordinator: NotionDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entity_name = f"Notion {entry.title[-6:]}" if entry.title else "Notion"
    async_add_entities([NotionTodoListEntity(coordinator, entity_name, entry.entry_id)])

STATUS_IN_PROGRESS = 'in-progress'
STATUS_ARCHIVED = 'archived'
STATUS_DONE = 'done'
STATUS_NOT_STARTED = 'not-started'


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


def _map_notion_to_hass_status(status_id: str | None, status_name: str | None) -> TodoItemStatus:
    if status_id in (STATUS_DONE, STATUS_ARCHIVED) or _name_looks_completed(status_name):
        return TodoItemStatus.COMPLETED
    if status_id in (STATUS_NOT_STARTED, STATUS_IN_PROGRESS):
        return TodoItemStatus.NEEDS_ACTION
    return TodoItemStatus.NEEDS_ACTION

class NotionTodoListEntity(CoordinatorEntity[NotionDataUpdateCoordinator], TodoListEntity):
    """A Notion TodoListEntity."""

    _attr_supported_features = (
        TodoListEntityFeature.CREATE_TODO_ITEM
        | TodoListEntityFeature.UPDATE_TODO_ITEM
        | TodoListEntityFeature.DELETE_TODO_ITEM
        | TodoListEntityFeature.SET_DESCRIPTION_ON_ITEM
        | TodoListEntityFeature.SET_DUE_DATE_ON_ITEM
        | TodoListEntityFeature.SET_DUE_DATETIME_ON_ITEM
    )

    def __init__(
        self,
        coordinator: NotionDataUpdateCoordinator,
        name: str,
        entry_id: str,
    ) -> None:
        """Initialize TodoListEntity."""
        super().__init__(coordinator=coordinator)
        self._attr_unique_id = f"{DOMAIN}_{entry_id}"
        self._attr_name = name
        self._status = {}

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.data is None:
            self._attr_todo_items = None
        else:
            items = []
            for task in self.coordinator.data['results']:
                id = task['id']
                status_id, status_name = propHelper.get_status_meta_by_id(TASK_STATUS_PROPERTY, task)
                self._status[id] = status_id
                status = _map_notion_to_hass_status(status_id, status_name)

                if status == TodoItemStatus.COMPLETED:
                    continue

                due = propHelper.get_property_by_id(TASK_DATE_PROPERTY, task)

                items.append(
                    TodoItem(
                        summary=propHelper.get_property_by_id('title', task),
                        uid=id,
                        status=status,
                        description=propHelper.get_property_by_id(TASK_DESCRIPTION_PROPERTY, task),
                        due=due,
                    )
                )
            self._attr_todo_items = items
        super()._handle_coordinator_update()

    async def async_create_todo_item(self, item: TodoItem) -> None:
        """Create a To-do item."""
        status = await self.coordinator.client.resolve_status_id(
            is_completed=item.status == TodoItemStatus.COMPLETED,
            current_status_id=None,
        )
        await self.coordinator.client.create_task(item.summary, status=status)
        await self.coordinator.async_refresh()

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Update a To-do item."""
        uid: str = cast(str, item.uid)
        current_status_id = self._status.get(uid)
        status = await self.coordinator.client.resolve_status_id(
            is_completed=item.status == TodoItemStatus.COMPLETED,
            current_status_id=current_status_id,
        )

        await self.coordinator.client.update_task(task_id=uid,
                                                  title=item.summary,
                                                  status=status,
                                                  due=item.due,
                                                  description=item.description)

        await self.coordinator.async_refresh()

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        """Delete a To-do item."""
        await asyncio.gather(
            *[self.coordinator.client.delete_task(task_id=uid) for uid in uids]
        )
        await self.coordinator.async_refresh()

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass update state from existing coordinator data."""
        await super().async_added_to_hass()
        self._handle_coordinator_update()
