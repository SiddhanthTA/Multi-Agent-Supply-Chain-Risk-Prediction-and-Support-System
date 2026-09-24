from unittest.mock import MagicMock, patch

from app.services import scheduler as scheduler_service


def test_start_scheduler_collects_immediately_and_schedules_minutes():
    mocked_scheduler = MagicMock()
    mocked_scheduler.running = False

    with patch.object(scheduler_service, "scheduler", mocked_scheduler), \
            patch.object(scheduler_service, "collect_news_events") as collect_news_events:
        scheduler_service.start_scheduler()

    collect_news_events.assert_called_once_with()
    mocked_scheduler.add_job.assert_called_once_with(
        collect_news_events,
        trigger="interval",
        minutes=30,
        id="news_collection",
        replace_existing=True,
    )
    mocked_scheduler.start.assert_called_once_with()


def test_start_scheduler_does_not_start_a_second_scheduler_when_running():
    mocked_scheduler = MagicMock()
    mocked_scheduler.running = True

    with patch.object(scheduler_service, "scheduler", mocked_scheduler), \
         patch.object(scheduler_service, "collect_news_events") as collect_news_events:
        scheduler_service.start_scheduler()

    collect_news_events.assert_not_called()
    mocked_scheduler.add_job.assert_not_called()
    mocked_scheduler.start.assert_not_called()
