# airline-sked

Open-source monitoring for Korea-Japan airline route changes.

## Implemented Features

- Implementation note: developed with both Codex GPT-5.4 High and Claude Code Opus 4.6
- SQLite-backed data model for airlines, airports, routes, schedules, changes, news, and subscriptions
- Diff engine for:
  - `NEW_ROUTE`
  - `ROUTE_SUSPENDED`
  - `FREQ_CHANGE`
  - `TIME_CHANGE`
  - `AIRCRAFT_CHANGE`
- Scrape pipeline that:
  - runs a scraper
  - upserts routes
  - stores schedule snapshots
  - saves detected change events
- Live crawler coverage:
  - `KE`: live route extraction from the official Korean Air page
  - `OZ`: live browser-backed schedule extraction from the official Asiana schedule flow
- FastAPI service scaffold with health/root endpoints and route/schedule/change API modules
- Static GitHub Pages homepage and dashboard
- CLI commands for database init/seed, scraping, diff, and serving the API
- Telegram/Discord message formatting utilities
- Test coverage for scraper helpers, diff helpers, and formatter logic

## Current Architecture

```text
scrapers
  -> scrape runner
  -> diff engine
  -> SQLite
  -> API / dashboard / notifier formatting
```

More concretely:

```text
src/airline_sked/scrapers/*        airline-specific collection
src/airline_sked/scrapers/runner.py
                                   scrape orchestration
src/airline_sked/differ/*          change detection
src/airline_sked/models/*          SQLModel data model
src/airline_sked/database.py       async DB engine/session
src/airline_sked/api/*             FastAPI app and routes
docs/*                             static homepage and dashboard
scripts/build_pages_data.py        dashboard JSON builder
```

## Repository Layout

```text
airline-sked/
├── README.md
├── pyproject.toml
├── data/
├── docs/
├── scripts/
├── src/airline_sked/
│   ├── api/
│   ├── differ/
│   ├── models/
│   ├── notifiers/
│   ├── scheduler/
│   ├── scrapers/
│   ├── cli.py
│   ├── config.py
│   └── database.py
├── tests/
└── docker/
```

## Setup

```bash
git clone https://github.com/YOUR_USERNAME/airline-sked.git
cd airline-sked
pip install -e ".[dev]"
python -m playwright install chromium
```

Initialize local data:

```bash
airline-sked db init
airline-sked db seed
```

## Run

Scrape one airline:

```bash
airline-sked scrape run --airline KE
airline-sked scrape run --airline OZ --origin ICN --destination NRT
```

Run all registered scrapers:

```bash
airline-sked scrape run --all
```

Start the API:

```bash
airline-sked serve
```

Build dashboard data:

```bash
python scripts/build_pages_data.py
```

## Notes

- `KE` is currently route-level live crawling, not full timetable extraction.
- `OZ` is the current live schedule crawler.
- Several other airline scraper classes still exist only as templates and are not included above as implemented features.
- `bot telegram`, `bot discord`, and `run` commands are still placeholders.

## Tests

```bash
PYTHONPATH=src pytest
```

## License

MIT License
