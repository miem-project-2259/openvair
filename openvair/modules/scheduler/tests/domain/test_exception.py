from __future__ import annotations

import pytest

from openvair.modules.scheduler.domain.exception import (
    CronDaemonException,
    CronJobNotFound,
    CronTabReadException,
    CronTabWriteException,
    InvalidCronExpression,
)
from openvair.modules.scheduler.shared.base_exceptions import SchedulerDomainException


@pytest.mark.parametrize(
    'exc_type',
    [
        CronJobNotFound,
        InvalidCronExpression,
        CronTabReadException,
        CronTabWriteException,
        CronDaemonException,
    ],
)
def test_domain_exceptions_inherit_scheduler_domain_exception(exc_type: type[Exception]) -> None:
    error = exc_type('boom')

    assert isinstance(error, SchedulerDomainException)


def test_exception_string_representation() -> None:
    error = CronJobNotFound('missing-id')

    assert str(error) == 'CronJobNotFound: missing-id'

