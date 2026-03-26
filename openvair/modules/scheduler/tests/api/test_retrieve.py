"""API tests for retrieving scheduler jobs."""

from unittest.mock import patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient


def test_get_jobs_list(client: TestClient) -> None:
    """Successful job receiving via API (pagination)."""
    with patch(
        'openvair.modules.scheduler.entrypoints.api.SchedulerCrud.get_all_jobs'
    ) as mock_method:
        mock_method.return_value = []
        response = client.get("/scheduler/jobs")
        assert response.status_code == status.HTTP_200_OK
        assert "items" in response.json()["data"]

def test_get_job_by_id_success(client: TestClient) -> None:
    """Successful job receiving via API and it's ID"""
    job_id = "74a18c88-04b7-4d6a-a50a-c91203b234db"
    with patch(
        'openvair.modules.scheduler.entrypoints.api.SchedulerCrud.get_job'
    ) as mock_method:
        mock_method.return_value = {
            "id": job_id,
            "name": "test_job",
            "cron_schedule": "* * * * *",
            "command": "ls",
            "enabled": True,
            "created_at": "2024-05-28T10:45:21",
            "updated_at": None
        }
        response = client.get(f"/scheduler/jobs/{job_id}")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"]["id"] == job_id

def test_get_single_job_not_found(client: TestClient) -> None:
    """Receiving JobNotFoundError"""
    import uuid

    from openvair.modules.scheduler.service_layer.exceptions import (
        JobNotFoundError,
    )

    fake_id = str(uuid.uuid4())
    with patch(
        'openvair.modules.scheduler.entrypoints.api.SchedulerCrud.get_job'
    ) as mock_method:
        mock_method.side_effect = JobNotFoundError("Not found")
        with pytest.raises(JobNotFoundError):
            client.get(f"/scheduler/jobs/{fake_id}")
