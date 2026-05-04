# TODO notion_todo

## Erledigt

- [x] Hardcodierte Begriffe zentralisieren (Punkte 1 + 4 zusammen).
  - [x] Fallback-Namen fuer Due Date und Description aus Code entfernen.
  - [x] Completed-Keywords aus API und Todo-Code entfernen.
  - [x] Zentrale `mapping.json` einfuehren.
  - [x] Mapping in `const.py` laden und in allen Modulen verwenden.

- [x] Pruefen, ob `custom_components/notion_todo/test_api.py` aktiv genutzt wird.
  - [x] Mit `@pytest.mark.integration` markiert und `skipIf`-Guard fuer fehlenden Token.
  - [x] Unit-Tests in `test_mapping_unit.py` ohne Credentials ergaenzt.
  - [x] `pytest.ini` mit `integration`-Marker angelegt.

- [x] Notion API Version pruefen.
  - [x] `2022-06-28` ist die aktuellste gueltige Version (Stand 2026, verifiziert per Smoketest).
  - [x] Neuere Datumsstrings werden von Notion mit `missing_version` / `invalid_request_url` abgelehnt.

- [x] CI/GitHub Actions aufraeumen.
  - [x] Nightly Validate-Cron deaktiviert.
  - [x] Hassfest-Fehler in Translations behoben (keine URLs in Description-Feldern).
  - [x] Workflow aufgeteilt: Unit-Tests immer, Integration-Tests nur mit Secret.
  - [x] Workflow-Actions auf aktuelle Versionen gebracht (`checkout@v5` etc.).

- [x] README.md overhaul.

## Offen

- [ ] GitHub-Repo Beschreibung und Topics setzen (manuell im GitHub UI).
