"""Unit tests for the scheduler service layer."""

import uuid
from unittest.mock import MagicMock

from openvair.modules.scheduler.service_layer.services import (
    SchedulerServiceLayerManager,
)


def test_create_job_service_logic(mock_uow: MagicMock) -> None:
    """Проверка логики создания задачи в сервис-слое."""
    manager = SchedulerServiceLayerManager()
    manager.domain_rpc = MagicMock()

    data = {
        "name": "service_test_job",
        "cron_schedule": "*/5 * * * *",
        "command": "ls",
        "enabled": True
    }

    result = manager.create_job(data)

    assert result["name"] == "service_test_job"
    assert mock_uow.jobs.add.called
    assert mock_uow.commit.called
    assert manager.domain_rpc.call.called


def test_delete_job_service_logic(mock_uow: MagicMock) -> None:
    """Проверка логики удаления задачи в сервис-слое."""
    manager = SchedulerServiceLayerManager()
    manager.domain_rpc = MagicMock()

    job_id = uuid.uuid4()
    mock_job = MagicMock(id=job_id)
    mock_uow.jobs.get_by_id.return_value = mock_job

    payload = {"id": job_id}
    result = manager.delete_job(payload)

    assert str(result["id"]) == str(job_id)
    assert mock_uow.jobs.delete.called
    assert mock_uow.commit.called
