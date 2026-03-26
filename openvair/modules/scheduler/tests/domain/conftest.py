from __future__ import annotations

import datetime
from typing import Any

import pytest

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


class _FakeCronItem:
    def __init__(self, command: str, comment: str, schedule: str) -> None:
        self.command = command
        self.comment = comment
        self.slices = schedule
        self._enabled = True

    def setall(self, schedule: str) -> None:
        self.slices = schedule

    def set_command(self, command: str) -> None:
        self.command = command

    def set_comment(self, comment: str) -> None:
        self.comment = comment

    def is_enabled(self) -> bool:
        return self._enabled

    def schedule(self) -> _FakeSchedule:
        return _FakeSchedule()


class _FakeCronTab:
    def __init__(self) -> None:
        self.items: list[_FakeCronItem] = []

    def __enter__(self) -> _FakeCronTab:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def new(
        self,
        *,
        command: str,
        comment: str,
        before: _FakeCronItem | None = None,
    ) -> _FakeCronItem:
        job = _FakeCronItem(command=command, comment=comment, schedule='* * * * *')
        if before is None:
            self.items.append(job)
        else:
            index = self.items.index(before)
            self.items.insert(index, job)
        return job

    def remove(self, job: _FakeCronItem) -> None:
        self.items.remove(job)


class _TestCronJobScheduler(CronJobScheduler):
    def list_all(self) -> list[dict[str, Any]]:
        return []


@pytest.fixture
def fake_cron() -> _FakeCronTab:
    return _FakeCronTab()


@pytest.fixture
def scheduler(fake_cron: _FakeCronTab) -> _TestCronJobScheduler:
    return _TestCronJobScheduler(fake_cron)

