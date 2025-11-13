"""SearchTags UseCase - Search tags by partial name match

This use case handles:
- Validating search keyword (1-100 chars)
- Querying repository for matching tags
- Returning results up to limit
"""

from typing import List

from ...domain import Tag
from ...application.ports.output import TagRepository
from ...exceptions import TagOperationError


class SearchTagsUseCase:
    """Search tags by partial name match"""

    def __init__(self, repository: TagRepository):
        self.repository = repository

    async def execute(
        self,
        keyword: str,
        limit: int = 20
    ) -> List[Tag]:
        """
        Execute search tags use case

        Args:
            keyword: Search keyword (partial name match)
            limit: Maximum results to return (default 20)

        Returns:
            List of matching Tag domain objects

        Raises:
            TagOperationError: On query error
        """
        if not keyword or len(keyword) > 100:
            return []

        try:
            return await self.repository.find_by_name(keyword, limit=limit)
        except Exception as e:
            raise TagOperationError(f"Failed to search tags: {str(e)}")
