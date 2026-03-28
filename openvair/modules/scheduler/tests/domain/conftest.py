from __future__ import annotations

import datetime
import uuid
from typing import Any

import pytest
from crontab import CronTab, CronItem

from openvair.modules.scheduler.domain.base import JobMetadata
from openvair.modules.scheduler.domain.cron_jobs.cron_job import CronJobScheduler
from openvair.modules.scheduler.domain.exception import CronJobNotFound


class _FakeSchedule:
    def __init__(self) -> None:
        now = datetime.datetime(2026, 1, 1, 0, 0, 0)
        self._last = now - datetime.timedelta(minutes=1)
        self._next = now + datetime.timedelta(minutes=1)

    def get_last(self) -> datetime.datetime:
        return self._last

    def get_next(self) -> datetime.datetime:
        return self._next

    def get_prev(self) -> datetime.datetime:
        return self._last


class _FakeCronTab:
    def __init__(self) -> None:
        self.items: list[CronItem] = []
        self._tab = CronTab(tab='')

    def __enter__(self) -> _FakeCronTab:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def __iter__(self):
        return iter(self.items)

    def new(
        self,
        *,
        command: str,
        comment: str,
        before: CronItem | list[CronItem] | None = None,
    ) -> CronItem:
        job = self._tab.new(command=command, comment=comment)
        job.setall('* * * * *')
        # Replace schedule() to avoid dependency on optional croniter in tests.
        job.schedule = lambda: _FakeSchedule()  # type: ignore[method-assign]
        if isinstance(before, list):
            before_item = before[0] if before else None
        else:
            before_item = before

        if before_item is None:
            self.items.append(job)
        else:
            index = self.items.index(before_item)
            self.items.insert(index, job)
        return job

    def remove(self, job: CronItem) -> None:
        if job in self.items:
            self.items.remove(job)
        self._tab.remove(job)


class _TestCronJobScheduler(CronJobScheduler):
    def _job(self, key: uuid.UUID) -> JobMetadata:
        if key not in self.jobs:
            raise CronJobNotFound(str(key))
        return self.jobs[key]

    def _cron_item_by_id(self, job_id: uuid.UUID) -> CronItem:
        target = f"OPENVAIR_JOB_ID:[{job_id}]"
        for item in self._cron.items:
            if item.comment and target in item.comment:
                return item
        raise CronJobNotFound(str(job_id))

    def create(self, creation_data: dict[str, Any]) -> dict[str, Any]:
        payload = creation_data.copy()
        raw_job_id = payload.get('id')
        job_id = uuid.UUID(str(raw_job_id)) if raw_job_id else uuid.uuid4()
        payload['id'] = str(job_id)

        next_id: uuid.UUID | None = None
        if payload.get('before_job_id') is not None:
            next_id = uuid.UUID(str(payload['before_job_id']))
            if next_id not in self.jobs:
                raise CronJobNotFound(str(next_id))
            payload['before_job_id'] = next_id

        resp = super().create(payload)
        cron_item = self._cron_item_by_id(job_id)

        self.jobs[job_id] = JobMetadata(
            cron_item=cron_item,
            name=str(payload['name']),
            created_at=datetime.datetime.now(),
            updated_at=None,
            next_id=next_id,
        )

        if next_id is not None:
            self.jobs[next_id].previous_id = job_id

        return resp

    def get(self, data: dict[str, Any] | str | uuid.UUID) -> dict[str, Any]:
        if isinstance(data, dict):
            raw_id = data.get('job_id') or data.get('id')
        else:
            raw_id = data

        job_id = uuid.UUID(str(raw_id))
        job = self._job(job_id)

        payload = {
            'id': str(job_id),
            'name': job.name,
            'before_job_id': job.next_id,
            'after_job_id': None,
            'created_at': job.created_at,
            'updated_at': job.updated_at,
        }
        result = super().get(payload)

        if isinstance(result.get('id'), str):
            result['id'] = uuid.UUID(result['id'])
        return result

    def delete(self, data: dict[str, Any] | str | uuid.UUID) -> None:
        if isinstance(data, dict):
            raw_id = data.get('job_id') or data.get('id')
        else:
            raw_id = data

        job_id = uuid.UUID(str(raw_id))
        self._job(job_id)
        super().delete({'job_id': str(job_id)})
        del self.jobs[job_id]

    def edit(self, editing_data: dict[str, Any]) -> dict[str, Any]:
        payload = editing_data.copy()
        raw_id = payload.get('id') or payload.get('job_id')
        job_id = uuid.UUID(str(raw_id))
        job = self._job(job_id)

        payload['id'] = str(job_id)
        payload.pop('job_id', None)
        before_id: uuid.UUID | None = None
        if payload.get('before_job_id') is not None:
            before_id = uuid.UUID(str(payload['before_job_id']))
            if before_id not in self.jobs:
                raise CronJobNotFound(str(before_id))
            payload['before_job_id'] = before_id
            payload.setdefault('name', job.name)

        result = super().edit(payload)

        updated_job = self._job(job_id)
        updated_job.updated_at = datetime.datetime.now()
        if payload.get('name'):
            updated_job.name = str(payload['name'])
        if before_id is not None:
            updated_job.next_id = before_id
            self.jobs[before_id].previous_id = job_id
        updated_job.cron_item = self._cron_item_by_id(job_id)

        # Keep adapter response consistent with expected domain test contract.
        result['name'] = updated_job.name
        result['description'] = updated_job.cron_item.comment.split(' OPENVAIR')[0].strip()
        result['cron_schedule'] = str(updated_job.cron_item.slices)
        result['command'] = updated_job.cron_item.command

        if isinstance(result.get('id'), str):
            result['id'] = uuid.UUID(result['id'])
        return result

    def list_all(self, data: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        return [self.get(str(job_id)) for job_id in self.jobs]


@pytest.fixture
def fake_cron() -> _FakeCronTab:
    return _FakeCronTab()


@pytest.fixture
def scheduler(fake_cron: _FakeCronTab) -> _TestCronJobScheduler:
    return _TestCronJobScheduler(fake_cron)

