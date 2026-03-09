# airline-sked

한-일 항공 노선 스케줄 변경 감지 및 알림 시스템

## 프로젝트 개요

한국 ↔ 일본 노선을 운항하는 한국/일본 항공사의 **신규 취항, 단항(운휴), 스케줄 변경**을 자동으로 감지하고 다양한 채널로 알림을 보내는 시스템.

## 대상 항공사

### 한국 항공사 (Korean Carriers)
| 코드 | 항공사 | 유형 |
|------|--------|------|
| KE | 대한항공 | FSC |
| OZ | 아시아나항공 | FSC |
| LJ | 진에어 | LCC |
| TW | 티웨이항공 | LCC |
| RS | 에어서울 | LCC |
| BX | 에어부산 | LCC |
| 7C | 제주항공 | LCC |
| ZE | 이스타항공 | LCC |

### 일본 항공사 (Japanese Carriers)
| 코드 | 항공사 | 유형 |
|------|--------|------|
| NH | ANA (전일본공수) | FSC |
| JL | JAL (일본항공) | FSC |
| MM | 피치항공 | LCC |
| GK | 젯스타재팬 | LCC |
| IJ | 스프링재팬 | LCC |
| BC | 스카이마크 | LCC |

## 대상 공항

### 한국 출발지
ICN (인천), GMP (김포), PUS (부산), CJU (제주), TAE (대구), CJJ (청주), MWX (무안), KWJ (광주), RSU (여수), USN (울산), HIN (사천)

### 일본 도착지
NRT (나리타), HND (하네다), KIX (간사이), FUK (후쿠오카), NGO (중부), CTS (신치토세/삿포로), OKA (나하/오키나와), KOJ (가고시마), OIT (오이타), KMJ (구마모토), TAK (타카마쓰), HIJ (히로시마), SDJ (센다이), AOJ (아오모리), KMQ (코마츠), TOY (토야마), NGS (나가사키), MYJ (마쓰야마), FSZ (시즈오카), IBR (이바라키), SHM (시라하마), MMJ (마쓰모토)

---

## 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                    airline-sked                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────┐   │
│  │ Scrapers │───▶│  Differ  │───▶│   Notifier       │   │
│  │          │    │ (변경감지) │    │ (TG/DC/Web/App)  │   │
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
│  │ Scheduler (cron) │    │  FastAPI (웹/API)     │       │
│  └──────────────────┘    └──────────────────────┘       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 핵심 기능

### 1. 데이터 수집 (Scrapers)
- 항공사 공식 사이트 스케줄 페이지 스크래핑
- 공항공사 운항정보 API/페이지
- 항공 뉴스/커뮤니티 크롤링 (보조)

### 2. 변경 감지 (Differ)
| 이벤트 유형 | 설명 | 우선도 |
|-------------|------|--------|
| `NEW_ROUTE` | 신규 취항 (이전에 없던 OD pair) | 🔴 HIGH |
| `ROUTE_SUSPENDED` | 단항/운휴 | 🔴 HIGH |
| `ROUTE_RESUMED` | 운항 재개 | 🟡 MEDIUM |
| `FREQ_CHANGE` | 주간 운항 빈도 변경 (예: 주3→주7) | 🟡 MEDIUM |
| `TIME_CHANGE` | 출발/도착 시간 변경 | 🟢 LOW |
| `AIRCRAFT_CHANGE` | 기재 변경 | 🟢 LOW |
| `SEASONAL_START` | 계절 스케줄 시작 | 🟡 MEDIUM |
| `SEASONAL_END` | 계절 스케줄 종료 | 🟢 LOW |

### 3. 알림 (Notifier)
- **Telegram Bot**: 실시간 알림, 구독 기반
- **Discord Bot**: 채널별 알림
- **웹 대시보드**: 전체 현황 조회, 필터링, 히스토리
- **향후**: 모바일 앱 (PWA 우선 검토)

---

## 기술 스택

| 구분 | 기술 | 비고 |
|------|------|------|
| 언어 | Python 3.11+ | |
| 웹 프레임워크 | FastAPI | 비동기, 자동 API 문서 |
| DB | SQLite + aiosqlite | 경량, 로컬 우선 |
| ORM | SQLModel (SQLAlchemy) | Pydantic 호환 |
| 스크래핑 | httpx + selectolax/bs4 | 비동기 HTTP |
| 헤드리스 | Playwright | JS 렌더링 필요 시 |
| 스케줄러 | APScheduler | 크론잡 대체 |
| 알림 | python-telegram-bot, discord.py | |
| 프론트엔드 | React (Vite) 또는 Next.js | 대시보드 |
| 캐싱 | 파일 기반 / Redis (옵션) | |

---

## 데이터 소스 전략

### Primary: 항공사 스케줄 페이지 스크래핑
각 항공사의 노선/스케줄 조회 페이지를 주기적으로 스크래핑하여 구조화된 데이터로 변환.

