# Quick Reference: Domain vs Service Layer Decision Tree

**Use this guide when deciding where to implement a new feature.**

---

## 🎯 Quick Decision Tree

```
┌─ Does this change represent a core business invariant?
│  ├─ YES → DOMAIN LAYER
│  └─ NO → Continue to next question
│
├─ Does this need to be audited/tracked in events?
│  ├─ YES → DOMAIN LAYER (with DomainEvent)
│  └─ NO → Continue to next question
│
├─ Is this a user convenience feature?
│  ├─ YES → SERVICE LAYER
│  └─ NO → Continue to next question
│
├─ Is this metadata storage or state manipulation?
│  ├─ YES → SERVICE LAYER
│  └─ NO → Continue to next question
│
└─ Does this require orchestration between aggregates?
   ├─ YES → SERVICE LAYER
   └─ NO → Consider REPOSITORY LAYER
```

---

## 📋 Feature Classification Examples

### ✅ DOMAIN LAYER Features

```python
# Core Business Invariants
- Book.rename(new_title)           # Changes title, emit BookRenamed event
- Book.change_status(NEW_STATUS)   # State invariant, emit BookStatusChanged
- Book.move_to_bookshelf(id)       # Transfer semantics, emit BookMovedToBookshelf
- Book.move_to_basement(id)        # Soft delete, emit BookMovedToBasement
- Book.restore_from_basement(id)   # Recovery, emit BookRestoredFromBasement
- Bookshelf.rename(new_name)       # Changes name, emit BookshelfRenamed
- Bookshelf.mark_deleted()         # Core invariant, emit BookshelfDeleted

# Characteristics:
✓ Changes core state
✓ Protects business rules
✓ Emits domain events
✓ Represents "what must be true"
```

### 🔧 SERVICE LAYER Features

```python
# Auxiliary/UI Features
- Book.pin_book(book_id)           # Direct field update, no event
- Book.unpin_book(book_id)         # Direct field update, no event
- Book.favorite_book(book_id)      # Direct field update, no event
- Book.unfavorite_book(book_id)    # Direct field update, no event
- Book.archive_book(book_id)       # Calls change_status() via orchestration
- Book.set_summary(book_id, text)  # Metadata update, no event
- Book.set_due_date(book_id, date) # Metadata update, no event

# Characteristics:
✓ Handles "how" questions
✓ Orchestrates domain operations
✓ No events (or auxiliary events only)
✓ Idempotent operations
✓ UI convenience features
```

### 🗂️ REPOSITORY LAYER Features

```python
# Data Access Abstractions
- await repository.get_by_id(id)
- await repository.get_by_library_id(lib_id)
- await repository.get_by_bookshelf_id(bs_id)
- await repository.save(entity)
- await repository.delete(id)

# Characteristics:
✓ Handles persistence
✓ Query abstractions
✓ No business logic
✓ Framework-agnostic
```

---

## 📊 Implementation Patterns

### Pattern 1: Domain Feature (Core Business Logic)

```python
# Location: bookshelf/domain.py
class Bookshelf(AggregateRoot):

    def rename(self, new_name: str) -> None:
        """Rename the Bookshelf (DOMAIN operation)"""
        # Validation (invariants)
        if not new_name or len(new_name) > 255:
            raise ValueError("Invalid name")

        # State change
        old_name = self.name
        self.name = new_name
        self.updated_at = datetime.utcnow()

        # EMIT EVENT (key characteristic)
        self.emit(BookshelfRenamed(
            bookshelf_id=self.id,
            old_name=old_name,
            new_name=new_name,
            occurred_at=self.updated_at
        ))

# Usage in Service: Just call domain method
async def rename_bookshelf(self, bs_id, new_name):
    bs = await repository.get_by_id(bs_id)
    bs.rename(new_name)  # ← Domain handles it
    await repository.save(bs)  # ← Save changes
```

---

### Pattern 2: Service Feature (Auxiliary Logic)

```python
# Location: bookshelf/service.py
class BookshelfService:

    async def pin_bookshelf(self, bookshelf_id: UUID) -> Bookshelf:
        """Pin a Bookshelf (SERVICE operation)"""
        # Get aggregate
        bs = await self.repository.get_by_id(bookshelf_id)

        # Direct field manipulation (NO domain method)
        if not bs.is_pinned:
            bs.is_pinned = True
            bs.pinned_at = datetime.utcnow()
            bs.updated_at = bs.pinned_at

            # Save (no events)
            await self.repository.save(bs)

        return bs

# Key differences from Pattern 1:
# - No domain method called
# - No events emitted
# - Direct field manipulation
# - Service orchestrates the operation
```

---

### Pattern 3: Orchestration (Multi-Aggregate)

