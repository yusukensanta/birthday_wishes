import logging
from datetime import datetime, timezone
from typing import Optional

# Attempt to import croniter, and handle if not found due to potential install issues
try:
    from croniter import croniter
except ImportError:
    croniter = None # type: ignore
    logging.error("croniter library not found. Please install it.")


logger = logging.getLogger(__name__)

class MessageScheduler:
    def is_due(self, cron_expression: str, now: Optional[datetime] = None) -> bool:
        if croniter is None:
            logger.error("croniter is not available, cannot check schedule.")
            return False

        if not now:
            now = datetime.now(timezone.utc) # Ensure timezone-aware datetime

        try:
            # croniter by default matches if 'now' is >= the scheduled time.
            # For an exact match (within the same minute), we can check if 'now'
            # is a match for the cron expression.
            # croniter.match returns True if the cron expression is a valid match for the given datetime.
            return croniter.match(cron_expression, now)
        except ValueError as e:
            logger.error(f"Invalid cron expression '{cron_expression}': {e}")
            return False
        except Exception as e:
            logger.error(f"Error checking cron expression '{cron_expression}': {e}")
            return False
