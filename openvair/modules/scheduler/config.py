"""Scheduler service layer configuration loader."""

import re

import toml

from openvair.config import (
    RPC_QUEUES,
    PROJECT_ROOT,
    get_default_session_factory,
)

CONFIG_PATH = PROJECT_ROOT / 'project_config.toml'
API_SERVICE_LAYER_QUEUE_NAME: str = RPC_QUEUES.Scheduler.SERVICE_LAYER
SERVICE_LAYER_DOMAIN_QUEUE_NAME: str = RPC_QUEUES.Scheduler.DOMAIN_LAYER
DEFAULT_SESSION_FACTORY = get_default_session_factory()

# Forbidden command patterns for validation
FORBIDDEN_COMMAND_PATTERNS = [
    r'\brm\s+-rf\b',     # dangerous deletion
    r'\bdd\b',           # raw disk write
    r'\bmkfs\b',         # filesystem creation
    r'\bcurl\b',         # unrestricted network calls
    r'\bwget\b',         # unrestricted downloads
    r'[;&\[\]\|]',       # shell chaining or unsafe symbols
]

def is_command_forbidden(command: str) -> bool:
    """Check if command contains forbidden or unsafe patterns."""
    return any(
        re.search(
            pattern,
            command,
            re.IGNORECASE
        ) for pattern in FORBIDDEN_COMMAND_PATTERNS
    )

try:
    config = toml.load(CONFIG_PATH)
except FileNotFoundError:
    error_message = f'Configuration file not found: {CONFIG_PATH}'
    raise RuntimeError(error_message)

# --- RabbitMQ ---
rabbitmq_cfg = config.get('rabbitmq', {})
RABBITMQ_HOST = rabbitmq_cfg.get('host', 'localhost')
RABBITMQ_PORT = rabbitmq_cfg.get('port', 5672)
RABBITMQ_USER = rabbitmq_cfg.get('user', 'guest')
RABBITMQ_PASSWORD = rabbitmq_cfg.get('password', 'guest')

# --- Database ---
db_cfg = config.get('database', {})
DATABASE_URL = (
    f"postgresql+psycopg2://{db_cfg.get('user', 'aero')}:"
    f"{db_cfg.get('password', 'aero')}@"
    f"{db_cfg.get('host', 'localhost')}:"
    f"{db_cfg.get('port', 5432)}/"
    f"{db_cfg.get('db_name', 'openvair')}"
)

# --- Scheduler defaults ---
CRON_USER = 'openvair'
MAX_CONCURRENT_JOBS = 10
JOB_TIMEOUT = 3600
LOG_RETENTION_DAYS = 30
