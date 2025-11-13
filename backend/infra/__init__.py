"""
Infra Layer - Infrastructure & Adapters

Hexagonal Architecture: This layer contains all external adapters and infrastructure
components. The domain layer has NO dependencies on this layer.

Structure:
  infra/
  ├── database/       - Database persistence adapters (ORM models, migrations)
  ├── storage/        - Repository implementations (adapters for domain ports)
  ├── event_bus/      - Event publishing infrastructure
  └── __init__.py

Key Principle:
  - Domain defines PORTS (interfaces in application/ports/)
  - Infra implements ADAPTERS (concrete implementations here)
  - Dependencies flow inward: Domain ← Application ← Infra
"""
