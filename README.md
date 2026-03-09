# airline-sked

Open-source monitoring for Korea-Japan airline route changes.

`airline-sked` tracks route launches, suspensions, and schedule changes across Korean and Japanese carriers, then exposes the results through an API, a dashboard, and notification-friendly event formatting.

## Current Status

This repository is in early development.

- Implemented: database models, seed data, a FastAPI service scaffold, a diff engine, formatter utilities, a CLI scaffold, static Pages assets, and test coverage for core comparison/formatting logic.
- In progress: production-grade scrapers, scheduler orchestration, and live Telegram/Discord bot delivery.

## Scope

The project focuses on routes between South Korea and Japan and is designed to detect:

- new routes
- route suspensions
- route resumptions
- frequency changes
- departure time changes
- aircraft changes
- seasonal schedule start/end signals

## Target Airlines

### Korean carriers

| Code | Airline | Type |
|------|---------|------|
| KE | Korean Air | FSC |
| OZ | Asiana Airlines | FSC |
| LJ | Jin Air | LCC |
| TW | T'way Air | LCC |
| RS | Air Seoul | LCC |
| BX | Air Busan | LCC |
| 7C | Jeju Air | LCC |
| ZE | Eastar Jet | LCC |

### Japanese carriers

| Code | Airline | Type |
|------|---------|------|
| NH | ANA (All Nippon Airways) | FSC |
| JL | JAL (Japan Airlines) | FSC |
| MM | Peach Aviation | LCC |
| GK | Jetstar Japan | LCC |
| IJ | Spring Japan | LCC |
| BC | Skymark Airlines | LCC |

## Target Airports

### Korea origins

`ICN`, `GMP`, `PUS`, `CJU`, `TAE`, `CJJ`, `MWX`, `KWJ`, `RSU`, `USN`, `HIN`

### Japan destinations

`NRT`, `HND`, `KIX`, `FUK`, `NGO`, `CTS`, `OKA`, `KOJ`, `OIT`, `KMJ`, `TAK`, `HIJ`, `SDJ`, `AOJ`, `KMQ`, `TOY`, `NGS`, `MYJ`, `FSZ`, `IBR`, `SHM`, `MMJ`

## System Architecture

```text
┌─────────────────────────────────────────────────────────┐
│                       airline-sked                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────┐   │
│  │ Scrapers │───▶│  Differ  │───▶│   Notifiers      │   │
│  │          │    │          │    │ (TG/DC/Web/App)  │   │
│  └────┬─────┘    └────┬─────┘    └──────────────────┘   │
│       │               │                                  │
│       ▼               ▼                                  │
│  ┌─────────────────────────┐                             │
│  │    SQLite Database      │                             │
│  │  ┌───────┐ ┌─────────┐ │                             │
│  │  │routes │ │schedules│ │                             │
│  │  └───────┘ └─────────┘ │                             │
│  │  ┌───────┐ ┌─────────┐ │                             │
│  │  │changes│ │  news   │ │                             │
│  │  └───────┘ └─────────┘ │                             │
│  └─────────────────────────┘                             │
│                                                         │
│  ┌──────────────────┐    ┌──────────────────────┐       │
│  │ Scheduler (cron) │    │  FastAPI (web/API)   │       │
│  └──────────────────┘    └──────────────────────┘       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Core Features

### 1. Data collection

- scrape airline schedule pages
- ingest airport operations data where useful
- use aviation news/community sources as supporting signals

### 2. Change detection

| Event type | Description | Priority |
|------------|-------------|----------|
| `NEW_ROUTE` | New service on a previously unseen OD pair | HIGH |
| `ROUTE_SUSPENDED` | Route suspension or service stop | HIGH |
| `ROUTE_RESUMED` | Service resumed after suspension | MEDIUM |
| `FREQ_CHANGE` | Weekly frequency changed, for example `3/wk -> 7/wk` | MEDIUM |
| `TIME_CHANGE` | Departure or arrival time changed | LOW |
| `AIRCRAFT_CHANGE` | Aircraft type changed | LOW |
| `SEASONAL_START` | Seasonal schedule started | MEDIUM |
| `SEASONAL_END` | Seasonal schedule ended | LOW |

### 3. Delivery surfaces

- Telegram message formatting
- Discord embed formatting
- web dashboard and API endpoints
- future mobile/PWA support

## Data Source Strategy

### Primary: airline schedule pages

Each airline's public route or timetable page is the primary source of truth.

Suggested collection cadence:

- regular run: once per day at `02:00 KST`
- recheck after detected changes: every 2 hours
- seasonal transition periods: twice per day around IATA summer/winter schedule cutovers

### Secondary: airport and public aviation data

- Incheon Airport schedule/operations data
- Korea Airports Corporation data
- Korean MOLIT aviation statistics
- Japanese MLIT aviation data

### Tertiary: news and community monitoring

- Aviation Wire
- Traicy
- airline press releases
- community posts used only as supporting evidence

## Database Schema

```sql
-- Airline master
CREATE TABLE airlines (
    iata_code TEXT PRIMARY KEY,      -- 'KE', 'NH', etc.
    icao_code TEXT,
    name_ko TEXT NOT NULL,
    name_en TEXT NOT NULL,
    name_ja TEXT,
    country TEXT NOT NULL,           -- 'KR' or 'JP'
    carrier_type TEXT NOT NULL,      -- 'FSC' or 'LCC'
    website_url TEXT,
    schedule_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Airport master
CREATE TABLE airports (
    iata_code TEXT PRIMARY KEY,      -- 'ICN', 'NRT', etc.
    icao_code TEXT,
    name_ko TEXT NOT NULL,
    name_en TEXT NOT NULL,
    name_ja TEXT,
    city_ko TEXT,
    city_en TEXT,
    country TEXT NOT NULL,
    latitude REAL,
    longitude REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Route master (OD pair per airline)
CREATE TABLE routes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    airline_code TEXT NOT NULL REFERENCES airlines(iata_code),
    origin TEXT NOT NULL REFERENCES airports(iata_code),
    destination TEXT NOT NULL REFERENCES airports(iata_code),
    status TEXT NOT NULL DEFAULT 'ACTIVE',  -- ACTIVE, SUSPENDED, SEASONAL
    first_seen DATE,
    last_seen DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(airline_code, origin, destination)
);

-- Schedule snapshots
CREATE TABLE schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id INTEGER NOT NULL REFERENCES routes(id),
    season TEXT,                      -- '2025S' (summer), '2025W' (winter)
    effective_from DATE,
    effective_to DATE,
    days_of_week TEXT,                -- 'MON,WED,FRI' or '1,3,5'
    departure_time TEXT,              -- local 'HH:MM'
    arrival_time TEXT,                -- local 'HH:MM'
    flight_number TEXT,
    aircraft_type TEXT,               -- 'B737-800', 'A321neo', etc.
    frequency_weekly INTEGER,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source TEXT
);

