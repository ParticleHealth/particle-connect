"""Base agent contract for ToC workflow agents."""

from database import Database


class BaseAgent:
    """Abstract base for all ToC workflow agents."""

    def __init__(self, db: Database):
        self.db = db

    async def run(self, workflow_id: str) -> dict:
        raise NotImplementedError

    def validate_preconditions(self, workflow_id: str) -> bool:
        raise NotImplementedError