```
스크래핑 주기:
- 정기 수집: 매일 1회 (새벽 02:00 KST)
- 변경 감지 시: 2시간 간격 재확인
- 시즌 전환기: 매일 2회 (IATA 하계/동계 스케줄 전환)
```

### Secondary: 공항공사 공개데이터
- 인천공항공사 운항정보 (flights.airport.kr)
- 한국공항공사 (airport.co.kr) 운항정보
- 국토교통부 항공통계 (stat.molit.go.kr)
- 일본 국토교통성 항공국 데이터

### Tertiary: 뉴스/커뮤니티 크롤링 (보조)
- Aviation Wire (aviationwire.jp)
- Traicy (traicy.com)
- 마일모아 (milemoa.com)
- 항공 관련 보도자료

---

## DB 스키마

```sql
-- 항공사 마스터
CREATE TABLE airlines (
    iata_code TEXT PRIMARY KEY,      -- 'KE', 'NH' 등
    icao_code TEXT,
    name_ko TEXT NOT NULL,
    name_en TEXT NOT NULL,
    name_ja TEXT,
    country TEXT NOT NULL,           -- 'KR' or 'JP'
    carrier_type TEXT NOT NULL,      -- 'FSC' or 'LCC'
    website_url TEXT,
    schedule_url TEXT,               -- 스케줄 조회 페이지
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 공항 마스터
CREATE TABLE airports (
    iata_code TEXT PRIMARY KEY,      -- 'ICN', 'NRT' 등
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

-- 노선 (OD pair per airline)
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

-- 스케줄 스냅샷
CREATE TABLE schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id INTEGER NOT NULL REFERENCES routes(id),
    season TEXT,                      -- '2025S' (summer), '2025W' (winter)
    effective_from DATE,
    effective_to DATE,
    days_of_week TEXT,               -- 'MON,WED,FRI' 또는 '1,3,5'
    departure_time TEXT,             -- 'HH:MM' local
    arrival_time TEXT,               -- 'HH:MM' local
    flight_number TEXT,
    aircraft_type TEXT,              -- 'B737-800', 'A321neo' 등
    frequency_weekly INTEGER,        -- 주간 운항 횟수
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source TEXT                      -- 스크래핑 소스 식별
);

-- 변경 이벤트 로그
CREATE TABLE changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id INTEGER REFERENCES routes(id),
    event_type TEXT NOT NULL,        -- NEW_ROUTE, ROUTE_SUSPENDED, FREQ_CHANGE 등
    priority TEXT NOT NULL,          -- HIGH, MEDIUM, LOW
    summary TEXT NOT NULL,           -- 사람이 읽을 수 있는 요약
    detail_json TEXT,                -- 변경 전/후 상세 JSON
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notified_at TIMESTAMP,           -- 알림 발송 시각
    source TEXT
);

-- 뉴스/보도자료 수집
CREATE TABLE news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    url TEXT UNIQUE,
    source TEXT,                     -- 'aviationwire', 'traicy', 'milemoa'
    summary TEXT,
    related_airline TEXT,
    related_route TEXT,              -- 'ICN-NRT' 형태
    published_at TIMESTAMP,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 알림 구독 (Telegram/Discord 유저)
CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,          -- 'telegram', 'discord'
    chat_id TEXT NOT NULL,
    filter_airlines TEXT,            -- 쉼표 구분 항공사 코드, NULL=전체
    filter_origins TEXT,             -- 쉼표 구분 출발지, NULL=전체
    filter_destinations TEXT,        -- 쉼표 구분 도착지, NULL=전체
    filter_events TEXT,              -- 쉼표 구분 이벤트 유형, NULL=전체
    min_priority TEXT DEFAULT 'LOW', -- 최소 알림 우선도
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_routes_airline ON routes(airline_code);
CREATE INDEX idx_routes_od ON routes(origin, destination);
CREATE INDEX idx_schedules_route ON schedules(route_id);
CREATE INDEX idx_changes_type ON changes(event_type);
CREATE INDEX idx_changes_detected ON changes(detected_at);
CREATE INDEX idx_subscriptions_platform ON subscriptions(platform, is_active);
```

---

## 프로젝트 구조