-- Change event log
CREATE TABLE changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id INTEGER REFERENCES routes(id),
    event_type TEXT NOT NULL,
    priority TEXT NOT NULL,           -- HIGH, MEDIUM, LOW
    summary TEXT NOT NULL,
    detail_json TEXT,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notified_at TIMESTAMP,
    source TEXT
);

-- News / press collection
CREATE TABLE news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    url TEXT UNIQUE,
    source TEXT,
    summary TEXT,
    related_airline TEXT,
    related_route TEXT,               -- format: 'ICN-NRT'
    published_at TIMESTAMP,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Notification subscriptions
CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,           -- 'telegram', 'discord'
    chat_id TEXT NOT NULL,
    filter_airlines TEXT,             -- comma-separated, NULL = all
    filter_origins TEXT,              -- comma-separated, NULL = all
    filter_destinations TEXT,         -- comma-separated, NULL = all
    filter_events TEXT,               -- comma-separated, NULL = all
    min_priority TEXT DEFAULT 'LOW',
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_routes_airline ON routes(airline_code);
CREATE INDEX idx_routes_od ON routes(origin, destination);
CREATE INDEX idx_schedules_route ON schedules(route_id);
CREATE INDEX idx_changes_type ON changes(event_type);
CREATE INDEX idx_changes_detected ON changes(detected_at);
CREATE INDEX idx_subscriptions_platform ON subscriptions(platform, is_active);
```

## Repository Layout

```text
airline-sked/
├── README.md
├── pyproject.toml
├── data/                     # seed data and dashboard data
├── docs/                     # GitHub Pages landing page + dashboard
├── scripts/                  # build helpers for static docs
├── src/airline_sked/
│   ├── api/                  # FastAPI app and routes
│   ├── differ/               # change detection engine
│   ├── models/               # SQLModel models
│   ├── notifiers/            # notifier base classes and formatters
│   ├── scheduler/            # scheduled jobs
│   ├── scrapers/             # scraper interfaces and implementations
│   ├── cli.py                # Typer CLI entrypoint
│   ├── config.py             # settings
│   └── database.py           # async DB engine and sessions
├── tests/                    # unit tests
└── docker/                   # container assets
```

## Roadmap

### Phase 1: Foundation

- [x] project packaging and dependency setup
- [x] database schema and seed data
- [x] core diff engine structure
- [x] formatter utilities and base notifier interfaces
- [x] CLI and API scaffolding

### Phase 2: Source coverage

- [ ] implement stable airline scrapers across all target carriers
- [ ] ingest airport schedule data for cross-checking
- [ ] persist scraped snapshots automatically
- [ ] expand comparison logic for more schedule-level changes

### Phase 3: Delivery

- [ ] production Telegram notifications
- [ ] production Discord notifications
- [ ] scheduler-driven recurring collection
- [ ] subscription filtering by airline, route, and event type

### Phase 4: Productization

- [ ] richer REST endpoints
- [ ] more capable dashboard visualizations
- [ ] historical analytics by season and route
- [ ] multilingual alert messages
- [ ] containerized deployment workflow

## Getting Started

```bash
git clone https://github.com/YOUR_USERNAME/airline-sked.git
cd airline-sked
pip install -e ".[dev]"
```

Initialize and seed the local database:

```bash
airline-sked db init
airline-sked db seed
```

Inspect or run the CLI:

```bash
airline-sked scrape list
airline-sked scrape run --airline KE
airline-sked scrape run --all
airline-sked diff
airline-sked serve
```

Current command notes:

- `airline-sked serve` starts the FastAPI app locally.
- `airline-sked diff` runs the current detection scaffold.
- `airline-sked bot telegram`, `airline-sked bot discord`, and `airline-sked run` are present but not fully implemented yet.

## Tests

```bash
pytest
```

## License

MIT License
