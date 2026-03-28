"""Request models for scheduler API operations.

Defines schemas used as input payloads for scheduler-related API endpoints.
These models represent user-submitted data for creating, updating,
and deleting scheduled jobs, including:
- validation of command safety
- validation of cron expression format

Classes:
    - RequestCreateJob
    - RequestUpdateJob
    - RequestDeleteJob
"""

from uuid import UUID
from typing import Optional

from crontab import CronSlices
from pydantic import Field, field_validator

from openvair.modules.scheduler.config import validate_command
from openvair.common.base_pydantic_models import APIConfigRequestModel


class RequestCreateJob(APIConfigRequestModel):
    """Schema for creating a new scheduled job.

    Attributes:
        name (str): Unique name of the job.
        description (Optional[str]): Description of the job.
        cron_schedule (str): CRON expression defining job schedule.
        command (str): Command to execute.
        enabled (bool): Indicates whether the job is active.
    """

    name: str = Field(
        ...,
        examples=['backup_daily'],
        description='Unique name of the job',
        min_length=1,
        max_length=50,
    )
    description: Optional[str] = Field(
        None,
        examples=['Daily database backup job'],
        description='Optional description of the job',
        max_length=255,
    )
    cron_schedule: str = Field(
        ...,
        examples=['0 3 * * *'],
        description='CRON expression defining when the job runs',
    )
    command: str = Field(
        ...,
        examples=['backup.sh'],
        description='Command to execute when the job runs',
        min_length=1,
    )
    enabled: bool = Field(
        default=True,
        examples=[True],
        description='Indicates whether the job is enabled',
    )

    @field_validator("command", mode="before")
    @classmethod
    def validate_cmd(cls, value: str) -> str:
        """Validate command safety and syntax correctness."""
        return validate_command(value)

    @field_validator("cron_schedule", mode="before")
    @classmethod
    def validate_cron_schedule(cls, value: str) -> str:
        """Validate cron expression format using python-crontab."""
        if not value or not value.strip():
            msg = "Cron schedule cannot be empty or whitespace"
            raise ValueError(msg)
        if not CronSlices.is_valid(value.strip()):
            msg = f"Invalid cron expression: {value}"
            raise ValueError(msg)
        return value.strip()

    @field_validator("name", mode="before")
    @classmethod
    def validate_non_empty_name(cls, value: str) -> str:
        """Ensure name field is not empty or whitespace-only."""
        if not value or not value.strip():
            raise ValueError('Field cannot be empty or whitespace') # noqa TRY003
        return value.strip()


class RequestUpdateJob(APIConfigRequestModel):
    """Schema for updating an existing scheduled job.

    Attributes:
        name (Optional[str]): Updated name for the job.
        description (Optional[str]): Updated description.
        cron_schedule (Optional[str]): Updated CRON schedule.
        command (Optional[str]): Updated command.
        enabled (Optional[bool]): Indicates if the job should be active.
    """

    name: Optional[str] = Field(
        None,
        examples=['backup_db_updated'],
        description='Updated name for the job',
        min_length=1,
        max_length=50,
    )
    description: Optional[str] = Field(
        None,
        examples=['Incremental backup job'],
        description='Updated description for the job',
        max_length=255,
    )
    cron_schedule: Optional[str] = Field(
        None,
        examples=['0 2 * * *'],
        description='Updated CRON schedule for the job',
    )
    command: Optional[str] = Field(
        None,
        examples=['backup_incremental.sh'],
        description='Updated command for the job',
    )
    enabled: Optional[bool] = Field(
        None,
        examples=[False],
        description='Whether the job is enabled or disabled',
    )

    @field_validator("command", mode="before")
    @classmethod
    def validate_cmd(cls, value: Optional[str]) -> Optional[str]:
        """Validate optional command field for safety and syntax correctness."""
        if value is None:
            return value
        return validate_command(value)

    @field_validator("cron_schedule", mode="before")
    @classmethod
    def validate_cron_schedule(cls, value: Optional[str]) -> Optional[str]:
        """Validate optional cron expression format."""
        if value is None:
            return value
        if not CronSlices.is_valid(value.strip()):
            msg = f"Invalid cron expression: {value}"
            raise ValueError(msg)
        return value.strip()

    @field_validator("name", mode="before")
    @classmethod
    def validate_optional_name(cls, value: Optional[str]) -> Optional[str]:
        """Validate that name, if provided, is not empty or whitespace-only."""
        msg = 'Field cannot be only whitespace'
        if value is not None and not value.strip():
            raise ValueError(msg)
        return value.strip() if value else value


class RequestDeleteJob(APIConfigRequestModel):
    """Schema for deleting a job by its unique identifier.

    Attributes:
        job_id (UUID): Unique identifier of the job to delete.
    """

    job_id: UUID = Field(
        ...,
        examples=['a73f920b-d282-41e4-8ec1-6e6b89d3a9e7'],
        description='Unique identifier of the job to delete',
    )