```
airline-sked/
├── README.md
├── pyproject.toml
├── .env.example
├── alembic.ini                    # DB 마이그레이션
│
├── src/
│   └── airline_sked/
│       ├── __init__.py
│       ├── config.py              # 설정 (env, constants)
│       ├── database.py            # DB 연결, 세션
│       │
│       ├── models/                # SQLModel 모델
│       │   ├── __init__.py
│       │   ├── airline.py
│       │   ├── airport.py
│       │   ├── route.py
│       │   ├── schedule.py
│       │   ├── change.py
│       │   └── subscription.py
│       │
│       ├── scrapers/              # 데이터 수집
│       │   ├── __init__.py
│       │   ├── base.py            # BaseScraper ABC
│       │   ├── korean_air.py      # KE
│       │   ├── asiana.py          # OZ
│       │   ├── jeju_air.py        # 7C
│       │   ├── jin_air.py         # LJ
│       │   ├── tway.py            # TW
│       │   ├── air_seoul.py       # RS
│       │   ├── air_busan.py       # BX
│       │   ├── eastar.py          # ZE
│       │   ├── ana.py             # NH
│       │   ├── jal.py             # JL
│       │   ├── peach.py           # MM
│       │   ├── jetstar_jp.py      # GK
│       │   ├── spring_jp.py       # IJ
│       │   ├── skymark.py         # BC
│       │   ├── airport_kr.py      # 공항공사 데이터
│       │   └── news.py            # 뉴스 크롤러
│       │
│       ├── differ/                # 변경 감지 엔진
│       │   ├── __init__.py
│       │   ├── engine.py          # DiffEngine 메인 로직
│       │   ├── comparator.py      # 스케줄 비교 로직
│       │   └── events.py          # 이벤트 타입 정의
│       │
│       ├── notifiers/             # 알림 발송
│       │   ├── __init__.py
│       │   ├── base.py            # BaseNotifier ABC
│       │   ├── telegram.py
│       │   ├── discord.py
│       │   └── formatter.py       # 메시지 포매팅
│       │
│       ├── api/                   # FastAPI 웹 서버
│       │   ├── __init__.py
│       │   ├── main.py            # FastAPI app
│       │   ├── routes/
│       │   │   ├── airlines.py
│       │   │   ├── schedules.py
│       │   │   ├── changes.py
│       │   │   └── subscriptions.py
│       │   └── deps.py            # 의존성 주입
│       │
│       ├── scheduler/             # 스케줄러
│       │   ├── __init__.py
│       │   └── jobs.py            # APScheduler 잡 정의
│       │
│       └── cli.py                 # CLI 엔트리포인트
│
├── frontend/                      # 웹 대시보드 (React/Next.js)
│   ├── package.json
│   └── src/
│
├── data/
│   ├── airlines.json              # 항공사 시드 데이터
│   ├── airports.json              # 공항 시드 데이터
│   └── airline_sked.db            # SQLite DB 파일
│
├── tests/
│   ├── test_scrapers/
│   ├── test_differ/
│   └── test_notifiers/
│
└── docker/
    ├── Dockerfile
    └── docker-compose.yml
```

---

## 개발 로드맵

### Phase 1: Foundation (MVP) — 2~3주
- [ ] 프로젝트 셋업 (pyproject.toml, DB 스키마, 시드 데이터)
- [ ] BaseScraper 추상 클래스 + 1~2개 항공사 스크래퍼 구현
- [ ] DiffEngine 기본 로직 (NEW_ROUTE, ROUTE_SUSPENDED 감지)
- [ ] Telegram Bot 알림 (기본)
- [ ] CLI로 수동 실행 가능

### Phase 2: 확장 — 3~4주
- [ ] 나머지 항공사 스크래퍼 구현
- [ ] 공항공사 데이터 수집기
- [ ] 스케줄 상세 비교 (FREQ_CHANGE, TIME_CHANGE)
- [ ] Discord Bot 알림
- [ ] APScheduler 자동 수집
- [ ] 구독 필터링 (항공사/노선별)

### Phase 3: 대시보드 & 고도화 — 4~6주
- [ ] FastAPI REST API
- [ ] React 웹 대시보드 (노선 지도, 변경 타임라인)
- [ ] 뉴스 크롤러 연동
- [ ] PWA 지원 (모바일 앱 대체)
- [ ] Docker 배포 구성

### Phase 4: 운영 & 개선 — 지속
- [ ] 스크래퍼 안정성 개선 (재시도, fallback)
- [ ] 알림 메시지 다국어 (한/영/일)
- [ ] 히스토리 분석 (계절별 패턴 등)
- [ ] 사용자 피드백 반영

---

## 실행 방법 (Phase 1 이후)

```bash
# 설치
git clone https://github.com/YOUR_USERNAME/airline-sked.git
cd airline-sked
pip install -e ".[dev]"

# 환경변수 설정
cp .env.example .env
# TELEGRAM_BOT_TOKEN, DISCORD_BOT_TOKEN 등 설정

# DB 초기화 & 시드
airline-sked db init
airline-sked db seed

# 수동 수집
airline-sked scrape --airline KE
airline-sked scrape --all

# 변경 감지
airline-sked diff

# 서버 실행
airline-sked serve          # FastAPI 서버
airline-sked bot telegram   # Telegram 봇
airline-sked bot discord    # Discord 봇

# 전체 자동 실행
airline-sked run            # 스케줄러 포함 전체 실행
```

---

## 라이선스

MIT License
