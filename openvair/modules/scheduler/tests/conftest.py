import uuid
import pytest
from unittest.mock import MagicMock, patch

# 1. Глобальные моки внешних систем (выполняются ПЕРВЫМИ)
# Патчим pika и MessagingClient, чтобы избежать AMQPConnectionError
patch('pika.BlockingConnection').start()
patch('openvair.libs.messaging.messaging_agents.MessagingClient').start()
# Патчим StaticFiles, чтобы не было ошибки из-за отсутствующей папки docs
patch('starlette.staticfiles.StaticFiles').start()

@pytest.fixture
def anyio_backend():
    """Фиксирует использование asyncio для anyio тестов"""
    return 'asyncio'

@pytest.fixture
def client():
    """Фикстура для FastAPI TestClient с подменой авторизации"""
    from openvair.main import app
    from openvair.libs.auth.jwt_utils import get_current_user
    from fastapi.testclient import TestClient

    def skip_auth():
        return {"user_id": str(uuid.uuid4()), "role": "admin"}
    
    app.dependency_overrides[get_current_user] = skip_auth
    with TestClient(app) as c:
        yield c
    # Очистка переопределений после теста
    app.dependency_overrides.clear()

@pytest.fixture(autouse=True)
def mock_uow():
    """Автоматический мок Unit of Work для всех тестов модуля"""
    with patch(
        'openvair.modules.scheduler.service_layer.services.SchedulerSqlAlchemyUnitOfWork'
    ) as mock:
        instance = mock.return_value
        # Настройка контекстного менеджера: with uow() as uow:
        instance.__enter__.return_value = instance
        instance.__exit__.return_value = None
        
        # По умолчанию считаем, что задач в базе нет
        instance.jobs.get_by_name.return_value = None
        
        # Имитируем SQLAlchemy refresh
        def mock_refresh(obj):
            if not getattr(obj, 'id', None):
                obj.id = uuid.uuid4()
        instance.session.refresh = mock_refresh
        
        yield instance