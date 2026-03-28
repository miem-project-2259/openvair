from sqlalchemy.orm import sessionmaker

from openvair.config import RPC_QUEUES, get_default_session_factory

# WAS API_SERVICE_LAYER_QUEUE_NAME: str = RPC_QUEUES.Eventstore.SERVICE_LAYER
# Had to change Eventstore to EventStore because of error
API_SERVICE_LAYER_QUEUE_NAME: str = RPC_QUEUES.EventStore.SERVICE_LAYER

DEFAULT_SESSION_FACTORY: sessionmaker = get_default_session_factory()
