"""Adds config flow for Notion ToDo."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import (
    NotionApiClient,
    NotionApiClientAuthenticationError,
    NotionApiClientCommunicationError,
    NotionApiClientError,
)
from .const import (
    DOMAIN,
    LOGGER,
    CONF_DATABASE_ID,
    CONF_PROJECT_PROPERTY,
    CONF_PROJECT_FILTER,
)


class NotionTodoConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Notion ToDo."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.FlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:

                await self._test_credentials(
                    token=user_input[CONF_ACCESS_TOKEN],
                    database_id=user_input[CONF_DATABASE_ID],
                    project_property=user_input.get(CONF_PROJECT_PROPERTY),
                    project_filter=user_input.get(CONF_PROJECT_FILTER),
                )
            except NotionApiClientAuthenticationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except NotionApiClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except NotionApiClientError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_DATABASE_ID],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_DATABASE_ID,
                        default=(user_input or {}).get(CONF_DATABASE_ID),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                    vol.Required(CONF_ACCESS_TOKEN): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD
                        ),
                    ),
                    vol.Optional(
                        CONF_PROJECT_PROPERTY,
                        default=(user_input or {}).get(CONF_PROJECT_PROPERTY, "Project"),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                    vol.Optional(
                        CONF_PROJECT_FILTER,
                        default=(user_input or {}).get(CONF_PROJECT_FILTER),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                }
            ),
            errors=_errors,
        )

    async def _test_credentials(
        self,
        token: str,
        database_id: str,
        project_property: str | None = None,
        project_filter: str | None = None,
    ) -> None:
        """Validate credentials."""
        client = NotionApiClient(
            token=token,
            database_id=database_id,
            session=async_create_clientsession(self.hass),
            project_property=project_property,
            project_filter=project_filter,
        )
        await client.async_get_data()
