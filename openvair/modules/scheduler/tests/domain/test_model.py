from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from openvair.modules.scheduler.domain.base import BaseScheduler
from openvair.modules.scheduler.domain.model import (
    DomainSchedulerModelDTO,
    SchedulerFactory,
)


class _DummyScheduler(BaseScheduler):
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


class _FactoryFakeCronTab:
    def __init__(self, *, user: str | None = None) -> None:
        self.user = user


def test_domain_scheduler_model_dto_parses_alias() -> None:
    dto = DomainSchedulerModelDTO.model_validate({'type': 'system_cron', 'user': 'root'})

    assert dto.scheduler_type == 'system_cron'
    assert dto.user == 'root'


def test_domain_scheduler_model_dto_requires_type() -> None:
    with pytest.raises(ValidationError):
        DomainSchedulerModelDTO.model_validate({'user': 'root'})


def test_scheduler_factory_returns_scheduler(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        'openvair.modules.scheduler.domain.model.CronTab',
        _FactoryFakeCronTab,
    )

    factory = SchedulerFactory()
    monkeypatch.setattr(factory, '_scheduler_classes', {'system_cron': _DummyScheduler})

    scheduler = factory.get_scheduler({'type': 'system_cron', 'user': 'alice'})

    assert isinstance(scheduler, _DummyScheduler)
    assert isinstance(scheduler._cron, _FactoryFakeCronTab)
    assert scheduler._cron.user == 'alice'


def test_scheduler_factory_unknown_type_raises_value_error() -> None:
    factory = SchedulerFactory()

    with pytest.raises(ValueError, match="Unknown scheduler type"):
        factory.get_scheduler({'type': 'unknown', 'user': 'root'})


def test_scheduler_factory_default_mapping_uses_abstract_scheduler() -> None:
    factory = SchedulerFactory()

    with pytest.raises(TypeError):
        factory.get_scheduler({'type': 'system_cron', 'user': 'root'})

