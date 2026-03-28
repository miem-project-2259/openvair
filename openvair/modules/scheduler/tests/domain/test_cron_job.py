from __future__ import annotations

import datetime
import uuid

import pytest
from pydantic import ValidationError

from openvair.modules.scheduler.domain.exception import CronJobNotFound


def _make_create_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        'id': str(uuid.uuid4()),
        'name': 'job',
        'description': 'job descr',
        'cron_schedule': '* * * * *',
        'command': 'job.sh',
    }
    payload.update(overrides)
    return payload


def test_create_job_success_writes_to_cron(domain_scheduler) -> None:
    payload = _make_create_payload(name='backup', command='backup.sh', cron_schedule='*/5 * * * *')

    response = domain_scheduler.create(payload)
    job_id = response['job_id']

    assert response['message'] == 'Job successfully created'
    assert len(domain_scheduler._cron.items) == 1
    assert f'OPENVAIR_JOB_ID:[{job_id}]' in domain_scheduler._cron.items[0].comment


def test_create_job_with_unknown_before_job_id_is_ignored(domain_scheduler) -> None:
    domain_scheduler.create(_make_create_payload(name='first', command='first.sh'))

    response = domain_scheduler.create(
        _make_create_payload(
            name='second',
            command='second.sh',
            before_job_id=uuid.uuid4(),
        )
    )

    assert response['message'] == 'Job successfully created'
    assert len(domain_scheduler._cron.items) == 2
    assert domain_scheduler._cron.items[1].command == 'second.sh'


def test_get_job_success(domain_scheduler) -> None:
    job_id = str(uuid.uuid4())
    created_at = datetime.datetime(2026, 1, 1, 1, 0, 0)
    updated_at = datetime.datetime(2026, 1, 1, 2, 0, 0)
    domain_scheduler.create(
        _make_create_payload(
            id=job_id,
            name='fetch-me',
            description='readable descr',
            command='fetch.sh',
        )
    )

    result = domain_scheduler.get(
        {
            'id': job_id,
            'name': 'fetch-me',
            'before_job_id': None,
            'after_job_id': None,
            'created_at': created_at,
            'updated_at': updated_at,
        }
    )

    assert result['id'] == job_id
    assert result['name'] == 'fetch-me'
    assert result['description'] == 'readable descr'
    assert result['command'] == 'fetch.sh'
    assert result['enabled'] is True
    assert result['updated_at'] == updated_at.isoformat()


def test_get_job_invalid_uuid_raises_value_error(domain_scheduler) -> None:
    with pytest.raises(ValueError):
        domain_scheduler.get({'id': 'not-a-uuid'})


def test_get_job_not_found_raises(domain_scheduler) -> None:
    missing_id = str(uuid.uuid4())

    with pytest.raises(CronJobNotFound, match=missing_id):
        domain_scheduler.get({'id': missing_id})


def test_edit_job_updates_existing_fields(domain_scheduler) -> None:
    created = domain_scheduler.create(
        _make_create_payload(name='old-name', description='old descr', command='old.sh')
    )

    updated = domain_scheduler.edit(
        {
            'id': created['job_id'],
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


def test_edit_job_with_before_job_id_reorders_items(domain_scheduler) -> None:
    first = domain_scheduler.create(_make_create_payload(name='first', command='first.sh'))
    second = domain_scheduler.create(_make_create_payload(name='second', command='second.sh'))

    domain_scheduler.edit(
        {
            'id': second['job_id'],
            'name': 'second',
            'before_job_id': first['job_id'],
        }
    )

    assert domain_scheduler._cron.items[0].command == 'second.sh'


def test_edit_job_not_found_raises(domain_scheduler) -> None:
    with pytest.raises(CronJobNotFound):
        domain_scheduler.edit({'id': str(uuid.uuid4()), 'name': 'new-name'})


def test_delete_job_success(domain_scheduler) -> None:
    created = domain_scheduler.create(
        _make_create_payload(name='job', description='to delete', command='delete.sh')
    )

    domain_scheduler.delete({'job_id': created['job_id']})

    assert domain_scheduler._cron.items == []


def test_delete_missing_job_is_noop(domain_scheduler) -> None:
    domain_scheduler.create(_make_create_payload(name='job', command='keep.sh'))

    domain_scheduler.delete({'job_id': str(uuid.uuid4())})

    assert len(domain_scheduler._cron.items) == 1


def test_list_all_returns_jobs_dict(domain_scheduler) -> None:
    domain_scheduler.create(_make_create_payload(name='first', command='first.sh'))
    domain_scheduler.create(_make_create_payload(name='second', command='second.sh'))

    result = domain_scheduler.list_all()

    assert 'jobs' in result
    assert len(result['jobs']) == 2
    assert {job['name'] for job in result['jobs']} == {'Unknown'}


def test_list_all_merges_db_fields(domain_scheduler) -> None:
    created = domain_scheduler.create(_make_create_payload(name='first', command='first.sh'))
    created_at = datetime.datetime(2026, 1, 1, 3, 0, 0)

    result = domain_scheduler.list_all(
        {
            'jobs_from_db': [
                {
                    'id': created['job_id'],
                    'name': 'from-db',
                    'before_job_id': None,
                    'after_job_id': None,
                    'created_at': created_at,
                    'updated_at': None,
                }
            ]
        }
    )

    assert len(result['jobs']) == 1
    assert result['jobs'][0]['name'] == 'from-db'
    assert result['jobs'][0]['created_at'] == created_at.isoformat()


def test_list_all_ignores_malformed_ids(domain_scheduler, fake_cron) -> None:
    domain_scheduler.create(_make_create_payload(name='valid', command='valid.sh'))
    fake_cron.new(command='bad.sh', comment='bad OPENVAIR_JOB_ID:[not-a-uuid]')

    result = domain_scheduler.list_all()

    assert len(result['jobs']) == 1


def test_create_job_with_invalid_command_raises_validation_error(domain_scheduler) -> None:
    with pytest.raises(ValidationError):
        domain_scheduler.create(
            _make_create_payload(name='bad', description='Invalid command', command='rm -rf /')
        )


def test_edit_job_with_conflicting_dependencies_raises_validation_error(domain_scheduler) -> None:
    first = domain_scheduler.create(_make_create_payload(name='first', command='first.sh'))
    second = domain_scheduler.create(_make_create_payload(name='second', command='second.sh'))

    with pytest.raises(ValidationError):
        domain_scheduler.edit(
            {
                'id': second['job_id'],
                'before_job_id': first['job_id'],
                'after_job_id': first['job_id'],
            }
        )


