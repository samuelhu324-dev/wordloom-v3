"""
Dependency Injection Container

Provides centralized dependency management and factory methods for all UseCase instances.
"""

from typing import Dict, Any, Type, TypeVar, Callable
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class DIContainer:
    """
    Dependency Injection Container

    Manages lifecycle of services, repositories, and use cases.
    Implements singleton and transient patterns.
    """

    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}

    def register(self, name: str, service: Any) -> None:
        """Register a singleton service"""
        self._services[name] = service

    def register_factory(self, name: str, factory: Callable) -> None:
        """Register a factory function"""
        self._factories[name] = factory

    def get(self, name: str) -> Any:
        """Get a service or call factory"""
        if name in self._services:
            return self._services[name]

        if name in self._factories:
            return self._factories[name]()

        raise KeyError(f"Service '{name}' not found in DI container")

    def clear(self) -> None:
        """Clear all services"""
        self._services.clear()
        self._factories.clear()


# Global container instance
_container: DIContainer | None = None


def get_di_container() -> DIContainer:
    """Get or create the global DI container"""
    global _container
    if _container is None:
        _container = DIContainer()
    return _container


def get_di_container_provider():
    """
    FastAPI dependency provider for DI container

    Usage in routers:
        @router.get("/items")
        async def get_items(
            di: DIContainer = Depends(get_di_container_provider)
        ):
            ...
    """
    return get_di_container()
