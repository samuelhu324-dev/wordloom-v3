"""Book Tests"""
import pytest
from uuid import uuid4
from domains.book.domain import Book, BookTitle, BookSummary, BookStatus

@pytest.fixture
def sample_bookshelf_id():
    return uuid4()

@pytest.fixture
def book_domain_factory(sample_bookshelf_id):
    def _create(book_id=None, bookshelf_id=None, title="Test Book"):
        return Book(
            book_id=book_id or uuid4(),
            bookshelf_id=bookshelf_id or sample_bookshelf_id,
            title=BookTitle(value=title),
            summary=BookSummary(value=None),
        )
    return _create

@pytest.fixture
async def mock_book_repository():
    class MockBookRepository:
        def __init__(self):
            self.store = {}
        async def save(self, book: Book) -> None:
            self.store[book.id] = book
        async def get_by_id(self, book_id):
            return self.store.get(book_id)
        async def get_by_bookshelf_id(self, bookshelf_id):
            return [b for b in self.store.values() if b.bookshelf_id == bookshelf_id]
        async def delete(self, book_id) -> None:
            self.store.pop(book_id, None)
    return MockBookRepository()
