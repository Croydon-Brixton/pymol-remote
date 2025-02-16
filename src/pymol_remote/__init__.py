"""
PyMOL Remote: A Python package for remote control of PyMOL instances.

This module provides functionality to establish and manage remote connections to PyMOL servers,
enabling programmatic control of PyMOL visualization from Python scripts.

The main entry point is the `get_pymol_session` function which establishes a connection to a
PyMOL server and returns a session object for interaction.

Example:
    >>> import pymol_remote
    >>> session = pymol_remote.get_pymol_session()
    >>> session.do("load 1abc.pdb")
"""

from pymol_remote import client


def get_pymol_session(
    hostname: str | None = None, port: int | None = None
) -> client.PymolSession:
    """
    Establishes a connection to a PyMOL server and returns a `pymol_remote.client.PymolSession` object.
    First attempts to reuse an existing global session if no hostname/port is specified.
    Otherwise tries to establish a new connection, attempting up to 5 consecutive ports.

    If you want to use `pymol_remote`, make sure to follow the usage instructions at
        https://github.com/Croydon-Brixton/pymol-remote

    Args:
        - hostname (str | None, optional): The hostname of the PyMOL server. Defaults to 'localhost' if None.
        - port (int | None, optional): The starting port number to attempt connection. Defaults to 9123 if None.

    Returns:
        pymol_remote.client.PymolSession: An active connection to the PyMOL server.

    Raises:
        - ImportError: If `pymol_remote` package is not installed.
        - RuntimeError: If unable to establish connection after trying 5 consecutive ports.
    """

    # ... get existing session if available
    if (hostname is None) and (port is None):
        session = client._GLOBAL_SERVER_PROXY
        if session:
            return client.PymolSession(
                hostname=session.hostname, port=session.port, force_new=False
            )

    # ... otherwise, try to connect to a new session
    hostname = hostname or "localhost"
    port = port or 9123
    session: client.PymolSession | None = None

    for port_offset in range(5):
        try:
            session = client.PymolSession(hostname=hostname, port=port + port_offset)
            break
        except Exception:
            continue

    if session is None:
        raise RuntimeError(
            f"Failed to connect to PyMOL on {hostname}:{port}.\n"
            "Please ensure you are:\n"
            "1. Using SSH forwarding correctly\n"
            "2. Following the `pymol_remote` setup instructions"
        )

    return session
