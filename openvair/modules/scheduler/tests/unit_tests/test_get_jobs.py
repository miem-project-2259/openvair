from uuid import uuid4
from unittest.mock import Mock, AsyncMock
from pytest_mock import MockerFixture

import pytest

pytestmark = pytest.mark.asyncio


async def test_get_jobs_success(mocker: MockerFixture) -> None:
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
    from openvair.modules.scheduler.entrypoints import api as scheduler_api

    # фейковые входные данные
    data = Mock()

    # мок crud
    crud = Mock()
    crud.create_job = Mock()

    # мок run_in_threadpool
    fake_job = Mock()
    run_tp = mocker.patch.object(
        scheduler_api,
        "run_in_threadpool",
        new=AsyncMock(return_value=fake_job),
    )

    # act
    result = await scheduler_api.create_job(data=data, crud=crud)

    # проверяем, что вызван правильный метод
    run_tp.assert_awaited_once_with(crud.create_job, data)

    # проверяем результат
    assert result.status == "success"
    assert result.data is fake_job


async def test_edit_job_success(mocker: MockerFixture) -> None:
    from openvair.modules.scheduler.entrypoints import api as scheduler_api

    # входные данные
    job_id = Mock()
    data = Mock()

    # мок crud
    crud = Mock()
    crud.edit_job = Mock()

    # мок run_in_threadpool
    fake_updated_job = Mock()
    run_tp = mocker.patch.object(
        scheduler_api,
        "run_in_threadpool",
        new=AsyncMock(return_value=fake_updated_job),
    )

    # act
    result = await scheduler_api.edit_job(
        job_id=job_id,
        data=data,
        crud=crud,
    )

    # проверяем, что вызвали правильно
    run_tp.assert_awaited_once_with(crud.edit_job, job_id, data)

    # проверяем результат
    assert result.status == "success"
    assert result.data is fake_updated_job


async def test_delete_job_success(mocker: MockerFixture) -> None:
    from openvair.modules.scheduler.entrypoints import api as scheduler_api

    # входные данные
    job_id = Mock()

    # мок crud
    crud = Mock()
    crud.delete_job = Mock()

    # мок run_in_threadpool
    fake_deleted_job = Mock()
    run_tp = mocker.patch.object(
        scheduler_api,
        "run_in_threadpool",
        new=AsyncMock(return_value=fake_deleted_job),
    )

    # act
    result = await scheduler_api.delete_job(
        job_id=job_id,
        crud=crud,
    )

    # проверяем вызов
    run_tp.assert_awaited_once_with(crud.delete_job, job_id)

    # проверяем результат
    assert result.status == "success"
    assert result.data is fake_deleted_job
