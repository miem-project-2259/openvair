from __future__ import annotations

import datetime
from typing import Any

import pytest
from crontab import CronTab, CronItem

from openvair.modules.scheduler.domain.cron_jobs.cron_job import CronJobScheduler


class _FakeSchedule:
    def __init__(self) -> None:
        now = datetime.datetime(2026, 1, 1, 0, 0, 0)
        self._last = now - datetime.timedelta(minutes=1)
        self._next = now + datetime.timedelta(minutes=1)

    def get_last(self) -> datetime.datetime:
        return self._last

    def get_next(self) -> datetime.datetime:
        return self._next


class _FakeCronTab:
    def __init__(self) -> None:
        self.items: list[CronItem] = []
        self._tab = CronTab(tab='')

    def __enter__(self) -> _FakeCronTab:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

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
    pass


@pytest.fixture
def fake_cron() -> _FakeCronTab:
    return _FakeCronTab()


@pytest.fixture
def scheduler(fake_cron: _FakeCronTab) -> _TestCronJobScheduler:
    return _TestCronJobScheduler(fake_cron)

