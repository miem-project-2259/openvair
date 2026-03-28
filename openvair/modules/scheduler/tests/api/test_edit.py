"""API tests for editing scheduler jobs."""

from unittest.mock import patch

from fastapi import status
from fastapi.testclient import TestClient


def test_edit_job_name(client: TestClient) -> None:
    """Successful job editing via API."""
    job_id = "74a18c88-04b7-4d6a-a50a-c91203b234db"

    with patch(
        'openvair.modules.scheduler.entrypoints.api.SchedulerCrud.edit_job'
    ) as mock_method:
        mock_method.return_value = {
            "id": job_id,
            "name": "new_name",
            "description": "Updated",
            "cron_schedule": "0 0 * * *",
            "command": "ls",
            "enabled": True,
            "created_at": "2024-05-28T10:45:21",
            "updated_at": "2024-05-28T12:00:00"
        }

        patch_payload = {"name": "new_name"}
        response = client.patch(f"/scheduler/{job_id}", json=patch_payload)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"]["name"] == "new_name"
