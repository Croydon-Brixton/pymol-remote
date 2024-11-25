# Configuration for pytest

import logging
import os

import pytest

from pymol_remote.client import PymolSession
from pymol_remote.common import PYMOL_RPC_DEFAULT_PORT, PYMOL_RPC_HOST

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Get client/server loggers and set log level
client_logger, server_logger = logging.getLogger("client"), logging.getLogger("server")
client_logger.setLevel(log_level)
server_logger.setLevel(log_level)

PYMOL_RPC_HOST = os.getenv("PYMOL_RPC_HOST", PYMOL_RPC_HOST)
PYMOL_RPC_PORT = int(os.getenv("PYMOL_RPC_PORT", PYMOL_RPC_DEFAULT_PORT))

logger.debug(f"Logging level: {log_level}")
logger.debug(f"PyMOL RPC host: {PYMOL_RPC_HOST}")
logger.debug(f"PyMOL RPC port: {PYMOL_RPC_PORT}")


@pytest.fixture
def hostname():
    return PYMOL_RPC_HOST


@pytest.fixture
def port():
    return PYMOL_RPC_PORT


@pytest.fixture
def session(hostname, port):
    """Creates a PymolSession with configurable hostname and port."""
    session = PymolSession(hostname=hostname, port=port)

    # ... reset before test
    session.reinitialize()

    yield session

    # ... reset after test
    session.reinitialize()


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "requires_server: mark test as requiring a running PyMOL server"
    )
    config.addinivalue_line(
        "markers",
        "client_requires_biotite: mark test as requiring biotite on client side",
    )
