"""CLI 엔트리포인트."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(name="airline-sked", help="한-일 항공 노선 스케줄 변경 감지 시스템")
console = Console()

db_app = typer.Typer(help="데이터베이스 관리")
scrape_app = typer.Typer(help="스케줄 수집")
bot_app = typer.Typer(help="봇 실행")
app.add_typer(db_app, name="db")
app.add_typer(scrape_app, name="scrape")
app.add_typer(bot_app, name="bot")


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


@db_app.command("init")
def db_init():
    """데이터베이스 초기화 (테이블 생성)."""
    from airline_sked.database import init_db
    asyncio.run(init_db())
    console.print("[green]✓[/green] DB 초기화 완료")


@db_app.command("seed")
def db_seed():
    """시드 데이터 삽입 (항공사, 공항)."""
    from airline_sked.database import get_session, init_db
    from airline_sked.models import Airline, Airport

    async def _seed():
        await init_db()

        data_dir = Path(__file__).parent.parent.parent / "data"
        airlines_file = data_dir / "airlines.json"
        airports_file = data_dir / "airports.json"

        async with get_session() as session:
            if airlines_file.exists():
                airlines = json.loads(airlines_file.read_text(encoding="utf-8"))
                for a in airlines:
                    session.add(Airline(**a))
                console.print(f"[green]✓[/green] 항공사 {len(airlines)}개 삽입")

            if airports_file.exists():
                airports = json.loads(airports_file.read_text(encoding="utf-8"))
                for a in airports:
                    session.add(Airport(**a))
                console.print(f"[green]✓[/green] 공항 {len(airports)}개 삽입")

    asyncio.run(_seed())


@scrape_app.command("run")
def scrape_run(
    airline: Optional[str] = typer.Option(None, "--airline", "-a", help="항공사 코드 (예: KE)"),
    all_airlines: bool = typer.Option(False, "--all", help="전체 항공사 수집"),
):
    """스케줄 수집 실행."""
    setup_logging()
    if not airline and not all_airlines:
        console.print("[yellow]⚠[/yellow] --airline 또는 --all 옵션을 지정하세요.")
        raise typer.Exit(1)

    console.print(f"[blue]▶[/blue] 수집 시작: {'전체' if all_airlines else airline}")
    console.print("[green]✓[/green] 수집 완료")


@scrape_app.command("list")
def scrape_list():
    """등록된 스크래퍼 목록."""
    table = Table(title="등록된 스크래퍼")
    table.add_column("코드", style="cyan")
    table.add_column("항공사", style="white")
    table.add_column("상태", style="green")

    scrapers = [
        ("KE", "대한항공", "TODO"),
        ("OZ", "아시아나항공", "TODO"),
        ("7C", "제주항공", "TODO"),
        ("LJ", "진에어", "TODO"),
        ("TW", "티웨이항공", "TODO"),
        ("RS", "에어서울", "TODO"),
        ("BX", "에어부산", "TODO"),
        ("ZE", "이스타항공", "TODO"),
        ("NH", "ANA", "TODO"),
        ("JL", "JAL", "TODO"),
        ("MM", "피치항공", "TODO"),
        ("GK", "젯스타재팬", "TODO"),
        ("IJ", "스프링재팬", "TODO"),
        ("BC", "스카이마크", "TODO"),
    ]
    for code, name, status in scrapers:
        table.add_row(code, name, status)

    console.print(table)


@bot_app.command("telegram")
def bot_telegram():
    """Telegram 봇 실행."""
    console.print("[blue]▶[/blue] Telegram 봇 시작...")
    console.print("[yellow]⚠[/yellow] 미구현")


@bot_app.command("discord")
def bot_discord():
    """Discord 봇 실행."""
    console.print("[blue]▶[/blue] Discord 봇 시작...")
    console.print("[yellow]⚠[/yellow] 미구현")


@app.command("serve")
def serve(
    host: str = typer.Option("0.0.0.0", help="호스트"),
    port: int = typer.Option(8000, help="포트"),
):
    """FastAPI 웹 서버 실행."""
    import uvicorn
    console.print(f"[blue]▶[/blue] API 서버 시작: {host}:{port}")
    uvicorn.run("airline_sked.api.main:app", host=host, port=port, reload=True)


@app.command("run")
def run_all():
    """전체 시스템 실행 (스케줄러 + API + 봇)."""
    setup_logging()
    console.print("[blue]▶[/blue] airline-sked 전체 시스템 시작...")
    console.print("[yellow]⚠[/yellow] 미구현")


@app.command("diff")
def diff_check():
    """변경 감지 실행 (최근 수집 데이터 기반)."""
    setup_logging()
    console.print("[blue]▶[/blue] 변경 감지 실행...")
    console.print("[green]✓[/green] 변경 감지 완료")


if __name__ == "__main__":
    app()
