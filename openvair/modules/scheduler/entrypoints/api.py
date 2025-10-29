"""Scheduler API endpoints.

This module exposes HTTP API endpoints for managing schedulers.
It includes operations for listing, retrieving, creating, updating, and deleting
schedulers.

All endpoints require user authentication and rely on the SchedulerCrud adapter
for business logic.

Endpoints:
    - GET /scheduler/jobs - getting a list of all jobs with pagination
    - GET /scheduler/jobs/{job_id} - getting a specific job by ID
    - POST /scheduler/jobs - creating a new scheduler job
    - PATCH /scheduler/jobs/{job_id} - changing job parameters
    - DELETE /scheduler/jobs/{job_id} - deleting a scheduler job

Dependencies:
    - get_current_user: Ensures request is authenticated
    - SchedulerCrud: RPC adapter between API and service layer
"""

from uuid import UUID
from typing import List

from fastapi import Depends, APIRouter, status
from fastapi_pagination import Page, Params, paginate
from openvair.modules.scheduler.entrypoints.crud import SchedulerCrud
from starlette.concurrency import run_in_threadpool

from openvair.libs.log import get_logger
from openvair.common.schemas import BaseResponse
from openvair.libs.auth.jwt_utils import get_current_user
from openvair.modules.scheduler.entrypoints.schemas.responses import JobListResponse, JobResponse
from openvair.modules.template.entrypoints.schemas.requests import (
    RequestEditTemplate,
    RequestCreateTemplate,
)
from openvair.modules.template.entrypoints.schemas.responses import (
    TemplateResponse,
)

LOG = get_logger(__name__)
router = APIRouter(
    prefix='/scheduler',
    tags=['scheduler'],
    dependencies=[
        Depends(get_current_user)
    ],  # Глобальная авторизация для всех эндпоинтов
    responses={404: {'description': 'Not found!'}},
)


@router.get(
    '/jobs',
    response_model=BaseResponse[Page[JobListResponse]],
    status_code=status.HTTP_200_OK,
)
async def get_jobs(
    crud: SchedulerCrud = Depends(SchedulerCrud),
    params: Params = Depends(),
) -> BaseResponse[Page[JobListResponse]]:
    """Retrieve a paginated list of jobs.

    Args:
        crud (SchedulerCrud): Dependency-injected service for handling scheduler
            logic.
        params (Params): Dependency-injected for pagination params
    Returns:
        BaseResponse[Page[JobListResponse]]: Paginated response containing jobs.
    """
    LOG.info('Api handle request on getting jobs')

    jobs: List[JobListResponse] = await run_in_threadpool(
        crud.get_all_jobs
    )
    paginated_jobs = paginate(jobs, params)

    LOG.info('Api request on getting jobs was successfully processed')
    return BaseResponse(status='success', data=paginated_jobs)


@router.get(
    '/jobs/{job_id}',
    response_model=BaseResponse[JobResponse],
    status_code=status.HTTP_200_OK,
)
async def get_job(
    job_id: UUID,
    crud: SchedulerCrud = Depends(SchedulerCrud),
) -> BaseResponse[JobResponse]:
    """Retrieve a specific job by its ID.

    Args:
        job_id (UUID): The ID of the job to retrieve.
        crud (SchedulerCrud): Dependency-injected service for handling job
            logic.

    Returns:
        BaseResponse[JobResponse]: The retrieved job.
    """
    LOG.info(f'Api handle request on getting template: {job_id}')

    job = await run_in_threadpool(crud.get_job, job_id)

    LOG.info(
        f'Api request on getting job {job_id} '
        'was successfully processed'
    )
    return BaseResponse(status='success', data=job)
