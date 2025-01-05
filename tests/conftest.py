# Configuration for pytest

import logging
import subprocess
import time

import pytest

from pymol_remote.client import PymolSession
from pymol_remote.common import log_level, pymol_rpc_host, pymol_rpc_port

# Configure logging
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Get client/server loggers and set log level
client_logger, server_logger = logging.getLogger("client"), logging.getLogger("server")
client_logger.setLevel(log_level)
server_logger.setLevel(log_level)

logger.debug(f"Logging level: {log_level}")
logger.debug(f"PyMOL RPC host: {pymol_rpc_host}")
logger.debug(f"PyMOL RPC port: {pymol_rpc_port}")


@pytest.fixture
def hostname():
    return pymol_rpc_host


@pytest.fixture
def port():
    return pymol_rpc_port


@pytest.fixture(scope="session")
def pymol_server():
    """Launches a PyMOL server subprocess for tests that require it."""
    logger.info("Starting PyMOL server subprocess...")

    # Start PyMOL server process
    server_process = subprocess.Popen(
        "pymol_remote",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=True,
    )

    # Give the server a moment to start up
    time.sleep(2)

    # Check if process is still running
    if server_process.poll() is not None:
        # Process has terminated - get output
        stdout, stderr = server_process.communicate()
        raise RuntimeError(
            f"PyMOL server failed to start!\n"
            f"Exit code: {server_process.returncode}\n"
            f"stdout: {stdout}\n"
            f"stderr: {stderr}"
        )

    # Verify server is responding
    try:
        test_session = PymolSession(hostname=pymol_rpc_host, port=pymol_rpc_port)
        test_session.is_alive()
        logger.info("PyMOL server started successfully!")
    except Exception as e:
        # Kill the process if it's still running
        server_process.terminate()
        server_process.wait()
        stdout, stderr = server_process.communicate()
        raise RuntimeError(
            f"PyMOL server started but is not responding!\n"
            f"Error: {str(e)}\n"
            f"stdout: {stdout}\n"
            f"stderr: {stderr}"
        )

    yield server_process

    # Cleanup after tests
    logger.info("Shutting down PyMOL server...")
    server_process.terminate()
    server_process.wait()
    logger.info("PyMOL server shutdown complete.")


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
