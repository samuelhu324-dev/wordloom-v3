"""GetMostUsedTags UseCase - Get most frequently used tags

This use case handles:
- Querying repository for top-used tags
- Sorting by usage_count in descending order
- Returning results for menu/dashboard display
"""

from typing import List

from ...domain import Tag
from ...application.ports.output import TagRepository
from ...exceptions import TagOperationError


class GetMostUsedTagsUseCase:
    """Get most frequently used tags for menu/dashboard display"""

    def __init__(self, repository: TagRepository):
        self.repository = repository

    async def execute(self, limit: int = 30) -> List[Tag]:
        """
        Execute get most used tags use case

        Args:
            limit: Maximum results to return (default 30)

        Returns:
            List of most-used Tag domain objects, sorted by usage_count descending

        Raises:
            TagOperationError: On query error
        """
        try:
            return await self.repository.find_most_used(limit=limit)
        except Exception as e:
            raise TagOperationError(f"Failed to get popular tags: {str(e)}")
