# mypy: disable-error-code="no-any-unimported, unused-ignore"

"""Cron Job Scheduler

This module defines the `CronJobScheduler` concrete class that allows for
management of cron jobs
"""

from __future__ import annotations

import uuid
import datetime
from typing import Any, Dict, Optional

from crontab import CronTab, CronItem  # type: ignore

from openvair.libs.log import get_logger
from openvair.modules.scheduler.domain.base import JobMetadata, BaseScheduler
from openvair.modules.scheduler.domain.exception import (
    CronJobNotFound,
)
from openvair.modules.scheduler.shared.base_exceptions import (
    SchedulerDomainException,
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
    """Concrete implementation of BaseScheduler for system cron jobs.

    This class provides specific logic for interacting with the system crontab,
    managing job metadata, and handling task positioning (before/after).
    """

    def __init__(self, crontab: Optional[CronTab] = None) -> None:
        """Initialize the CronJobScheduler."""
        super().__init__()
        if crontab is not None:
            self._cron = crontab
        else:
            self._cron = CronTab(user=True)

    def __create_job(self, req: RequestCreateJob) -> CronItem:
        with self._cron as cron:
            before_job = (
                self._job(req.before_job_id).cron_item
                if req.before_job_id
                else None
            )
            before_arg = None if before_job is None else [before_job]
            job = cron.new(
                command=req.command,
                comment=req.description or '',
                before=before_arg,
            )
            job.setall(req.cron_schedule)
        return job

    def create(self, creation_data: Dict[str, Any]) -> Dict[str, Any]:  # pyright: ignore[reportExplicitAny]
        """Create a scheduled task and store its metadata.

        Args:
            creation_data (Dict[str, Any]): Dictionary with job creation data.

        Returns:
            Dict[str, Any]: Dictionary containing the new job_id.
        """
        try:
            req = RequestCreateJob.model_validate(creation_data)
            job_id = uuid.uuid4()
            next_id = None

            if req.before_job_id:
                next_id = req.before_job_id
                before_job = self._job(next_id)
                before_job.previous_id = job_id

            cron_job = self.__create_job(req)

            self.jobs[job_id] = JobMetadata(
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

    def edit(self, editing_data: Dict[str, Any]) -> Dict[str, Any]:  # noqa: C901
        # TODO: Ruff ругается C901 `edit` is too complex (7 > 5)
        """Modify an existing scheduled task.

        Args:
            editing_data (Dict[str, Any]): Dictionary with updated job data.

        Returns:
            Dict[str, Any]: Updated job representation.
        """
        try:
            req = RequestUpdateJob.model_validate(editing_data)
            with self._cron as cron:
                job = self._job(req.job_id)

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
                    c_req = RequestCreateJob(
                        name=job.name,
                        description=job.cron_item.comment,
                        cron_schedule=str(job.cron_item.slices),
                        command=job.cron_item.command,  # type: ignore[arg-type]
                        before_job_id=req.before_job_id,
                        after_job_id=None,
                    )

                    new_job = self.__create_job(c_req)
                    job.cron_item = new_job

                job_schedule = job.cron_item.schedule()  # noqa: F841
                # noqa: RUF003 TODO: Элис, привет, это Рустам) А для чего эта переменная?

                return self.get(str(req.job_id))

        except SchedulerDomainException as error:
            LOG.error(f'Failed to edit scheduled tasks: {error}')
            raise

    def get(self, job_id: str) -> Dict[str, Any]:
        """Retrieve job details by ID.

        Args:
            job_id (str): UUID of the job as a string.

        Returns:
            Dict[str, Any]: Job details including schedule and run times.
        """
        try:
            with self._cron:
                job_uuid = uuid.UUID(job_id)
                job = self._job(job_uuid)
                job_schedule = job.cron_item.schedule()

                # TODO recreate job if before is set

                resp = JobResponse(
                    id=job_uuid,
                    name=job.name,
                    description=job.cron_item.comment,
                    cron_schedule=str(job.cron_item.slices),
                    command=job.cron_item.command, # type: ignore[arg-type]
                    enabled=job.cron_item.is_enabled(),
                    before_job_id=job.next_id,
                    after_job_id=None,
                    created_at=job.created_at,
                    updated_at=job.updated_at,
                    last_run=job_schedule.get_last(),
                    next_run=job_schedule.get_next(),
                )

            return resp.model_dump()
        except SchedulerDomainException as error:
            LOG.error(f'Failed to get scheduled task: {error}')
            raise

    def delete(self, job_id: str) -> None:
        """Remove a job from both the crontab and internal metadata.

        Args:
            job_id (str): UUID of the job to delete.
        """
        try:
            job_uuid = uuid.UUID(job_id)
            job = self._job(job_uuid)
            with self._cron as cron:
                cron.remove(job.cron_item)
            del self.jobs[job_uuid]
        except SchedulerDomainException as error:
            LOG.error(f'Failed to delete scheduled task: {error}')
            raise

    def _job(self, key: uuid.UUID) -> JobMetadata:
        """Helper to get JobMetadata or raise CronJobNotFound."""
        if key not in self.jobs:
            raise CronJobNotFound(str(key))
        return self.jobs[key]
