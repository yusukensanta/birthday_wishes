import pytest
from datetime import datetime, timezone
from src.scheduler import MessageScheduler

@pytest.fixture
def scheduler():
    return MessageScheduler()

def test_is_due_every_minute(scheduler):
    # This should always be true as croniter matches the current minute when '*' is used.
    test_time = datetime(2023, 1, 1, 12, 30, 0, tzinfo=timezone.utc) # A fixed point in time
    assert scheduler.is_due("* * * * *", now=test_time)

def test_is_due_specific_match(scheduler):
    # Schedule for 12:30 PM on Jan 1st, 2023
    cron_expr = "30 12 1 1 *" # At 12:30 on day-of-month 1 and month 1
    test_time = datetime(2023, 1, 1, 12, 30, 0, tzinfo=timezone.utc)
    assert scheduler.is_due(cron_expr, now=test_time)

def test_is_due_specific_match_with_year(scheduler):
    # Schedule for 12:30 PM on Jan 1st, 2023
    cron_expr = "30 12 1 1 * 2023" # croniter supports 6-part cron with year
    test_time = datetime(2023, 1, 1, 12, 30, 0, tzinfo=timezone.utc)
    assert scheduler.is_due(cron_expr, now=test_time)

def test_is_not_due_specific_mismatch_minute(scheduler):
    cron_expr = "30 12 1 1 *"
    test_time = datetime(2023, 1, 1, 12, 31, 0, tzinfo=timezone.utc) # One minute later
    assert not scheduler.is_due(cron_expr, now=test_time)

def test_is_not_due_specific_mismatch_hour(scheduler):
    cron_expr = "30 12 1 1 *"
    test_time = datetime(2023, 1, 1, 13, 30, 0, tzinfo=timezone.utc) # One hour later
    assert not scheduler.is_due(cron_expr, now=test_time)

def test_is_not_due_specific_mismatch_day(scheduler):
    cron_expr = "30 12 1 1 *"
    test_time = datetime(2023, 1, 2, 12, 30, 0, tzinfo=timezone.utc) # One day later
    assert not scheduler.is_due(cron_expr, now=test_time)

def test_is_not_due_specific_mismatch_month(scheduler):
    cron_expr = "30 12 1 1 *"
    test_time = datetime(2023, 2, 1, 12, 30, 0, tzinfo=timezone.utc) # One month later
    assert not scheduler.is_due(cron_expr, now=test_time)

def test_is_not_due_specific_mismatch_year(scheduler):
    # Using 6-part cron to specify year for a more precise test
    cron_expr = "30 12 1 1 * 2023"
    test_time = datetime(2024, 1, 1, 12, 30, 0, tzinfo=timezone.utc) # One year later
    assert not scheduler.is_due(cron_expr, now=test_time)

def test_invalid_cron_expression(scheduler, caplog):
    # The MessageScheduler.is_due method logs an error and returns False for invalid expressions
    import logging
    caplog.set_level(logging.ERROR)
    assert not scheduler.is_due("not a cron string", now=datetime.now(timezone.utc))
    assert any("Invalid cron expression" in record.message for record in caplog.records)

def test_is_due_every_5_minutes_match(scheduler):
    cron_expr = "*/5 * * * *"
    test_time_match = datetime(2023, 1, 1, 12, 5, 0, tzinfo=timezone.utc)
    assert scheduler.is_due(cron_expr, now=test_time_match)

def test_is_due_every_5_minutes_no_match(scheduler):
    cron_expr = "*/5 * * * *"
    test_time_no_match = datetime(2023, 1, 1, 12, 6, 0, tzinfo=timezone.utc)
    assert not scheduler.is_due(cron_expr, now=test_time_no_match)

def test_is_due_start_of_minute(scheduler):
    # croniter match includes the exact start of the minute.
    cron_expr = "30 12 * * *" # At 12:30
    test_time = datetime(2023, 1, 1, 12, 30, 0, 0, tzinfo=timezone.utc)
    assert scheduler.is_due(cron_expr, now=test_time)

def test_is_due_during_minute(scheduler):
    # croniter match considers the whole minute.
    # So if it's 12:30:30, a cron for 12:30 should match.
    cron_expr = "30 12 * * *" # At 12:30
    test_time = datetime(2023, 1, 1, 12, 30, 30, 0, tzinfo=timezone.utc)
    assert scheduler.is_due(cron_expr, now=test_time)

def test_is_due_end_of_minute_boundary(scheduler):
    # croniter usually matches based on the cron expression's specified minute,
    # not the exact second. So if 'now' is 12:30:59, a "30 12 * * *" cron should match.
    cron_expr = "30 12 * * *"
    test_time = datetime(2023, 1, 1, 12, 30, 59, 999999, tzinfo=timezone.utc)
    assert scheduler.is_due(cron_expr, now=test_time)

def test_scheduler_handles_no_croniter(scheduler, caplog):
    # Simulate croniter not being installed or importable
    original_croniter_module = scheduler.croniter
    scheduler.croniter = None # type: ignore

    import logging
    caplog.set_level(logging.ERROR)

    assert not scheduler.is_due("* * * * *", now=datetime.now(timezone.utc))
    assert any("croniter is not available" in record.message for record in caplog.records)

    # Restore croniter for other tests
    scheduler.croniter = original_croniter_module
