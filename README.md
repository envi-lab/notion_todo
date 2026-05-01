# Notion ToDo Integration for Home Assistant

This repository exists because the original project was basically in maintenance graveyard mode: useful idea, stale implementation, and enough sharp edges to turn simple sync into a mini incident report.

So this fork does the practical thing: keep the integration alive, harden the fragile parts, and document everything like adults who still occasionally sigh at JSON payloads.

## What This Integration Does

This custom Home Assistant integration connects a Notion database to the Home Assistant `todo` platform.

Supported platform:

- `todo`: exposes tasks from a Notion database as Home Assistant todo items.

## What Was Fixed In This Fork

The following updates are already implemented in code:

- More robust property handling in `notion_property_helper.py`: missing properties no longer crash lookups.
- Date serialization and parsing in `notion_property_helper.py`: JSON-safe writing and more resilient reading.
- No extra trailing newline generated for text fields in `notion_property_helper.py`.
- Fallback handling for unknown Notion statuses in `todo.py` to prevent `KeyError`.
- Notion API version updated in `const.py` to `2022-06-28`.
- Pagination added to database queries in `api.py` so datasets over 100 tasks are fully loaded.
- Version bump in `manifest.json` to `1.1.2`.

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

AI-assisted refactoring and fix support was used for parts of this maintenance pass.

Human review still decided what changed, what shipped, and what did not get blamed on the compiler.

## Contributing

Contributions are welcome. Please see `CONTRIBUTING.md`.
