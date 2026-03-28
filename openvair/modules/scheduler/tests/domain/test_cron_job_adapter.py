from __future__ import annotations

from uuid import UUID

import pytest

from openvair.modules.scheduler.domain.exception import CronJobNotFound


def test_adapter_create_generates_uuid_and_tracks_metadata(adapter_scheduler) -> None:
    response = adapter_scheduler.create(
        {
            'name': 'adapter-job',
            'description': 'adapter',
            'cron_schedule': '* * * * *',
            'command': 'adapter.sh',
        }
    )

    job_id = UUID(response['job_id'])

    assert job_id in adapter_scheduler.jobs
    assert adapter_scheduler.jobs[job_id].name == 'adapter-job'


def test_adapter_get_accepts_raw_id_and_returns_uuid(adapter_scheduler) -> None:
    response = adapter_scheduler.create(
        {
            'name': 'adapter-job',
            'description': 'adapter',
            'cron_schedule': '* * * * *',
            'command': 'adapter.sh',
        }
    )

    fetched = adapter_scheduler.get(response['job_id'])

    assert isinstance(fetched['id'], UUID)


def test_adapter_delete_unknown_job_raises(adapter_scheduler) -> None:
    with pytest.raises(CronJobNotFound):
        adapter_scheduler.delete('5966db8e-df0f-4dc4-832c-13bda57dbf8c')


def test_adapter_list_all_returns_list(adapter_scheduler) -> None:
    adapter_scheduler.create(
        {
            'name': 'one',
            'description': 'first',
            'cron_schedule': '* * * * *',
            'command': 'one.sh',
        }
    )
    adapter_scheduler.create(
        {
            'name': 'two',
            'description': 'second',
            'cron_schedule': '* * * * *',
            'command': 'two.sh',
        }
    )

    result = adapter_scheduler.list_all()

    assert isinstance(result, list)
    assert len(result) == 2

