from enum import Enum


class ChronicleEventType(str, Enum):
    """Chronicle event types (Plan117 ready).

    约束：新增值需同步更新 ADR-093 / ADR-126 与 RULES 三件套，以及前端 union type。
    """

    BOOK_CREATED = "book_created"
    BOOK_MOVED = "book_moved"
    BOOK_MOVED_TO_BASEMENT = "book_moved_to_basement"  # Legacy alias (保留历史数据)
    BOOK_RESTORED = "book_restored"
    BOOK_DELETED = "book_deleted"
    BOOK_RENAMED = "book_renamed"
    BOOK_UPDATED = "book_updated"
    BLOCK_CREATED = "block_created"
    BLOCK_UPDATED = "block_updated"
    BLOCK_SOFT_DELETED = "block_soft_deleted"
    BLOCK_RESTORED = "block_restored"
    BLOCK_TYPE_CHANGED = "block_type_changed"
    BLOCK_STATUS_CHANGED = "block_status_changed"
    BOOK_OPENED = "book_opened"
    BOOK_STAGE_CHANGED = "book_stage_changed"
    BOOK_MATURITY_RECOMPUTED = "book_maturity_recomputed"
    STRUCTURE_TASK_COMPLETED = "structure_task_completed"
    STRUCTURE_TASK_REGRESSED = "structure_task_regressed"

    # Plan117 (P0/P1) additions
    BOOK_SOFT_DELETED = "book_soft_deleted"
    COVER_CHANGED = "cover_changed"
    COVER_COLOR_CHANGED = "cover_color_changed"
    CONTENT_SNAPSHOT_TAKEN = "content_snapshot_taken"
    WORDCOUNT_MILESTONE_REACHED = "wordcount_milestone_reached"
    TODO_PROMOTED_FROM_BLOCK = "todo_promoted_from_block"
    TODO_COMPLETED = "todo_completed"

    TAG_ADDED_TO_BOOK = "tag_added_to_book"
    TAG_REMOVED_FROM_BOOK = "tag_removed_from_book"

    # P2 placeholders (still listed to keep contracts stable)
    WORK_SESSION_SUMMARY = "work_session_summary"
    BOOK_VIEWED = "book_viewed"
    FOCUS_STARTED = "focus_started"
    FOCUS_ENDED = "focus_ended"
