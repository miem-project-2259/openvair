"""Tests for scheduler API endpoints."""

from uuid import uuid4
from unittest.mock import Mock, AsyncMock

import pytest
from pytest_mock import MockerFixture

pytestmark = pytest.mark.asyncio


async def test_get_jobs_success(mocker: MockerFixture) -> None:
    """Test successful retrieval of all jobs."""
    from openvair.modules.scheduler.entrypoints import api as scheduler_api

    crud = Mock()
    crud.get_all_jobs = Mock()

    fake_jobs = [Mock(), Mock()]
    run_tp = mocker.patch.object(
        scheduler_api,
        "run_in_threadpool",
        new=AsyncMock(return_value=fake_jobs),
    )

    fake_page = Mock()
    paginate = mocker.patch.object(
        scheduler_api,
        "paginate",
        return_value=fake_page,
    )

    params = Mock()

    result = await scheduler_api.get_jobs(crud=crud, params=params)

    run_tp.assert_awaited_once_with(crud.get_all_jobs)
    paginate.assert_called_once_with(fake_jobs, params)

    assert result.status == "success"
    assert result.data is fake_page


async def test_get_job_success(mocker: MockerFixture) -> None:
    """Test successful retrieval of a specific job by ID."""
    from openvair.modules.scheduler.entrypoints import api as scheduler_api

    job_id = uuid4()

    crud = Mock()
    crud.get_job = Mock()

    fake_job = Mock()
    run_tp = mocker.patch.object(
        scheduler_api,
        "run_in_threadpool",
        new=AsyncMock(return_value=fake_job),
    )

    result = await scheduler_api.get_job(job_id=job_id, crud=crud)

    run_tp.assert_awaited_once_with(crud.get_job, job_id)

    assert result.status == "success"
    assert result.data is fake_job


async def test_create_job_success(mocker: MockerFixture) -> None:
    """Test successful creation of a new job."""
    from openvair.modules.scheduler.entrypoints import api as scheduler_api

    data = Mock()

    crud = Mock()
    crud.create_job = Mock()

    fake_job = Mock()
    run_tp = mocker.patch.object(
        scheduler_api,
        "run_in_threadpool",
        new=AsyncMock(return_value=fake_job),
    )

    result = await scheduler_api.create_job(data=data, crud=crud)

    run_tp.assert_awaited_once_with(crud.create_job, data)

    assert result.status == "success"
    assert result.data is fake_job


async def test_edit_job_success(mocker: MockerFixture) -> None:
    """Test successful editing of a job."""
    from openvair.modules.scheduler.entrypoints import api as scheduler_api

    job_id = Mock()
    data = Mock()

    crud = Mock()
    crud.edit_job = Mock()

    fake_updated_job = Mock()
    run_tp = mocker.patch.object(
        scheduler_api,
        "run_in_threadpool",
        new=AsyncMock(return_value=fake_updated_job),
    )

    result = await scheduler_api.edit_job(
        job_id=job_id,
        data=data,
        crud=crud,
    )

    run_tp.assert_awaited_once_with(crud.edit_job, job_id, data)

    assert result.status == "success"
    assert result.data is fake_updated_job


async def test_delete_job_success(mocker: MockerFixture) -> None:
    """Test successful deletion of a job."""
    from openvair.modules.scheduler.entrypoints import api as scheduler_api

    job_id = Mock()

    crud = Mock()
    crud.delete_job = Mock()

    fake_deleted_job = Mock()
    run_tp = mocker.patch.object(
        scheduler_api,
        "run_in_threadpool",
        new=AsyncMock(return_value=fake_deleted_job),
    )

    result = await scheduler_api.delete_job(
        job_id=job_id,
        crud=crud,
    )

    run_tp.assert_awaited_once_with(crud.delete_job, job_id)

    assert result.status == "success"
    assert result.data is fake_deleted_job
