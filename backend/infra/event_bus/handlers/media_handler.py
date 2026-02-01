"""
Media Event Handlers

Handles domain events from Media module:
- MediaUploaded: Schedule 30-day purge job
- MediaMovedToTrash: Reset 30-day timer
- MediaRestored: Cancel purge job
- MediaPurged: Clean up storage

Pattern: Event handlers registered via @EventHandlerRegistry.register decorator
All handlers are async functions that implement side effects.

Architecture:
- Handlers are decoupled from domain logic
- Side effects (background jobs, file operations) happen here
- Domain layer never knows about handler implementations
"""

from datetime import datetime, timedelta, timezone
import logging
from api.app.shared.base import DomainEvent

from ..event_handler_registry import EventHandlerRegistry

logger = logging.getLogger(__name__)


@EventHandlerRegistry.register(DomainEvent)
async def on_media_uploaded(event: DomainEvent) -> None:
    """
    Handle MediaUploaded event

    Side effect: Schedule 30-day automated purge for media file
    This implements POLICY-009 (30-day retention for temporary media)

    Args:
        event: MediaUploaded domain event

    TODO:
    - Schedule background job (Celery, APScheduler, or similar)
    - Calculate purge_at = now + 30 days
    - Store scheduled job ID in Media aggregate (for cancellation)
    """
    logger.info(f"[Event] MediaUploaded: {event.media_id}")
    logger.info(f"  File size: {getattr(event, 'file_size', 'unknown')} bytes")

    purge_at = datetime.now(timezone.utc) + timedelta(days=30)
    logger.info(f"  Scheduling purge at: {purge_at.isoformat()}")

    # TODO: Implement background job scheduling
    # await schedule_purge_job(
    #     media_id=event.media_id,
    #     purge_at=purge_at,
    #     reason="30-day retention policy"
    # )


@EventHandlerRegistry.register(DomainEvent)
async def on_media_moved_to_trash(event: DomainEvent) -> None:
    """
    Handle MediaMovedToTrash event

    Side effect: Reset 30-day timer when media is moved to trash
    (May indicate user is still using it, so delay purge)

    Args:
        event: MediaMovedToTrash domain event

    TODO:
    - Find existing scheduled purge job
    - Cancel and reschedule with extended deadline
    """
    logger.info(f"[Event] MediaMovedToTrash: {event.media_id}")
    logger.info(f"  Resetting purge timer (extend deadline)")

    # TODO: Reschedule purge job
    # await reschedule_purge_job(event.media_id, delay_days=30)


@EventHandlerRegistry.register(DomainEvent)
async def on_media_restored(event: DomainEvent) -> None:
    """
    Handle MediaRestored event

    Side effect: Cancel purge job when media is restored/recovered
    (User actively used this media, keep it)

    Args:
        event: MediaRestored domain event

    TODO:
    - Cancel scheduled purge job
    - Update job status in audit log
    """
    logger.info(f"[Event] MediaRestored: {event.media_id}")
    logger.info(f"  Canceling scheduled purge")

    # TODO: Cancel purge job
    # await cancel_purge_job(event.media_id)


@EventHandlerRegistry.register(DomainEvent)
async def on_media_purged(event: DomainEvent) -> None:
    """
    Handle MediaPurged event

    Side effect: Clean up storage and audit log after 30-day retention expires

    Args:
        event: MediaPurged domain event

    TODO:
    - Delete file from storage (S3 or local)
    - Log audit entry
    - Clean up database records if needed
    """
    logger.info(f"[Event] MediaPurged: {event.media_id}")
    logger.info(f"  Cleaning up from storage")

    # TODO: Implement storage cleanup
    # await storage_manager.delete_file(event.file_path)
    # await audit_logger.log_purge(event.media_id, event.library_id)
