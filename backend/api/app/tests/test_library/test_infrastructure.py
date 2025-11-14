"""
Library Infrastructure Layer Tests

Purpose:
- Test LibraryModel (ORM) mapping and persistence
- Test LibraryRepositoryImpl adapter implementation
- Verify round-trip domain ↔ ORM conversion
- Validate business rules enforcement (RULE-001, RULE-002, RULE-003)

Test Coverage:
- ORM Model: to_dict(), from_dict(), __repr__()
- Repository: save(), get_by_id(), get_by_user_id(), delete()
- Business Rules: user_id uniqueness (RULE-001)

Architecture:
- Uses MockRepository for isolated testing (no DB)
- Fixtures in conftest.py for reusability
- Async/await pattern for consistency with application layer
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4, UUID

from api.app.modules.library.domain.library import Library
from api.app.modules.library.domain.library_name import LibraryName


# ============================================================================
# ORM Model Tests
# ============================================================================

class TestLibraryModel:
    """Test LibraryModel ORM mapping and serialization"""

    @pytest.mark.asyncio
    async def test_library_model_to_dict(self, library_factory):
        """Test ORM model to dictionary conversion"""
        library = library_factory()
        data = library.to_dict()

        assert data["id"] == library.id
        assert data["user_id"] == library.user_id
        assert data["name"] == library.name
        assert isinstance(data["created_at"], datetime)
        assert isinstance(data["updated_at"], datetime)

    @pytest.mark.asyncio
    async def test_library_model_from_dict(self, library_data):
        """Test creating ORM model from dictionary"""
        from infra.database.models.library_models import LibraryModel

        model = LibraryModel.from_dict(library_data)

        assert model.user_id == library_data["user_id"]
        assert model.name == library_data["name"]
        assert model.id == library_data["id"]

    @pytest.mark.asyncio
    async def test_library_model_repr(self, library_factory):
        """Test ORM model string representation"""
        library = library_factory()
        repr_str = repr(library)

        assert "LibraryModel" in repr_str
        assert str(library.id) in repr_str
        assert str(library.user_id) in repr_str


# ============================================================================
# Repository Adapter Tests
# ============================================================================

class TestLibraryRepository:
    """Test LibraryRepositoryImpl adapter implementation"""

    @pytest.mark.asyncio
    async def test_repository_save_and_get(self, repository, library_domain):
        """Test save and retrieve by ID"""
        # Save
        await repository.save(library_domain)

        # Get by ID
        retrieved = await repository.get_by_id(library_domain.id)

        assert retrieved is not None
        assert retrieved.id == library_domain.id
        assert str(retrieved.name) == "My Library"

    @pytest.mark.asyncio
    async def test_repository_get_by_user_id(self, repository, user_id, library_domain):
        """Test retrieve library by user ID (RULE-001: one per user)"""
        await repository.save(library_domain)

        retrieved = await repository.get_by_user_id(user_id)

        assert retrieved is not None
        assert retrieved.user_id == user_id
        assert str(retrieved.name) == "My Library"

    @pytest.mark.asyncio
    async def test_repository_user_id_uniqueness(self, repository, user_id):
        """Test RULE-001: Each user has exactly one Library"""
        # Create first library
        lib1 = Library.create(
            user_id=user_id,
            name=LibraryName("Library One"),
        )
        await repository.save(lib1)

        # Try to create second library with same user_id (should fail)
        lib2 = Library.create(
            user_id=user_id,
            name=LibraryName("Library Two"),
        )

        with pytest.raises(Exception):  # RULE-001 enforces uniqueness
            await repository.save(lib2)

    @pytest.mark.asyncio
    async def test_repository_delete(self, repository, library_domain):
        """Test soft delete"""
        await repository.save(library_domain)

        await repository.delete(library_domain.id)

        retrieved = await repository.get_by_id(library_domain.id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_repository_get_nonexistent(self, repository):
        """Test retrieve non-existent library"""
        nonexistent_id = uuid4()

        retrieved = await repository.get_by_id(nonexistent_id)

        assert retrieved is None

    @pytest.mark.asyncio
    async def test_repository_list_all(self, repository, user_id):
        """Test list all libraries"""
        # Create libraries for different users
        lib1 = Library.create(user_id=user_id, name=LibraryName("Lib 1"))
        lib2_user_id = uuid4()
        lib2 = Library.create(user_id=lib2_user_id, name=LibraryName("Lib 2"))

        await repository.save(lib1)
        await repository.save(lib2)

        all_libs = await repository.get_all()

        assert len(all_libs) == 2
        assert any(lib.user_id == user_id for lib in all_libs)
        assert any(lib.user_id == lib2_user_id for lib in all_libs)

    @pytest.mark.asyncio
    async def test_repository_timestamps(self, repository, library_domain):
        """Test timestamps are set correctly"""
        before_save = datetime.now(timezone.utc)
        await repository.save(library_domain)
        after_save = datetime.now(timezone.utc)

        retrieved = await repository.get_by_id(library_domain.id)

        assert before_save <= retrieved.created_at <= after_save
        assert before_save <= retrieved.updated_at <= after_save
