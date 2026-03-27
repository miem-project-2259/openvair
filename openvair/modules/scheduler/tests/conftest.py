"""Pytest configuration and fixtures for the scheduler module tests."""

import uuid
from typing import Any, Dict, Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# 1. Global mocks of external systems (executed FIRST)
# Patch pika and MessagingClient to avoid AMQPConnectionError
patch('pika.BlockingConnection').start()
patch('openvair.libs.messaging.messaging_agents.MessagingClient').start()
# Patch StaticFiles to avoid errors due to missing docs folder
patch('starlette.staticfiles.StaticFiles').start()


@pytest.fixture
def anyio_backend() -> str:
    """Fixate the use of asyncio for anyio tests."""
    return 'asyncio'


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Fixture for FastAPI TestClient with authorization override."""
    from openvair.main import app
    from openvair.libs.auth.jwt_utils import get_current_user

    def skip_auth() -> Dict[str, str]:
        return {"user_id": str(uuid.uuid4()), "role": "admin"}

    app.dependency_overrides[get_current_user] = skip_auth
    with TestClient(app) as c:
        yield c
    # Cleanup overrides after test
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def mock_uow() -> Generator[MagicMock, None, None]:
    """Automatic Unit of Work mock for all tests in the module."""
    with patch(
        'openvair.modules.scheduler.service_layer.services.SchedulerSqlAlchemyUnitOfWork'
    ) as mock:
        instance = mock.return_value
        # Context manager setup: with uow() as uow:
        instance.__enter__.return_value = instance
        instance.__exit__.return_value = None

        # By default, assume there are no jobs in the database
        instance.jobs.get_by_name.return_value = None

        # Simulate SQLAlchemy refresh
        def mock_refresh(obj: Any) -> None: # noqa: ANN401
            if not getattr(obj, 'id', None):
                obj.id = uuid.uuid4()

        instance.session.refresh = mock_refresh

        yield instance
