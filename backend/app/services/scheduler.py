from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from app.config.settings import settings
from app.services.event_service import collect_news_events
from app.utils.logger import logger

scheduler = BackgroundScheduler()


def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(
            collect_news_events,
            trigger="interval",
            minutes=settings.news_collection_interval_minutes,
            id="news_collection",
            replace_existing=True,
            next_run_time=datetime.now(timezone.utc),
            max_instances=1,
        )

        scheduler.start()

        logger.info(
            "Scheduler started successfully. "
            f"Interval: {settings.news_collection_interval_minutes} minute(s). "
            "Initial collection is running in the background."
        )


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped successfully.")
