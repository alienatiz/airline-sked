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

    from airline_sked.scrapers import get_all_scrapers
    from airline_sked.database import get_session
    from airline_sked.differ import DiffEngine

    scrapers = get_all_scrapers()
    all_events = []

    for scraper in scrapers:
        try:
            async with scraper:
                result = await scraper.scrape_schedules()

            if result.success:
                async with get_session() as session:
                    engine = DiffEngine(session)
                    events = await engine.process_scrape_result(result)
                    if events:
                        await engine.save_events(events)
                        all_events.extend(events)
                    await engine.update_routes(result)

                logger.info(f"[{scraper.airline_code}] {result.route_count} routes, {len(events)} changes")
            else:
                logger.warning(f"[{scraper.airline_code}] 수집 실패: {result.errors}")

        except Exception as e:
            logger.error(f"[{scraper.airline_code}] 예외: {e}")

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
