from abc import ABC, abstractmethod
from datetime import datetime

from stravalib.model import SummaryActivity


class ActivityRepository(ABC):
    """Abstract interface for activity storage backends."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize sync state from the backing store. Should be called at startup."""

    @abstractmethod
    def get_last_sync_date(self) -> datetime | None:
        """Get the date up to which activities have been synchronized."""

    @abstractmethod
    def is_activity_synced(self, strava_id: int) -> bool:
        """Check if an activity has already been synced."""

    @abstractmethod
    async def get_activities(self, limit: int = 100) -> list[SummaryActivity]:
        """Get activities ordered by date descending, up to ``limit``."""

    @abstractmethod
    async def insert_activity(self, activity: SummaryActivity) -> bool:
        """Insert a new activity. Returns True if inserted, False if skipped."""
