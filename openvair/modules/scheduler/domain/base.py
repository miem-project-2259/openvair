"""Base classes for scheduler domain models.

This module defines the `BaseScheduler` abstract class, which serves as the
foundation for implementing specific scheduler types (e.g., SystemCronScheduler).
It declares the required interface and shared fields for managing scheduled tasks.
"""

import abc
from typing import Any, Dict, List


class BaseScheduler(metaclass=abc.ABCMeta):
    """Abstract base class for scheduler domain models.

    This class defines the interface for all scheduler operations such as
    creation, editing, deletion, and retrieval of scheduled tasks (cron jobs).
    Concrete implementations must implement all abstract methods.
    """

    @abc.abstractmethod
    def create(self, creation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a scheduled task.

        Args:
            creation_data (Dict[str, Any]): Data required for task creation,
                e.g., {'schedule': '0 0 * * *', 'command': '/bin/true', 'comment': 'my-job-id'}.

        Returns:
            Dict[str, Any]: A dictionary representation of the created task.
        """
        ...

    @abc.abstractmethod
    def get(self, job_id: str) -> Dict[str, Any]:
        """Retrieve a single scheduled task by its unique identifier.

        Args:
            job_id (str): The unique identifier (e.g., comment) of the task.

        Returns:
            Dict[str, Any]: A dictionary representation of the found task.

        Raises:
            CronJobNotFound: If a task with the given ID is not found.
        """
        ...

    @abc.abstractmethod
    def list_all(self) -> List[Dict[str, Any]]:
        """Retrieve all scheduled tasks managed by this scheduler.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, where each dictionary
            represents a scheduled task.
        """
        ...

    @abc.abstractmethod
    def edit(self, job_id: str, editing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Edit a scheduled task.

        Args:
            job_id (str): The unique identifier of the task to edit.
            editing_data (Dict[str, Any]): New data for the task.

        Returns:
            Dict[str, Any]: A dictionary representation of the updated task.

        Raises:
            CronJobNotFound: If a task with the given ID is not found.
        """
        ...

    @abc.abstractmethod
    def delete(self, job_id: str) -> None:
        """Delete a scheduled task by its unique identifier.

        Args:
            job_id (str): The unique identifier of the task to delete.

        Raises:
            CronJobNotFound: If a task with the given ID is not found.
        """
        ...
