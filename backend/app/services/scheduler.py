from apscheduler.schedulers.background import BackgroundScheduler

from app.config.settings import settings
from app.services.event_service import collect_news_events
from app.utils.logger import logger

scheduler = BackgroundScheduler()


def start_scheduler():
    if not scheduler.running:
        collect_news_events()

        scheduler.add_job(
            collect_news_events,
            trigger="interval",
            minutes=settings.news_collection_interval_minutes,
            id="news_collection",
            replace_existing=True,
        )

        scheduler.start()

        logger.info(
            "Scheduler started successfully. "
            f"Interval: {settings.news_collection_interval_minutes} minute(s)."
        )


def stop_scheduler():
    if scheduler.running:

        scheduler.shutdown()

        logger.info("Scheduler stopped successfully.")