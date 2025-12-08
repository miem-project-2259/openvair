"""Cron Job Scheduler

This module defines the `CronJobScheduler` concrete class that allows for
management of cron jobs
"""

from typing import Any
from typing_extensions import override
import uuid

from crontab import CronTab, CronItem

from openvair.libs.log import get_logger
from openvair.modules.scheduler.domain.base import BaseScheduler
from openvair.modules.scheduler.domain.exception import (
    SchedulerDomainException,
    CronJobNotFound,
)
from openvair.modules.scheduler.entrypoints.schemas.requests import (
    RequestCreateJob,
    RequestUpdateJob,
)
from openvair.modules.scheduler.entrypoints.schemas.responses import (
    JobCreateResponse,
    JobResponse
)

LOG = get_logger(__name__)


class CronJobScheduler(BaseScheduler):
    def __init__(self, cron_obj: CronTab) -> None:
        super().__init__(cron_obj)

    def create(self, creation_data: dict[str, Any]) -> dict[str, Any]:  # pyright: ignore[reportExplicitAny]
        try:
            req = RequestCreateJob.model_validate(creation_data)
            with self._cron as cron:
                if req.before_job_id:
                    before_cmd = self._job(str(req.before_job_id)).command
                else:
                    before_cmd = None

                job = cron.new(
                    command=req.command,
                    comment=req.description or '',
                    before=before_cmd,
                )
                job.setall(req.cron_schedule)
                job_id = uuid.uuid4()
                self.jobs[str(job_id)] = job

            resp = JobCreateResponse(job_id=job_id)
            return resp.model_dump()

        except SchedulerDomainException as error:
            LOG.error(f'Failed to create a scheduled task: {error}')
            raise

    def edit(self, editing_data: dict[str, Any]) -> dict[str, Any]:
        try:
            req = RequestUpdateJob.model_validate(editing_data)
            with self._cron:
                job = self._job(str(req.job_id))
                if req.command:
                    job.set_command(req.command)
                if req.description:
                    job.set_comment(req.description)
                if req.cron_schedule:
                    job.setall(req.cron_schedule)

                # TODO recreate job if before is set

                resp = JobResponse(
                    id=req.job_id,
                    name="",
                    description=job.comment,
                    cron_schedule=str(job.slices),
                    command=job.command,
                    enabled=job.is_enabled(),
                    # TODO grab job ids
                    before_job_id=None,
                    after_job_id=None,
                    # TODO add rest
                )

            return resp

        except SchedulerDomainException as error:
            LOG.error(f'Failed to edit scheduled tasks: {error}')
            raise

    def delete(self, job_id: str) -> None:
        try:
            job = self._job(job_id)
            with self._cron as cron:
                cron.remove(job)
            self.jobs[job_id].delete()
        except SchedulerDomainException as error:
            LOG.error(f'Failed to delete scheduled task: {error}')
            raise

    @classmethod
    def _upd_job(cls, job: CronItem, data: dict[str, Any]) -> None:
        job.command = data.get('command')
        job.comment = data.get('comment')
        job.user = data.get('user')
        job.pre_comment = data.get('pre_comment')
        job.setall(data.get('schedule'))

    def _job(self, key: str) -> CronItem:
        if key not in self.jobs:
            raise CronJobNotFound(key)
        return self.jobs[key]
