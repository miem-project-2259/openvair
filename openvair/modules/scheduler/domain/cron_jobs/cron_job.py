"""Cron Job Scheduler

This module defines the `CronJobScheduler` concrete class that allows for
management of cron jobs
"""

import uuid
import datetime
from typing import Any

from crontab import CronTab, CronItem

from openvair.libs.log import get_logger
from openvair.modules.scheduler.domain.base import JobMetadata, BaseScheduler
from openvair.modules.scheduler.domain.exception import (
    CronJobNotFound,
)
from openvair.modules.scheduler.entrypoints.schemas.requests import (
    RequestCreateJob,
    RequestUpdateJob,
)
from openvair.modules.scheduler.entrypoints.schemas.responses import (
    JobResponse,
    JobCreateResponse,
)

LOG = get_logger(__name__)


class CronJobScheduler(BaseScheduler):
    def __init__(self, cron_obj: CronTab) -> None:
        super().__init__(cron_obj)

    def __create_job(self, req: RequestCreateJob) -> CronItem:
        with self._cron as cron:
            job = cron.new(
                command=req.command,
                comment=req.description or '',
                # FIX this should be job item
                before=str(req.before_job_id or ''),
            )
            job.setall(req.cron_schedule)
        return job

    def create(self, creation_data: dict[str, Any]) -> dict[str, Any]:  # pyright: ignore[reportExplicitAny]
        try:
            req = RequestCreateJob.model_validate(creation_data)
            job_id = uuid.uuid4()
            next_id = None

            if req.before_job_id:
                next_id = req.before_job_id
                before_job = self._job(str(next_id))
                before_job.previous_id = job_id

            cron_job = self.__create_job(req)

            self.jobs[str(job_id)] = JobMetadata(
                cron_item=cron_job,
                name=req.name,
                created_at=datetime.datetime.now(),
                updated_at=None,
                next_id=next_id,
            )

            resp = JobCreateResponse(job_id=job_id)
            return resp.model_dump()

        except SchedulerDomainException as error:
            LOG.error(f'Failed to create a scheduled task: {error}')
            raise

    def edit(self, editing_data: dict[str, Any]) -> dict[str, Any]:
        try:
            req = RequestUpdateJob.model_validate(editing_data)
            with self._cron as cron:
                job = self._job(str(req.job_id))

                job.updated_at = datetime.datetime.now()

                if req.command:
                    job.cron_item.set_command(req.command)
                if req.description:
                    job.cron_item.set_comment(req.description)
                if req.cron_schedule:
                    job.cron_item.setall(req.cron_schedule)
                if req.name:
                    job.name = req.name

                if req.before_job_id:
                    cron.remove(job.cron_item)
                    req = RequestCreateJob(
                        name=job.name,
                        description=job.cron_item.comment,
                        cron_schedule=str(job.cron_item.slices),
                        command=job.cron_item.command,
                        before_job_id=req.before_job_id,
                        after_job_id=None,
                    )

                    new_job = self.__create_job(req)
                    job.cron_item = new_job

                job_schedule = job.cron_item.schedule()

                # TODO recreate job if before is set

                resp = JobResponse(
                    id=uuid.UUID(req.job_id),
                    name=job.name,
                    description=job.cron_item.comment,
                    cron_schedule=str(job.cron_item.slices),
                    command=job.cron_item.command,
                    enabled=job.cron_item.is_enabled(),
                    before_job_id=job.next_id,
                    after_job_id=None,
                    created_at=job.created_at,
                    updated_at=job.updated_at,
                    # TODO add rest
                    last_run=job_schedule.get_last(),
                    next_run=job_schedule.get_next(),
                )

            return resp.model_dump()

        except SchedulerDomainException as error:
            LOG.error(f'Failed to edit scheduled tasks: {error}')
            raise

    def delete(self, job_id: str) -> None:
        try:
            job = self._job(job_id)
            with self._cron as cron:
                cron.remove(job.cron_item)
            del self.jobs[job_id]
        except SchedulerDomainException as error:
            LOG.error(f'Failed to delete scheduled task: {error}')
            raise

    def _job(self, key: str) -> JobMetadata:
        if key not in self.jobs:
            raise CronJobNotFound(key)
        return self.jobs[key]
