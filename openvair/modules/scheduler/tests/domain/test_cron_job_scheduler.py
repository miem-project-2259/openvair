"""Unit tests for CronJobScheduler domain layer.

Covers all possible scenarios for:
- create()
- get()
- edit()
- delete()
- list_all()

Uses a _FakeCronTab stub instead of the real system crontab so the tests
are self-contained and do not require cron access.
"""

from __future__ import annotations  # чтобы не ругался на типы, которых "ещё нет"

import uuid
from typing import Any, Optional
from uuid import UUID

import pytest
from pydantic import ValidationError

from openvair.modules.scheduler.domain.cron_jobs.cron_job import CronJobScheduler
from openvair.modules.scheduler.domain.exception import CronJobNotFound


# ---------------------------------------------------------------------------
# Fake crontab infrastructure
# ---------------------------------------------------------------------------


class _FakeCronSchedule:
    """Minimal schedule stub returned by _FakeCronItem.schedule()."""

    def get_last(self) -> None:
        return None

    def get_next(self) -> None:
        return None


class _FakeCronSlices:
    """Minimal slices stub so that str(job.slices) works."""

    def __init__(self, schedule: str = '* * * * *') -> None:
        self._schedule = schedule

    def __str__(self) -> str:
        return self._schedule


class _FakeCronItem:
    """Minimal CronItem stub that satisfies CronJobScheduler usage."""

    def __init__(self, command: str, comment: str = '') -> None:
        self.command = command
        self.comment = comment
        self.slices: _FakeCronSlices = _FakeCronSlices()
        self._enabled: bool = True

    def setall(self, schedule: str) -> None:
        self.slices = _FakeCronSlices(schedule)

    def schedule(self) -> _FakeCronSchedule:
        return _FakeCronSchedule()

    def is_enabled(self) -> bool:
        return self._enabled

    def set_command(self, command: str) -> None:
        self.command = command

    def set_comment(self, comment: str) -> None:
        self.comment = comment


class _FakeCronTab:
    """Minimal CronTab stub that acts as a context manager and tracks jobs."""

    def __init__(self) -> None:
        self._items: list[_FakeCronItem] = []

    def __enter__(self) -> _FakeCronTab:
        return self

    def __exit__(self, *exc: Any) -> None:
        pass

    def new(
        self,
        command: str,
        comment: str = '',
        before: Optional[_FakeCronItem] = None,
    ) -> _FakeCronItem:
        item = _FakeCronItem(command, comment)
        self._items.append(item)
        return item

    def remove(self, item: _FakeCronItem) -> None:
        if item in self._items:
            self._items.remove(item)


# ---------------------------------------------------------------------------
# Helpers & fixtures
# ---------------------------------------------------------------------------

_VALID_COMMAND = 'backup.sh'
_VALID_SCHEDULE = '0 3 * * *'
_VALID_NAME = 'daily_backup'


def _make_scheduler() -> CronJobScheduler:
    return CronJobScheduler(cron_obj=_FakeCronTab())  # type: ignore[arg-type]


def _create_job(
    scheduler: CronJobScheduler,
    *,
    name: str = _VALID_NAME,
    command: str = _VALID_COMMAND,
    schedule: str = _VALID_SCHEDULE,
    description: Optional[str] = 'some description',
    before_job_id: Optional[UUID] = None,
) -> UUID:
    """Helper: create a job and return its UUID."""
    result = scheduler.create(
        {
            'name': name,
            'command': command,
            'cron_schedule': schedule,
            'description': description,
            'before_job_id': before_job_id,
            'after_job_id': None,
        }
    )
    return result['job_id']


# ---------------------------------------------------------------------------
# create() tests
# ---------------------------------------------------------------------------


def test_create_job_returns_job_id() -> None:
    """create() returns a dict with a valid UUID job_id."""
    scheduler = _make_scheduler()
    result = scheduler.create(
        {
            'name': _VALID_NAME,
            'command': _VALID_COMMAND,
            'cron_schedule': _VALID_SCHEDULE,
            'description': None,
            'before_job_id': None,
            'after_job_id': None,
        }
    )
    assert 'job_id' in result
    assert isinstance(result['job_id'], UUID)


def test_create_job_registers_in_scheduler() -> None:
    """The new job is stored inside scheduler.jobs after creation."""
    scheduler = _make_scheduler()
    job_id = _create_job(scheduler)
    assert job_id in scheduler.jobs


def test_create_job_stores_correct_name() -> None:
    """The stored JobMetadata has the name supplied at creation time."""
    scheduler = _make_scheduler()
    job_id = _create_job(scheduler, name='my_job')
    assert scheduler.jobs[job_id].name == 'my_job'


def test_create_job_with_before_job_id() -> None:
    """Creating a job with before_job_id links next_id correctly."""
    scheduler = _make_scheduler()
    first_id = _create_job(scheduler, name='first')
    second_id = _create_job(scheduler, name='second', before_job_id=first_id)

    # second job must know it precedes first
    assert scheduler.jobs[second_id].next_id == first_id


