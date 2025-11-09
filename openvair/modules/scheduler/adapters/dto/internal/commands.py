from uuid import UUID

from openvair.common.base_pydantic_models import BaseDTOModel


class GetJobServiceCommandDTO(BaseDTOModel):
    """DTO for retrieving a job by its ID.

    Attributes:
        id (UUID): Unique identifier of the job.
    """

    id: UUID
    