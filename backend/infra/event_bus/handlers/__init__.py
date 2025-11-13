"""
Domain Event Handlers

Each file handles one or more related domain events.

Handlers (planned):
  - media_purge_handler.py: Listen to MediaUploaded, schedule 30-day purge
  - bookshelf_cascade_handler.py: BookshelfDeleted → cascade to books/blocks
  - tag_usage_handler.py: TagAssociatedWithEntity → update usage_count

Pattern:
  @event_bus.on(MediaUploaded)
  async def handle_media_uploaded(event: MediaUploaded):
      # Schedule purge job after 30 days
      pass
"""