def test_create_job_with_before_sets_previous_id_on_target() -> None:
    """The referenced job's previous_id is updated to the new job's id."""
    scheduler = _make_scheduler()
    first_id = _create_job(scheduler, name='first')
    second_id = _create_job(scheduler, name='second', before_job_id=first_id)

    assert scheduler.jobs[first_id].previous_id == second_id


def test_create_job_nonexistent_before_raises() -> None:
    """CronJobNotFound is raised when before_job_id is unknown."""
    scheduler = _make_scheduler()
    with pytest.raises(CronJobNotFound):
        _create_job(scheduler, before_job_id=uuid.uuid4())


def test_create_job_invalid_command_no_sh_suffix() -> None:
    """ValidationError is raised for a command without .sh suffix."""
    scheduler = _make_scheduler()
    with pytest.raises((ValidationError, ValueError)):
        scheduler.create(
            {
                'name': _VALID_NAME,
                'command': 'backup',
                'cron_schedule': _VALID_SCHEDULE,
                'description': None,
                'before_job_id': None,
                'after_job_id': None,
            }
        )


def test_create_job_invalid_command_forbidden_chars() -> None:
    """ValidationError is raised for a command with forbidden shell chars."""
    scheduler = _make_scheduler()
    with pytest.raises((ValidationError, ValueError)):
        scheduler.create(
            {
                'name': _VALID_NAME,
                'command': 'backup.sh; rm -rf /',
                'cron_schedule': _VALID_SCHEDULE,
                'description': None,
                'before_job_id': None,
                'after_job_id': None,
            }
        )


def test_create_job_invalid_cron_schedule() -> None:
    """ValidationError is raised for a malformed cron expression."""
    scheduler = _make_scheduler()
    with pytest.raises((ValidationError, ValueError)):
        scheduler.create(
            {
                'name': _VALID_NAME,
                'command': _VALID_COMMAND,
                'cron_schedule': 'not-a-cron',
                'description': None,
                'before_job_id': None,
                'after_job_id': None,
            }
        )


def test_create_job_empty_name_raises() -> None:
    """ValidationError is raised when name is empty or whitespace-only."""
    scheduler = _make_scheduler()
    with pytest.raises((ValidationError, ValueError)):
        scheduler.create(
            {
                'name': '   ',
                'command': _VALID_COMMAND,
                'cron_schedule': _VALID_SCHEDULE,
                'description': None,
                'before_job_id': None,
                'after_job_id': None,
            }
        )


def test_create_job_both_before_and_after_raises() -> None:
    """ValidationError is raised when both before_job_id and after_job_id are set."""
    scheduler = _make_scheduler()
    some_id = uuid.uuid4()
    other_id = uuid.uuid4()
    with pytest.raises((ValidationError, ValueError)):
        scheduler.create(
            {
                'name': _VALID_NAME,
                'command': _VALID_COMMAND,
                'cron_schedule': _VALID_SCHEDULE,
                'description': None,
                'before_job_id': some_id,
                'after_job_id': other_id,
            }
        )


# ---------------------------------------------------------------------------
# get() tests
# ---------------------------------------------------------------------------


def test_get_existing_job_returns_dict() -> None:
    """get() returns a dict with the expected keys for a known job."""
    scheduler = _make_scheduler()
    job_id = _create_job(scheduler)
    result = scheduler.get(str(job_id))

    assert isinstance(result, dict)
    assert result['id'] == job_id
    assert result['name'] == _VALID_NAME
    assert result['command'] == _VALID_COMMAND
    assert result['cron_schedule'] == _VALID_SCHEDULE


def test_get_existing_job_enabled_by_default() -> None:
    """Newly created jobs are enabled."""
    scheduler = _make_scheduler()
    job_id = _create_job(scheduler)
    result = scheduler.get(str(job_id))
    assert result['enabled'] is True


def test_get_existing_job_updated_at_is_none_initially() -> None:
    """A freshly created job has updated_at=None."""
    scheduler = _make_scheduler()
    job_id = _create_job(scheduler)
    result = scheduler.get(str(job_id))
    assert result['updated_at'] is None


def test_get_nonexistent_job_raises() -> None:
    """get() raises CronJobNotFound for an unknown job UUID."""
    scheduler = _make_scheduler()
    with pytest.raises(CronJobNotFound):
        scheduler.get(str(uuid.uuid4()))


def test_get_invalid_uuid_raises() -> None:
    """get() raises ValueError when passed a non-UUID string."""
    scheduler = _make_scheduler()
    with pytest.raises(ValueError):
        scheduler.get('not-a-uuid')


# ---------------------------------------------------------------------------
# edit() tests
# ---------------------------------------------------------------------------


def test_edit_job_updates_command() -> None:
    """edit() updates the command field of an existing job."""
    scheduler = _make_scheduler()
    job_id = _create_job(scheduler)
    result = scheduler.edit(
        {
            'job_id': str(job_id),
            'command': 'new_backup.sh',
        }
    )
    assert result['command'] == 'new_backup.sh'


