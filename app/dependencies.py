# -*- coding: utf-8 -*-
# =============================================================================
# dependencies.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
Dependency injection for nsis FastAPI application.
Manages service instances and provides dependency functions using a service container.
"""

from typing import Dict, Any
from app.config import settings


class ServiceContainer:
    """
    Service container for dependency injection.
    Manages service instances and provides dependency functions.
    """

    def __init__(self):
        """Initialize an empty service container."""
        self._services: Dict[str, Any] = {}

    def register(self, name: str, instance: Any) -> None:
        """
        Register a service instance with the container.

        Args:
            name: Name of the service
            instance: Service instance
        """
        self._services[name] = instance

    def get(self, name: str) -> Any:
        """
        Get a service instance by name.

        Args:
            name: Name of the service

        Returns:
            Service instance or None if not found
        """
        return self._services.get(name)

    def clear(self) -> None:
        """Clear all registered services."""
        self._services.clear()


# Create a global service container instance
container = ServiceContainer()


def get_settings():
    """Get application settings."""
    return settings


def get_milvus_service():
    """Get Milvus service instance."""
    return container.get('milvus_service')


def get_vufind_service():
    """Get VuFind service instance."""
    return container.get('vufind_service')


def get_transformation_service():
    """Get Transformation service instance."""
    return container.get('transformation_service')


async def initialize_services():
    """
    Initialize all services at application startup.
    This function is called during FastAPI startup event.
    """
    # Import services here to avoid circular imports
    from app.services.milvus_service import MilvusService
    from app.services.vufind_service import VuFindService
    from app.services.transformation_service import TransformationService

    from app.utils.dev_print import DevPrint

    DevPrint.start("Initializing services...")

    # Initialize Milvus service (this will load the databases)
    milvus_service = MilvusService(
        device=settings.milvus_device,
        bk_db_path=settings.milvus_bk_db_path,
        bk_csv_path=settings.milvus_bk_csv_path,
        gnd_saz_head_db_path=settings.milvus_gnd_saz_head_db_path,
        gnd_saz_head_csv_path=settings.milvus_gnd_saz_head_csv_path,
        gnd_saz_desc_db_path=settings.milvus_gnd_saz_desc_db_path,
        gnd_saz_desc_csv_path=settings.milvus_gnd_saz_desc_csv_path,
        gnd_geo_db_path=settings.milvus_gnd_geo_db_path,
        gnd_geo_csv_path=settings.milvus_gnd_geo_csv_path,
    )
    await milvus_service.initialize()

    # Initialize VuFind service
    vufind_service = VuFindService()

    # Initialize Transformation service
    transformation_service = TransformationService(
        milvus_service=milvus_service,
    )

    # Register services with the container
    container.register('milvus_service', milvus_service)
    container.register('vufind_service', vufind_service)
    container.register('transformation_service', transformation_service)

    DevPrint.success("All services initialized successfully.")


async def shutdown_services():
    """
    Shutdown all services at application shutdown.
    This function is called during FastAPI shutdown event.
    """
    from app.utils.dev_print import DevPrint

    DevPrint.info("Shutting down services...")

    milvus_service = container.get('milvus_service')
    if milvus_service:
        await milvus_service.shutdown()

    # Clear all services from the container
    container.clear()

    DevPrint.success("All services shut down successfully.")
