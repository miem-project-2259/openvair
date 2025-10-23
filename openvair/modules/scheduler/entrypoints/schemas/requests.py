"""Request models for scheduler API operations.

Defines schemas used as input payloads for scheduler-related API endpoints.
These models represent user-submitted data for creating, updating,
and deleting scheduled jobs.

Classes:
    - RequestCreateJob
    - RequestUpdateJob
    - RequestDeleteJob
"""

from uuid import UUID
from typing import Optional
from pydantic import Field
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
        examples=["backup_daily"],
        description="Unique name of the job",
        min_length=1,
        max_length=50,
    )
    description: Optional[str] = Field(
        None,
        examples=["Daily database backup job"],
        description="Optional description of the job",
        max_length=255,
    )
    cron_schedule: str = Field(
        ...,
        examples=["0 3 * * *"],
        description="CRON expression defining when the job runs",
    )
    command: str = Field(
        ...,
        examples=["backup.sh"],
        description="Command to execute when the job runs",
        min_length=1,
    )
    enabled: bool = Field(
        default=True,
        examples=[True],
        description="Indicates whether the job is enabled",
    )


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
        examples=["backup_db_updated"],
        description="Updated name for the job",
        min_length=1,
        max_length=50,
    )
    description: Optional[str] = Field(
        None,
        examples=["Incremental backup job"],
        description="Updated description for the job",
        max_length=255,
    )
    cron_schedule: Optional[str] = Field(
        None,
        examples=["0 2 * * *"],
        description="Updated CRON schedule for the job",
    )
    command: Optional[str] = Field(
        None,
        examples=["backup_incremental.sh"],
        description="Updated command for the job",
    )
    enabled: Optional[bool] = Field(
        None,
        examples=[False],
        description="Whether the job is enabled or disabled",
    )


class RequestDeleteJob(APIConfigRequestModel):
    """Schema for deleting a job by its unique identifier.

    Attributes:
        job_id (UUID): Unique identifier of the job to delete.
    """

    job_id: UUID = Field(
        ...,
        examples=["a73f920b-d282-41e4-8ec1-6e6b89d3a9e7"],
        description="Unique identifier of the job to delete",
    )
