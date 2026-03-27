from __future__ import annotations

import datetime
from typing import Any
from uuid import uuid4

import pytest
from crontab import CronTab

from openvair.modules.scheduler.domain.base import BaseScheduler, JobMetadata


class _ConcreteScheduler(BaseScheduler):
    def create(self, creation_data: dict[str, Any]) -> dict[str, Any]:
        return creation_data

    def get(self, job_id: str) -> dict[str, Any]:
        return {'job_id': job_id}

    def list_all(self) -> list[dict[str, Any]]:
        return []


    def edit(self, editing_data: dict[str, Any]) -> dict[str, Any]:
        return editing_data

    def delete(self, job_id: str) -> None:
        return None


def test_base_scheduler_is_abstract() -> None:
    with pytest.raises(TypeError):
        BaseScheduler()


def test_concrete_scheduler_initializes_jobs_storage() -> None:
    scheduler = _ConcreteScheduler()

    assert scheduler.jobs == {}


def test_job_metadata_defaults() -> None:
    created_at = datetime.datetime.now()
    cron = CronTab(tab='')
    cron_item = cron.new(command='nightly.sh')
    cron_item.setall('* * * * *')
    metadata = JobMetadata(
        cron_item=cron_item,
        name='nightly',
        created_at=created_at,
    )

    assert metadata.created_at == created_at
    assert metadata.updated_at is None
    assert metadata.previous_id is None
    assert metadata.next_id is None


def test_job_metadata_links() -> None:
    prev_id = uuid4()
    next_id = uuid4()
    cron = CronTab(tab='')
    cron_item = cron.new(command='nightly.sh')
    cron_item.setall('* * * * *')
    metadata = JobMetadata(
        cron_item=cron_item,
        name='nightly',
        created_at=datetime.datetime.now(),
        previous_id=prev_id,
        next_id=next_id,
    )

    assert metadata.previous_id == prev_id
    assert metadata.next_id == next_id

