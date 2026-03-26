from __future__ import annotations

import datetime
import uuid

import pytest
from pydantic import ValidationError

from openvair.modules.scheduler.domain.exception import CronJobNotFound


def test_create_job_success(scheduler) -> None:
    payload = {
        'name': 'backup',
        'description': 'Backup job',
        'cron_schedule': '*/5 * * * *',
        'command': 'backup.sh',
    }

    response = scheduler.create(payload)
    job_id = uuid.UUID(response['job_id'])

    assert response['message'] == 'Job successfully created'
    assert job_id in scheduler.jobs
    assert len(scheduler.jobs) == 1
    assert len(scheduler._cron.items) == 1


def test_create_job_with_before_job_id_links_chain(scheduler) -> None:
    first = scheduler.create(
        {
            'name': 'first',
            'description': 'First job',
            'cron_schedule': '* * * * *',
            'command': 'first.sh',
        }
    )
    first_id = uuid.UUID(first['job_id'])

    second = scheduler.create(
        {
            'name': 'second',
            'description': 'Second job',
            'cron_schedule': '*/2 * * * *',
            'command': 'second.sh',
            'before_job_id': first_id,
        }
    )
    second_id = uuid.UUID(second['job_id'])

    assert scheduler.jobs[first_id].previous_id == second_id
    assert scheduler.jobs[second_id].next_id == first_id
    assert scheduler._cron.items[0].command == 'second.sh'


def test_create_job_with_unknown_before_job_id_raises(scheduler) -> None:
    with pytest.raises(CronJobNotFound):
        scheduler.create(
            {
                'name': 'bad',
                'description': 'Unknown dependency',
                'cron_schedule': '* * * * *',
                'command': 'bad.sh',
                'before_job_id': uuid.uuid4(),
            }
        )


def test_get_job_success_when_updated_at_present(scheduler) -> None:
    created = scheduler.create(
        {
            'name': 'job',
            'description': 'job descr',
            'cron_schedule': '* * * * *',
            'command': 'job.sh',
        }
    )
    job_id = uuid.UUID(created['job_id'])
    scheduler.jobs[job_id].updated_at = datetime.datetime(2026, 1, 1, 1, 0, 0)

    result = scheduler.get(str(job_id))

    assert result['id'] == str(job_id)
    assert result['name'] == 'job'
    assert result['description'] == 'job descr'
    assert result['command'] == 'job.sh'
    assert result['enabled'] is True


def test_get_job_without_updated_at_raises_validation_error(scheduler) -> None:
    created = scheduler.create(
        {
            'name': 'job',
            'description': 'job descr',
            'cron_schedule': '* * * * *',
            'command': 'job.sh',
        }
    )

    with pytest.raises(ValidationError):
        scheduler.get(created['job_id'])


def test_get_job_invalid_uuid_raises_value_error(scheduler) -> None:
    with pytest.raises(ValueError):
        scheduler.get('not-a-uuid')


def test_get_job_not_found_raises(scheduler) -> None:
    missing_id = str(uuid.uuid4())

    with pytest.raises(CronJobNotFound, match=missing_id):
        scheduler.get(missing_id)


def test_edit_job_updates_existing_fields(scheduler) -> None:
    created = scheduler.create(
        {
            'name': 'old-name',
            'description': 'old descr',
            'cron_schedule': '* * * * *',
            'command': 'old.sh',
        }
    )
    job_id = created['job_id']

    updated = scheduler.edit(
        {
            'job_id': job_id,
            'name': 'new-name',
            'description': 'new descr',
            'cron_schedule': '*/15 * * * *',
            'command': 'new.sh',
        }
    )

    assert updated['name'] == 'new-name'
    assert updated['description'] == 'new descr'
    assert updated['cron_schedule'] == '*/15 * * * *'
    assert updated['command'] == 'new.sh'


def test_edit_job_with_before_job_id_recreates_cron_item(scheduler) -> None:
    first = scheduler.create(
        {
            'name': 'first',
            'description': 'first',
            'cron_schedule': '* * * * *',
            'command': 'first.sh',
        }
    )
    second = scheduler.create(
        {
            'name': 'second',
            'description': 'second',
            'cron_schedule': '*/2 * * * *',
            'command': 'second.sh',
        }
    )

    second_id = uuid.UUID(second['job_id'])
    old_item = scheduler.jobs[second_id].cron_item

    scheduler.edit({'job_id': second['job_id'], 'before_job_id': uuid.UUID(first['job_id'])})

    assert scheduler.jobs[second_id].cron_item is not old_item
    assert scheduler._cron.items[0].command == 'second.sh'


def test_edit_job_not_found_raises(scheduler) -> None:
    with pytest.raises(CronJobNotFound):
        scheduler.edit({'job_id': str(uuid.uuid4()), 'name': 'new-name'})


def test_delete_job_success(scheduler) -> None:
    created = scheduler.create(
        {
            'name': 'job',
            'description': 'to delete',
            'cron_schedule': '* * * * *',
            'command': 'delete.sh',
        }
    )
    job_id = created['job_id']

    scheduler.delete(job_id)

    assert scheduler.jobs == {}
    assert scheduler._cron.items == []


def test_delete_job_invalid_uuid_raises_value_error(scheduler) -> None:
    with pytest.raises(ValueError):
        scheduler.delete('not-a-uuid')


def test_delete_job_not_found_raises(scheduler) -> None:
    with pytest.raises(CronJobNotFound):
        scheduler.delete(str(uuid.uuid4()))

