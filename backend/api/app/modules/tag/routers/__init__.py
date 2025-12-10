"""
Tag Routers - HTTP Adapter

FastAPI routers that expose use cases as REST endpoints.

Structure:
  routers/
  └── tag_router.py

Responsibilities:
  1. Parse HTTP requests → convert to input port DTO
  2. Call use case from DI container
  3. Convert output port DTO → HTTP response
  4. Handle exceptions → HTTP error responses
  5. Logging and observability

Routers have NO business logic, only HTTP translation.
"""
