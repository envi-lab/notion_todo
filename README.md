# Notion ToDo Integration for Home Assistant

## Experimental Notice

This repository is currently a hands-on maintenance playground.

If you are looking for a stable, polished, production-ready integration: do not download this one right now.

This is intentionally marked as work-in-progress while behavior is tested in a real setup.

Original upstream project:

- https://github.com/JanGiese/notion_todo

All glory goes to [JanGiese](https://github.com/JanGiese) and hypnotoad. This fork exists purely because the original went quiet - the idea and most of the code are his.


## What This Integration Does

This custom Home Assistant integration connects a Notion database to the Home Assistant `todo` platform.

Supported platform:

- `todo`: exposes tasks from a Notion database as Home Assistant todo items.

## Changes Made In This Fork

The following updates are already implemented in code:

### Fixes
- More robust property handling in `notion_property_helper.py`: missing properties no longer crash lookups.
- Date serialization and parsing in `notion_property_helper.py`: JSON-safe writing and more resilient reading.
- No extra trailing newline generated for text fields in `notion_property_helper.py`.
- Fallback handling for unknown Notion statuses in `todo.py` to prevent `KeyError`.
- Notion API version pinned to `2022-06-28` in `const.py` (verified: this is the latest working version released by Notion as of 2026).
- Pagination added to database queries in `api.py` so datasets over 100 tasks are fully loaded.
- Version bump in `manifest.json` to `1.1.2`.
- Hardcoded fallback property names and completed-status keywords moved out of code into `mapping.json`, loaded centrally via `const.py`.
- Translation files fixed to pass `hassfest` validation (no inline URLs in description fields).
- CI workflow overhauled: unit tests always run on push, integration tests only run when `NOTION_TOKEN` secret is available.
- `test_api.py` marked with `@pytest.mark.integration` so it is skipped cleanly in CI without credentials.
- Unit test file `test_mapping_unit.py` added: validates `mapping.json` structure without requiring any credentials.

### Features
- Project filtering: optionally define a Notion relation column and a filter keyword during setup. Only tasks whose linked project title contains that keyword will be shown (e.g. show only tasks tagged with "Chores" from a shared household project database).

## Installation (Home Assistant Custom Component)

1. Open your Home Assistant configuration directory (the one containing `configuration.yaml`).
2. Create `custom_components` if it does not exist.
3. Copy this repository's `custom_components/notion_todo` folder into your Home Assistant `custom_components` directory.
4. Restart Home Assistant.
5. In Home Assistant, go to `Settings -> Devices & Services -> Integrations`.
6. Click `Add Integration`, search for `Notion ToDo`, and complete setup.

## Configuration Notes

You will need two values during setup:

- Notion token:
	- Create an internal integration in Notion and generate a bearer token.
	- Notion docs: https://developers.notion.com/docs/getting-started
- Database ID:
	- Use a Notion database compatible with task fields.
	- Share that database with your integration so the token can access it.

If either token permissions or database sharing is incorrect, setup will fail with auth or connection errors.

## Known Limitations

- This integration is focused on task-style Notion databases and does not attempt to model every possible custom schema pattern.
- Status mapping is defensive, but custom workflows in Notion may still collapse into generic Home Assistant states.
- Network/API failures are handled, but real-time sync guarantees are still subject to Notion API behavior and Home Assistant polling cadence.

## Disclaimer

This is a personal hobby project. AI-assisted tooling was used during development, with human review throughout.

If something is broken for your setup, feel free to open an issue - no promises on response time, but feedback is welcome.
