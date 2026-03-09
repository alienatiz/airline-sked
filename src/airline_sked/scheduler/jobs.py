"""APScheduler 잡 정의.

주기적으로 실행할 수집/감지/알림 작업을 정의합니다.
"""

from __future__ import annotations

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


async def job_scrape_all() -> None:
    """전체 항공사 스케줄 수집 잡."""
    logger.info(f"[Scheduler] 전체 수집 시작: {datetime.now()}")

    from airline_sked.docs_dashboard import refresh_dashboard_data
    from airline_sked.scrapers import get_all_scrapers
    from airline_sked.scrapers.runner import run_scraper

    scrapers = get_all_scrapers()
    all_events = []

    for scraper in scrapers:
        try:
            _, events, summary = await run_scraper(scraper)
            if summary.success:
                all_events.extend(events)
                logger.info(
                    f"[{scraper.airline_code}] "
                    f"{summary.route_count} routes, "
                    f"{summary.saved_schedule_count} schedules, "
                    f"{summary.change_count} changes"
                )
            else:
                logger.warning(f"[{scraper.airline_code}] 수집 실패: {summary.errors}")

        except Exception as e:
            logger.error(f"[{scraper.airline_code}] 예외: {e}")

    output_file = refresh_dashboard_data()
    logger.info(f"[Scheduler] 대시보드 갱신 완료: {output_file}")

    if all_events:
        await _notify_changes(all_events)

    logger.info(f"[Scheduler] 수집 완료: {len(all_events)}건 변경 감지")


async def _notify_changes(events: list) -> None:
    """감지된 변경 이벤트를 알림 발송."""
    from airline_sked.config import settings
    from airline_sked.notifiers import TelegramNotifier

    if settings.telegram_bot_token:
        notifier = TelegramNotifier(
            bot_token=settings.telegram_bot_token,
            default_chat_id=settings.telegram_admin_chat_id,
        )
        sent = await notifier.send_batch(events)
        logger.info(f"[Notify] Telegram {sent}건 발송")


def setup_scheduler():
    """APScheduler 설정 및 잡 등록."""
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from airline_sked.config import settings

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        job_scrape_all,
        "cron",
        hour=2,
        minute=0,
        timezone="Asia/Seoul",
        id="daily_scrape",
        name="일일 전체 수집",
    )
    scheduler.add_job(
        job_scrape_all,
        "cron",
        month="3,10",
        hour=12,
        minute=0,
        timezone="Asia/Seoul",
        id="season_scrape",
        name="시즌 전환 추가 수집",
    )

    return scheduler
