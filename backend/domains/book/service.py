"""Book Service"""
from typing import List
from uuid import UUID
from domains.book.domain import Book, BookStatus
from domains.book.repository import BookRepository

class BookService:
    def __init__(self, repository: BookRepository):
        self.repository = repository

    async def create_book(self, bookshelf_id: UUID, title: str, summary: str = None) -> Book:
        book = Book.create(bookshelf_id=bookshelf_id, title=title, summary=summary)
        await self.repository.save(book)
        return book

    async def get_book(self, book_id: UUID) -> Book:
        book = await self.repository.get_by_id(book_id)
        if not book:
            raise Exception(f"Book {book_id} not found")
        return book

    async def list_books(self, bookshelf_id: UUID) -> List[Book]:
        return await self.repository.get_by_bookshelf_id(bookshelf_id)

    async def rename_book(self, book_id: UUID, new_title: str) -> Book:
        book = await self.get_book(book_id)
        book.rename(new_title)
        await self.repository.save(book)
        return book

    async def publish_book(self, book_id: UUID) -> Book:
        book = await self.get_book(book_id)
        book.publish()
        await self.repository.save(book)
        return book

    async def delete_book(self, book_id: UUID) -> None:
        book = await self.get_book(book_id)
        book.mark_deleted()
        await self.repository.save(book)
        await self.repository.delete(book_id)