```python
# Location: book/service.py
class BookService:

    async def move_to_bookshelf(
        self,
        book_id: UUID,
        target_bookshelf_id: UUID
    ) -> Book:
        """Move Book to different Bookshelf"""
        # Get both aggregates
        book = await self.book_repo.get_by_id(book_id)
        target_bs = await self.bs_repo.get_by_id(target_bookshelf_id)

        # Validate cross-aggregate constraints
        if target_bs.library_id != book.library_id:
            raise ValueError("Cannot move across libraries")

        # Call domain method (core operation)
        book.move_to_bookshelf(target_bookshelf_id)

        # Save both (Service coordinates)
        await self.book_repo.save(book)
        await self.bs_repo.update_book_count(target_bookshelf_id)

        return book

# Characteristics:
# - Calls domain method for core logic
# - Coordinates between aggregates
# - Validates cross-aggregate rules
# - Service layer handles complexity
```

---

## 🎯 When in Doubt

| Question | Answer | Layer |
|----------|--------|-------|
| "Does this validate a business rule?" | Yes | Domain |
| "Must this be auditable?" | Yes | Domain |
| "Is this just convenience for UI?" | Yes | Service |
| "Does this affect multiple aggregates?" | Yes | Service |
| "Could this change in requirements?" | Yes | Service |
| "Is this part of the core domain?" | Yes | Domain |
| "Is this a state transition?" | Yes | Domain |
| "Is this metadata?" | Yes | Service |

---

## 🚫 Anti-Patterns to Avoid

### ❌ DON'T: Put Auxiliary Features in Domain

```python
# WRONG - Don't do this
class Book(AggregateRoot):
    def pin(self):
        self.is_pinned = True
        self.emit(BookPinned(...))  # ← Anti-pattern

    def set_summary(self, summary):
        self.summary = summary
        self.emit(BookSummaryChanged(...))  # ← Anti-pattern
```

### ✅ DO: Keep Auxiliary Features in Service

```python
# RIGHT - Do this instead
class BookService:
    async def pin_book(self, book_id):
        book = await self.repo.get_by_id(book_id)
        book.is_pinned = True
        await self.repo.save(book)
        return book

    async def set_summary(self, book_id, summary):
        book = await self.repo.get_by_id(book_id)
        book.summary = summary
        await self.repo.save(book)
        return book
```

---

## 📚 Current Implementation Reference

### Bookshelf Domain Methods (✅ CORRECT)
```python
Domain Layer:
- rename()           ✅ CORE
- change_status()    ✅ CORE
- mark_deleted()     ✅ CORE

Service Layer:
- pin_bookshelf()         ✅ AUXILIARY
- unpin_bookshelf()       ✅ AUXILIARY
- favorite_bookshelf()    ✅ AUXILIARY
- unfavorite_bookshelf()  ✅ AUXILIARY
- archive_bookshelf()     ✅ AUXILIARY
- unarchive_bookshelf()   ✅ AUXILIARY
```

### Book Domain Methods (✅ CORRECT)
```python
Domain Layer:
- rename()                      ✅ CORE
- publish()                     ✅ CORE
- change_status()              ✅ CORE
- mark_deleted()               ✅ CORE
- move_to_bookshelf()          ✅ CORE (Transfer)
- move_to_basement()           ✅ CORE (Soft Delete)
- restore_from_basement()      ✅ CORE (Recovery)

Service Layer:
- pin_book()                   ✅ AUXILIARY
- unpin_book()                 ✅ AUXILIARY
- archive_book()               ✅ AUXILIARY
- set_summary()                ✅ AUXILIARY
- set_due_date()               ✅ AUXILIARY
```

---

## 🔍 Testing Guide

### Domain Layer Tests (Unit Tests)

```python
# Test invariants and business rules
def test_book_rename_updates_title():
    book = Book.create("My Book")
    book.rename("New Title")
    assert book.title == "New Title"
    assert BookRenamed in book.events

def test_book_rename_validates_length():
    book = Book.create("My Book")
    with pytest.raises(ValueError):
        book.rename("")  # Empty not allowed
```

### Service Layer Tests (Integration Tests)

```python
# Test orchestration and workflows
async def test_pin_book_updates_is_pinned():
    service = BookService(repo)
    book = await service.create_book("My Book")

    pinned = await service.pin_book(book.id)
    assert pinned.is_pinned == True

async def test_set_summary_updates_metadata():
    service = BookService(repo)
    book = await service.create_book("My Book")

    updated = await service.set_summary(book.id, "Summary text")
    assert updated.summary == "Summary text"
```

---

## 📖 Documentation References

- **Architecture Decision:** `backend/docs/DDD_RULES.yaml` (see AD-004)
- **Implementation Guide:** `backend/ARCHITECTURE_CODE_QUALITY_OPTIMIZATION.md`
- **Before/After Comparison:** `backend/ARCHITECTURE_BEFORE_AFTER_COMPARISON.md`

---

## ✨ Summary

**Domain Layer:** "What must be true?" (Business Invariants)
**Service Layer:** "How do we make it happen?" (Business Operations)
**Repository Layer:** "How do we store it?" (Data Persistence)
**Router Layer:** "How do we expose it?" (REST API)

Use this guide to maintain the proper layering as the codebase grows.
