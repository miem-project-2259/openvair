"""Scheduler service basic operations (get, create, edit, delete)."""

from typing import Any, Dict, List

from croniter import croniter

from openvair.libs.log import get_logger
from openvair.modules.scheduler.config import (
    API_SERVICE_LAYER_QUEUE_NAME,
    SERVICE_LAYER_DOMAIN_QUEUE_NAME,
)
from openvair.modules.scheduler.adapters.orm import SchedulerJob
from openvair.libs.messaging.messaging_agents import MessagingClient
from openvair.modules.scheduler.adapters.serializer import (
    SchedulerJobSerializer,
)
from openvair.modules.scheduler.service_layer.exceptions import (
    JobNotFoundError,
    JobInvalidNameError,
    JobNameAlreadyExists,
    JobFieldIsNotEditable,
    JobInvalidCronExpression,
)
from openvair.modules.scheduler.service_layer.unit_of_work import (
    SchedulerSqlAlchemyUnitOfWork,
)

LOG = get_logger(__name__)


class SchedulerServiceLayerManager:
    """Manager for coordinating scheduler operations in the service layer.

    This class orchestrates scheduler-related tasks such as creation,
    updating, and deletion. It handles RPC communication, database transactions,
    domain delegation, and event logging.

    Attributes:
        uow (SchedulerSqlAlchemyUnitOfWork): Unit of Work for template
            transactions.
        domain_rpc (MessagingClient): RPC client for communicating with the
            domain layer.
        service_layer_rpc (MessagingClient): RPC client for internal task
            delegation.
    """

    def __init__(self) -> None:
        """Initialize the SchedulerServiceLayerManager.

        Sets up messaging clients, unit of work, and RPC clients.
        """
        self.uow = SchedulerSqlAlchemyUnitOfWork
        self.domain_rpc = MessagingClient(
            queue_name=SERVICE_LAYER_DOMAIN_QUEUE_NAME
        )
        self.service_layer_rpc = MessagingClient(
            queue_name=API_SERVICE_LAYER_QUEUE_NAME
        )

    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Retrieve all scheduler jobs."""
        with self.uow() as uow:
            orm_jobs = uow.jobs.get_all()

        api_jobs: List[Dict[str, Any]] = [
            SchedulerJobSerializer.to_web(job) for job in orm_jobs
        ]

        LOG.info(
            'Service layer request on getting jobs was successfully processed'
        )

        return api_jobs

    def create_job(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new scheduler job."""
        if not isinstance(data.get('name'), str) or not data['name'].strip():
            message = 'Job name cannot be empty'
            raise JobInvalidNameError(message)

        cron_schedule = data.get('cron_schedule')
        if not isinstance(cron_schedule, str) or not croniter.is_valid(
            cron_schedule
        ):
            message = 'Invalid cron expression'
            raise JobInvalidCronExpression(message)

        with self.uow() as uow:
            if uow.jobs.get_by_name(data['name']):
                message = 'Job with that name already exists'
                raise JobNameAlreadyExists(message)

            new_job = SchedulerJobSerializer.to_db(data)
            uow.jobs.add(new_job)

            uow.commit()
            uow.session.refresh(new_job)

            self.domain_rpc.cast(
                method_name='create_job',
                data_for_method=SchedulerJobSerializer.to_domain(new_job),
            )

            return SchedulerJobSerializer.to_web(new_job)

    def edit_job(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Edit an existing scheduler job."""
        job_id = payload["job_id"]
        data = payload["data"]

        with self.uow() as uow:
            job = self._get_job_or_raise(uow, job_id)
            allowed_fields = self._validate_edit_data(uow, job, data)

            for key in allowed_fields & data.keys():
                setattr(job, key, data[key])

            uow.commit()
            uow.session.refresh(job)

            # self.domain_rpc.cast(
            #     method_name='edit_job',
            #     data_for_method=SchedulerJobSerializer.to_domain(?),
            # ) ? Что должно происходить на доменном слое при изменении джобы?

            return SchedulerJobSerializer.to_web(job)

    def _get_job_or_raise(
        self, u: 'SchedulerSqlAlchemyUnitOfWork', job_id: int
    ) -> SchedulerJob:
        """Retrieve job by id or raise not found error."""
        job = u.jobs.get_by_id(job_id)
        if not job:
            message = 'Job id does not exist'
            raise JobNotFoundError(message)
        return job

    def _validate_edit_data(
        self,
        u: 'SchedulerSqlAlchemyUnitOfWork',
        job: SchedulerJob,
        data: Dict[str, Any],
    ) -> set[str]:
        """Validate editable data before applying changes."""
        cron_schedule = data.get('cron_schedule')
        if (
            cron_schedule
            and isinstance(cron_schedule, str)
            and not croniter.is_valid(cron_schedule)
        ):
            message = 'Invalid cron expression'
            raise JobInvalidCronExpression(message)

        new_name = data.get("name")
        if new_name is not None:
            existing = u.jobs.get_by_name(data['name'])
            if existing and existing.id != job.id:
                message = 'Job already exists'
                raise JobNameAlreadyExists(message)

        allowed_fields = {
            'name',
            'description',
            'cron_schedule',
            'command',
            'enabled',
        }

        invalid_fields = set(data) - allowed_fields
        if invalid_fields:
            invalid = ', '.join(sorted(invalid_fields))
            message = f'Field(s) {invalid} are not editable or do not exist.'
            raise JobFieldIsNotEditable(message)

        return allowed_fields

    def delete_job(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Delete scheduler job by its ID."""
        job_id = payload["job_id"]
        with self.uow() as uow:
            job = uow.jobs.get_by_id(job_id)

            if not job:
                message = 'Job id does not exist'
                raise JobNotFoundError(message)

            uow.jobs.delete(job)
            uow.commit()

            # self.domain_rpc.cast(
            #     method_name='delete_job',
            #     data_for_method=SchedulerJobSerializer.to_domain(new_job), ?
            # По какому атрибуту мне указывать на
            # конкретный джоб на доменном слое?
            # )

            return SchedulerJobSerializer.to_web(job)


    # @periodic_task(interval=10) #  РЕАЛИЗУЙ МЕТОД ДЛЯ МОНИТОРИНГА
    # def monitoring(self) -> None:
    # TODO: refactor to multiple methods
    #     """Monitor and synchronize network interfaces with the system.

    #     This periodic task refreshes the state of all network interfaces
    #     in the database with data retrieved from the operating system.
    #     It ensures that the database remains consistent with
    #     the actual state of the system's network interfaces.
    #     """
    #     LOG.info('Start monitoring')
    #     interfaces_from_os = {
    #         inf['name']: inf for inf in utils.InterfacesFromSystem().get_all()
    #     }

    #     LOG.debug('Got interfaces from system %s' % interfaces_from_os)
    #     with self.uow() as uow:
    #         db_interfaces = [
    #             iface.name for iface in uow.interfaces.get_all()
    #         ]
    #         LOG.debug('Got interfaces from db %s' % db_interfaces)

    #     for (os_iface_name), os_iface_data in interfaces_from_os.items():
    #         with self.uow() as uow:
    #             db_iface_now = uow.interfaces.get_by_name(os_iface_name)
    #             db_interface = self.__synchronize_os_to_db_info(
    #                 os_iface_data,
    #                 db_iface_now,
    #             )
    #             db_interface.status = InterfaceStatus.available.name
    #             uow.interfaces.add(db_interface)
    #             if os_iface_name in db_interfaces:
    #                 db_interfaces.remove(os_iface_name)
    #             uow.commit()

    #     prefixes_to_delete = ['vnet', 'veth']
    #     for db_iface_name in db_interfaces:
    #         with self.uow() as uow:
    #             db_iface = uow.interfaces.get_by_name(db_iface_name)
    #             if not db_iface:
    #                 continue
    #             if db_iface_name.startswith('ovs-system') or any(
    #                 db_iface_name.startswith(prefix) for prefix
    #                 in prefixes_to_delete
    #             ):
    #                 uow.interfaces.delete(db_iface)
    #             else:
    #                 LOG.info(
    #                     f'Interface {db_iface_name!r} not found in os. '
    #                     f'Setting status to error for '
    #                     f'interface {db_iface!r}.'
    #                 )
    #                 db_iface.status = InterfaceStatus.error.name
    #             uow.commit()

    #     LOG.info('Stop monitoring')

    # def __synchronize_os_to_db_info(
    #     self,
    #     os_iface: Dict,
    #     db_iface: Optional[orm.Interface],
    # ) -> orm.Interface:
    #     """Synchronize the OS interface data with the database.

    #     This method compares the interface data from the operating system with
    #     the data in the database and updates the database accordingly. If the
    #     interface does not exist in the database, it is created.

    #     Args:
    #         os_iface (Dict): A dictionary containing the interface data from
    #             the operating system.
    #         db_iface (orm.Interface): The corresponding database interface
    #             object, if it exists.

    #     Returns:
    #         orm.Interface: The updated or created database interface object.
    #     """
    #     os_iface_name = os_iface.get('name')
    #     if db_iface is None:
    #         LOG.warning(
    #             f'Interface {os_iface_name} not found in db. Trying to '
    #             'synchronize...'
    #         )
    #         db_iface = cast(orm.Interface, DataSerializer.to_db(os_iface))
    #         LOG.info(f'Interface {os_iface_name}'
    #                   'successfully prepared for db')
    #     else:
    #         self._update_extra_specs(db_iface,
    #                                  os_iface.get('extra_specs', {}))

    #     for attribute in CreateInterfaceInfo._fields:
    #         attribute_value = os_iface.get(attribute)
    #         setattr(db_iface, attribute, attribute_value)

    #     return db_iface
