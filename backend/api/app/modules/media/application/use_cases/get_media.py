"""GetMedia UseCase - Get media by ID

This use case handles:
- Validating media exists
- Returning media domain object
"""

import logging
import time
from uuid import UUID

from ...domain import Media
from ...application.ports.output import MediaRepository
from ...exceptions import (
    MediaNotFoundError,
    MediaOperationError,
)
from api.app.shared.request_context import RequestContext


logger = logging.getLogger(__name__)


class GetMediaUseCase:
    """Get media by ID"""

    def __init__(self, repository: MediaRepository):
        self.repository = repository

    async def execute(self, media_id: UUID, ctx: RequestContext | None = None) -> Media:
        """
        Execute get media use case

        Args:
            media_id: Media ID

        Returns:
            Media domain object

        Raises:
            MediaNotFoundError: If not found
            MediaOperationError: On query error
        """
        start = time.perf_counter()
        correlation_id = getattr(ctx, "correlation_id", None)

        try:
            media = await self.repository.get_by_id(media_id, ctx=ctx)
            if not media:
                duration_ms = (time.perf_counter() - start) * 1000
                logger.info(
                    {
                        "event": "media.get.usecase.not_found",
                        "operation": "media.get",
                        "layer": "usecase",
                        "outcome": "not_found",
                        "correlation_id": correlation_id,
                        "media_id": str(media_id),
                        "duration_ms": duration_ms,
                    }
                )
                raise MediaNotFoundError(media_id)

            duration_ms = (time.perf_counter() - start) * 1000
            logger.info(
                {
                    "event": "media.get.usecase.success",
                    "operation": "media.get",
                    "layer": "usecase",
                    "outcome": "success",
                    "correlation_id": correlation_id,
                    "media_id": str(media_id),
                    "duration_ms": duration_ms,
                }
            )
            return media

        except Exception as e:
            if isinstance(e, MediaNotFoundError):
                raise

            duration_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                {
                    "event": "media.get.usecase.failed",
                    "operation": "media.get",
                    "layer": "usecase",
                    "outcome": "error",
                    "correlation_id": correlation_id,
                    "media_id": str(media_id),
                    "duration_ms": duration_ms,
                    "error_type": type(e).__name__,
                    "cause_type": type(getattr(e, "__cause__", None)).__name__ if getattr(e, "__cause__", None) else None,
                }
            )
            raise MediaOperationError(f"Failed to get media: {str(e)}") from e
