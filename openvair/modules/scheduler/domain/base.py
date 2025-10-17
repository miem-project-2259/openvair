"""Base classes for scheduler domain models.

This module defines the `BaseScheduler` abstract class, which serves as the
foundation for implementing specific scheduler types. It declares the required
interface and shared fields for managing schedulers.
"""

import abc
from typing import Any, Dict

from crontab import CronTab, CronItem


class BaseScheduler(metaclass=abc.ABCMeta):
    def __init__(self, cron_obj: CronTab):
        self._cron = cron_obj
        self.jobs: list[CronItem] = []


    @abc.abstractmethod
    def create(self, creation_data: Dict) -> CronItem:
        """Create a scheduled task.

        Args:
            creation_data (Dict): Data required for scheduler creation.
        """
        ...

    @abc.abstractmethod
    def edit(self, editing_data: Dict) -> Dict[str, Any]:
        """Edit scheduled tasks.

        Args:
            editing_data (Dict): Data for modifying the scheduler.
        """
        ...

    @abc.abstractmethod
    def delete(self, CronItem) -> None:
        """Delete a scheduled task."""
        ...
