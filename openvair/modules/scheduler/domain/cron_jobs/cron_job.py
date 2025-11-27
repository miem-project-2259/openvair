"""Cron Job Scheduler

This module defines the `CronJobScheduler` concrete class that allows for
management of cron jobs
"""

from typing import Dict, Any

from crontab import CronTab, CronItem

from openvair.libs.log import get_logger
from openvair.modules.scheduler.domain.base import BaseScheduler
from openvair.modules.scheduler.domain.exception import SchedulerDomainException, CronJobNotFound

LOG = get_logger(__name__)


class CronJobScheduler(BaseScheduler):
    def __init__(self, cron_obj: CronTab) -> None:
        super().__init__(cron_obj)

    def create(self, creation_data: Dict) -> None:
        try:
            with self._cron as cron:
                for k, data in creation_data.items():
                    job = cron.new(
                        data.get('before'),
                    )
                    self._upd_job(job, data)
                    self.jobs[k] = job

        except SchedulerDomainException as error:
            LOG.error(f'Failed to create a scheduled task: {error}')
            raise

    def edit(self, editing_data: Dict) -> Dict[str, Any]:
        try:
            with self._cron:
                for k, upd_data in editing_data:
                    job = self._job(k)
                    self._upd_job(job, upd_data)

            return {}
        except SchedulerDomainException as error:
            LOG.error(f'Failed to edit scheduled tasks: {error}')
            raise

    def delete(self, key: str) -> None:
        try:
            job = self._job(key)
            with self._cron as cron:
                cron.remove(job)
            self.jobs[key].delete()
        except SchedulerDomainException as error:
            LOG.error(f'Failed to delete scheduled task: {error}')
            raise

    @classmethod
    def _upd_job(cls, job: CronItem, data: Dict) -> None:
        job.command = data.get('command')
        job.comment = data.get('comment')
        job.user = data.get('user')
        job.pre_comment = data.get('pre_comment')
        job.setall(data.get('schedule'))

    def _job(self, key: str) -> CronItem:
        if key not in self.jobs:
            raise CronJobNotFound(key)
        return self.jobs[key]
