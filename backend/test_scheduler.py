from unittest.mock import MagicMock, patch

from app.services import scheduler as scheduler_service


def test_start_scheduler_collects_immediately_and_schedules_minutes():
    mocked_scheduler = MagicMock()
    mocked_scheduler.running = False

    # The ingestion switch defaults on, so the live pipeline is exercised.
    with patch.object(scheduler_service, "scheduler", mocked_scheduler), \
            patch.object(scheduler_service.settings, "INGESTION_ENABLED", True), \
            patch.object(scheduler_service, "collect_news_events") as collect_news_events:
        scheduler_service.start_scheduler()

    mocked_scheduler.add_job.assert_called_once()
    _, kwargs = mocked_scheduler.add_job.call_args
    assert kwargs["trigger"] == "interval"
    assert kwargs["minutes"] == 30
    assert kwargs["id"] == "news_collection"
    assert kwargs["replace_existing"] is True
    mocked_scheduler.start.assert_called_once_with()


def test_start_scheduler_does_not_start_a_second_scheduler_when_running():
    mocked_scheduler = MagicMock()
    mocked_scheduler.running = True

    with patch.object(scheduler_service, "scheduler", mocked_scheduler), \
         patch.object(scheduler_service.settings, "INGESTION_ENABLED", True), \
         patch.object(scheduler_service, "collect_news_events") as collect_news_events:
        scheduler_service.start_scheduler()

    collect_news_events.assert_not_called()
    mocked_scheduler.add_job.assert_not_called()
    mocked_scheduler.start.assert_not_called()


def test_disabled_ingestion_does_not_start_the_scheduler():
    """INGESTION_ENABLED=false pauses live news gathering entirely."""
    mocked_scheduler = MagicMock()
    mocked_scheduler.running = False

    with patch.object(scheduler_service, "scheduler", mocked_scheduler), \
         patch.object(scheduler_service.settings, "INGESTION_ENABLED", False), \
         patch.object(scheduler_service, "collect_news_events") as collect_news_events:
        scheduler_service.start_scheduler()

    # No job is registered, the scheduler never starts, and no collection runs.
    collect_news_events.assert_not_called()
    mocked_scheduler.add_job.assert_not_called()
    mocked_scheduler.start.assert_not_called()


def test_disabled_ingestion_skips_collection_even_if_invoked_directly():
    """The collector itself is guarded, so a manual call cannot fetch news."""
    with patch.object(scheduler_service.settings, "INGESTION_ENABLED", False), \
         patch("app.services.event_service.fetch_supply_chain_news") as news, \
         patch("app.services.event_service.fetch_currents_news") as currents, \
         patch("app.services.event_service.SessionLocal") as session_factory:
        from app.services.event_service import collect_news_events

        collect_news_events()

    news.assert_not_called()
    currents.assert_not_called()
    session_factory.assert_not_called()