def test_edit_job_updates_schedule() -> None:
    """edit() updates the cron_schedule of an existing job."""
    scheduler = _make_scheduler()
    job_id = _create_job(scheduler)
    result = scheduler.edit(
        {
            'job_id': str(job_id),
            'cron_schedule': '0 5 * * *',
        }
    )
    assert result['cron_schedule'] == '0 5 * * *'


def test_edit_job_updates_name() -> None:
    """edit() updates the name of an existing job."""
    scheduler = _make_scheduler()
    job_id = _create_job(scheduler)
    scheduler.edit(
        {
            'job_id': str(job_id),
            'name': 'renamed_job',
        }
    )
    assert scheduler.jobs[job_id].name == 'renamed_job'


def test_edit_job_updates_description() -> None:
    """edit() updates the description (comment) of an existing job."""
    scheduler = _make_scheduler()
    job_id = _create_job(scheduler)
    scheduler.edit(
        {
            'job_id': str(job_id),
            'description': 'new description',
        }
    )
    assert scheduler.jobs[job_id].cron_item.comment == 'new description'


def test_edit_job_sets_updated_at() -> None:
    """edit() sets updated_at on the job metadata."""
    scheduler = _make_scheduler()
    job_id = _create_job(scheduler)
    result = scheduler.edit(
        {
            'job_id': str(job_id),
            'name': 'updated_name',
        }
    )
    assert result['updated_at'] is not None


def test_edit_nonexistent_job_raises() -> None:
    """edit() raises CronJobNotFound for an unknown job UUID."""
    scheduler = _make_scheduler()
    with pytest.raises(CronJobNotFound):
        scheduler.edit(
            {
                'job_id': str(uuid.uuid4()),
                'name': 'new_name',
            }
        )


def test_edit_job_with_before_job_id_repositions() -> None:
    """edit() with before_job_id replaces the cron item and links the chain."""
    scheduler = _make_scheduler()
    anchor_id = _create_job(scheduler, name='anchor')
    target_id = _create_job(scheduler, name='target')

    scheduler.edit(
        {
            'job_id': str(target_id),
            'before_job_id': anchor_id,
        }
    )

    # The target job must record that it now precedes anchor
    assert scheduler.jobs[target_id].next_id == anchor_id
    # The anchor job must record that target precedes it
    assert scheduler.jobs[anchor_id].previous_id == target_id
    # The cron item was replaced (new object, still tracked in fake crontab)
    assert scheduler.jobs[target_id].cron_item is not None


# ---------------------------------------------------------------------------
# delete() tests
# ---------------------------------------------------------------------------


def test_delete_existing_job_removes_from_scheduler() -> None:
    """delete() removes the job from scheduler.jobs."""
    scheduler = _make_scheduler()
    job_id = _create_job(scheduler)
    scheduler.delete(str(job_id))
    assert job_id not in scheduler.jobs


def test_delete_existing_job_removes_from_crontab() -> None:
    """delete() removes the cron item from the underlying fake crontab."""
    fake_cron = _FakeCronTab()
    scheduler = CronJobScheduler(cron_obj=fake_cron)  # type: ignore[arg-type]
    job_id = _create_job(scheduler)
    cron_item = scheduler.jobs[job_id].cron_item
    scheduler.delete(str(job_id))
    assert cron_item not in fake_cron._items


def test_delete_nonexistent_job_raises() -> None:
    """delete() raises CronJobNotFound for an unknown job UUID."""
    scheduler = _make_scheduler()
    with pytest.raises(CronJobNotFound):
        scheduler.delete(str(uuid.uuid4()))


def test_delete_invalid_uuid_raises() -> None:
    """delete() raises ValueError for a non-UUID string."""
    scheduler = _make_scheduler()
    with pytest.raises(ValueError):
        scheduler.delete('not-a-uuid')


def test_double_delete_raises() -> None:
    """Deleting the same job twice raises CronJobNotFound the second time."""
    scheduler = _make_scheduler()
    job_id = _create_job(scheduler)
    scheduler.delete(str(job_id))
    with pytest.raises(CronJobNotFound):
        scheduler.delete(str(job_id))


# ---------------------------------------------------------------------------
# list_all() tests
# ---------------------------------------------------------------------------


def test_list_all_empty_scheduler() -> None:
    """list_all() returns an empty list when no jobs have been created."""
    scheduler = _make_scheduler()
    assert scheduler.list_all() == []


def test_list_all_single_job() -> None:
    """list_all() returns a one-element list after a single job is created."""
    scheduler = _make_scheduler()
    job_id = _create_job(scheduler)
    jobs = scheduler.list_all()
    assert len(jobs) == 1
    assert jobs[0]['id'] == job_id


def test_list_all_multiple_jobs() -> None:
    """list_all() returns all jobs that have been created."""
    scheduler = _make_scheduler()
    ids = {_create_job(scheduler, name=f'job_{i}') for i in range(3)}
    jobs = scheduler.list_all()
    assert len(jobs) == 3
    assert {j['id'] for j in jobs} == ids


def test_list_all_after_delete() -> None:
    """list_all() no longer includes a job after it has been deleted."""
    scheduler = _make_scheduler()
    job_id = _create_job(scheduler)
    scheduler.delete(str(job_id))
    assert scheduler.list_all() == []
