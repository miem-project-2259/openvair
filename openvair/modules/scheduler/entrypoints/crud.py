"""CRUD adapter for Template API.

This module defines the SchedulerCrud class, which mediates between API handlers
and the service layer using RPC calls.

The methods of this class are responsible for invoking service-layer logic
using strongly typed DTOs and returning validated response models.

Classes:
    - SchedulerCrud: Encapsulates all scheduler-related RPC logic.

Dependencies:
    - MessagingClient: Generic RPC client for service-to-service communication.
    - TemplateServiceLayerManager: RPC method names for the service layer.
"""

from uuid import UUID
from typing import Any, Dict, List

from openvair.libs.log import get_logger
from openvair.modules.scheduler.adapters.dto.internal.commands import GetJobServiceCommandDTO
from openvair.modules.scheduler.entrypoints.schemas.responses import JobListResponse, JobResponse
from openvair.modules.template.config import API_SERVICE_LAYER_QUEUE_NAME
from openvair.libs.messaging.messaging_agents import MessagingClient
from openvair.modules.template.service_layer.services import (
    TemplateServiceLayerManager,
)
from openvair.modules.template.entrypoints.schemas.requests import (
    RequestEditTemplate,
    RequestCreateTemplate,
)
from openvair.modules.template.entrypoints.schemas.responses import (
    TemplateResponse,
)
from openvair.modules.template.adapters.dto.internal.commands import (
    GetTemplateServiceCommandDTO,
    EditTemplateServiceCommandDTO,
    CreateTemplateServiceCommandDTO,
    DeleteTemplateServiceCommandDTO,
)

LOG = get_logger(__name__)


class SchedulerCrud:
    """Provides RPC-based access to scheduler service operations.

    This class encapsulates all logic required by the API layer to interact
    with the service layer for scheduler and volume management.

    Attributes:
        service_layer_rpc (MessagingClient): RPC client for calling service
            methods.
    """

    def __init__(self) -> None:
        """Initialize the SchedulerCrud instance.

        Sets up the RPC client for the template service layer.
        """
        self.service_layer_rpc = MessagingClient(
            queue_name=API_SERVICE_LAYER_QUEUE_NAME
        )

    def get_all_jobs(self) -> List[JobListResponse]:
        """Retrieve a list of all jobs via RPC.

        Returns:
            List[JobListResponse]: A list of all available jobs.
        """
        LOG.info('Call service layer on getting jobs.')

        result: List[Dict[str, Any]] = self.service_layer_rpc.call(
            SchedulerServiceLayerManager.get_all_jobs.__name__,
            data_for_method={},
        )

        return [JobListResponse.model_validate(item) for item in result]

    def get_job(self, job_id: UUID) -> JobResponse:
        """Retrieve a specific job by its ID via RPC.

        Args:
            job_id (UUID): The ID of the job to retrieve.

        Returns:
            JobResponse: The retrieved job object.
        """
        LOG.info(f'Call service layer on getting template {job_id}.')

        getting_command_dto = GetJobServiceCommandDTO(id=job_id)
        result: Dict[str, Any] = self.service_layer_rpc.call(
            SchedulerServiceLayerManager.get_job.__name__,
            data_for_method=getting_command_dto.model_dump(mode='json'),
        )

        return JobResponse.model_validate(result)
