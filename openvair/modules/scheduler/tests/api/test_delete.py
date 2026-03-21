import pytest
from fastapi import status
from unittest.mock import patch

def test_delete_job_success(client):
    """Успешное удаление задачи через API"""
    job_id = "74a18c88-04b7-4d6a-a50a-c91203b234db"
    
    with patch(
        'openvair.modules.scheduler.entrypoints.api.SchedulerCrud.delete_job'
    ) as mock_method:
        mock_method.return_value = {
            "id": job_id,
            "name": "deleted_job",
            "cron_schedule": "0 0 * * *",
            "command": "ls",
            "enabled": True,
            "created_at": "2024-05-28T10:45:21",
            "updated_at": None
        }

        # Согласно api.py: @router.delete('/{job_id}')
        response = client.delete(f"/scheduler/{job_id}")
        
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.json()["data"]["id"] == job_id