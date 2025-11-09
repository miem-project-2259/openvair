"""Request models for scheduler API operations.

Defines schemas used as input payloads for scheduler-related API endpoints.
These models represent user-submitted data for creating, updating,
and deleting scheduled jobs, including:
- dependency control ("before" / "after") between tasks
- validation of command safety
- validation of cron expression format

Classes:
    - RequestCreateJob
    - RequestUpdateJob
    - RequestDeleteJob
"""

import re
from uuid import UUID
from typing import Optional
from pydantic import Field, field_validator, model_validator
from crontab import CronSlices

from openvair.common.base_pydantic_models import APIConfigRequestModel


FORBIDDEN_COMMAND_PATTERNS = [
    r'\brm\s+-rf\b',
    r'\bdd\b',
    r'\bmkfs\b',
    r'\bcurl\b',
    r'\bwget\b',
    r'[;&\[\]\|]',
]


def is_command_forbidden(command: str) -> bool:
    """Check if command contains forbidden or unsafe patterns."""
    return any(re.search(pattern, command, re.IGNORECASE) for pattern in FORBIDDEN_COMMAND_PATTERNS)


class RequestCreateJob(APIConfigRequestModel):
    """Schema for creating a new scheduled job."""

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
    before_job_id: Optional[UUID] = Field(
        None,
        examples=["c1b65a20-5b29-4b1d-8c1c-8c41cb47d111"],
        description="If specified, this job will start only after the referenced job finishes",
    )
    after_job_id: Optional[UUID] = Field(
        None,
        examples=["f9d3a511-d3b4-4f4b-9287-4cbf3e6f49de"],
        description="If specified, the referenced job will start after this one completes",
    )

    @field_validator("command", mode="before")
    @classmethod
    def validate_command(cls, value: str) -> str:
        """Validate command safety and syntax correctness."""
        if not value or not value.strip():
            raise ValueError("Command cannot be empty or whitespace-only")

        if is_command_forbidden(value):
            raise ValueError("Command contains forbidden or unsafe operations")

        if not re.match(r"^[a-zA-Z0-9_\-./ ]+$", value):
            raise ValueError("Command contains invalid characters")

        if not re.search(r'\.sh$', value):
            raise ValueError("Command must reference a valid script file (e.g., backup.sh)")

        return value.strip()

    @field_validator("cron_schedule", mode="before")
    @classmethod
    def validate_cron_schedule(cls, value: str) -> str:
        """Validate cron expression format using python-crontab."""
        if not value or not value.strip():
            raise ValueError("Cron schedule cannot be empty or whitespace")
        if not CronSlices.is_valid(value.strip()):
            raise ValueError(f"Invalid cron expression: {value}")
        return value.strip()

    @field_validator("name", mode="before")
    @classmethod
    def validate_non_empty_name(cls, value: str) -> str:
        """Ensure name field is not empty or whitespace-only."""
        if not value or not value.strip():
            raise ValueError("Name cannot be empty or whitespace")
        return value.strip()

    @model_validator(mode="after")
    def check_dependency_conflicts(self) -> "RequestCreateJob":
        """Ensure that both before_job_id and after_job_id are not set simultaneously."""
        if self.before_job_id and self.after_job_id:
            raise ValueError(
                "Cannot specify both before_job_id and after_job_id for the same job."
            )
        return self


class RequestUpdateJob(APIConfigRequestModel):
    """Schema for updating an existing scheduled job."""

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
    before_job_id: Optional[UUID] = Field(
        None,
        examples=["d2c43a22-4e34-4e7f-9a3a-0af733d9a122"],
        description="If specified, this job will start only after the referenced job finishes",
    )
    after_job_id: Optional[UUID] = Field(
        None,
        examples=["a9b51a12-bd31-4fa3-9523-f7e4b8e3d321"],
        description="If specified, the referenced job will start after this one completes",
    )

    @field_validator("command", mode="before")
    @classmethod
    def validate_command(cls, value: Optional[str]) -> Optional[str]:
        """Validate optional command field for safety and syntax correctness."""
        if value is None:
            return value
        if not value.strip():
            raise ValueError("Command cannot be only whitespace")
        if is_command_forbidden(value):
            raise ValueError("Command contains forbidden or unsafe operations")
        if not re.match(r"^[a-zA-Z0-9_\-./ ]+$", value):
            raise ValueError("Command contains invalid characters")
        if not re.search(r'\.sh$', value):
            raise ValueError("Command must reference a valid script file (e.g., backup.sh)")
        return value.strip()

    @field_validator("cron_schedule", mode="before")
    @classmethod
    def validate_cron_schedule(cls, value: Optional[str]) -> Optional[str]:
        """Validate optional cron expression format."""
        if value is None:
            return value
        if not CronSlices.is_valid(value.strip()):
            raise ValueError(f"Invalid cron expression: {value}")
        return value.strip()

    @field_validator("name", mode="before")
    @classmethod
    def validate_optional_name(cls, value: Optional[str]) -> Optional[str]:
        """Validate that name, if provided, is not empty or whitespace-only."""
        if value is not None and not value.strip():
            raise ValueError("Name cannot be only whitespace")
        return value.strip() if value else value

    @model_validator(mode="after")
    def check_dependency_conflicts(self) -> "RequestUpdateJob":
        """Ensure that both before_job_id and after_job_id are not set simultaneously."""
        if self.before_job_id and self.after_job_id:
            raise ValueError(
                "Cannot specify both before_job_id and after_job_id for the same job."
            )
        return self


class RequestDeleteJob(APIConfigRequestModel):
    """Schema for deleting a job by its unique identifier."""

    job_id: UUID = Field(
        ...,
        examples=["a73f920b-d282-41e4-8ec1-6e6b89d3a9e7"],
        description="Unique identifier of the job to delete",
    )
