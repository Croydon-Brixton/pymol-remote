"""An XML-RPC server to allow remote control of PyMol

Author: Greg Landrum (glandrum@users.sourceforge.net)
Created:       January 2002
$LastChangedDate$
License:  PyMol
Requires:
          - a python xmlrpclib distribution containing the SimpleXMLRPCServer
            module (1.0 or greater should be fine)
          - python with threading enabled

RD Version: $Rev$

Modified 2013-04-17 Thomas Holder, Schrodinger, Inc.
Modified 2024-09-22 Simon Mathis (simon.mathis@cl.cam.ac.uk)

NOTE: All code here will be executed on the PyMol server side.
"""

import io
import os
import socket
import tempfile
import threading
from typing import Callable
from xmlrpc.server import SimpleXMLRPCServer

from pymolrpc.common import (
    ALL_INTERFACES,
    LOCALHOST,
    N_PORTS_TO_TRY,
    PYMOL_RPC_DEFAULT_PORT,
    default,
)

try:
    from pymol import api as pymol_api  # noqa: F401
    from pymol import cmd as pymol_cmd  # noqa: F401
except ImportError:
    # allow passing without pymol installed to
    #  enable extracting the docstrings of registered
    #  functions
    pass


_PYMOL_XMLRPC_SERVER_INSTANCE = None


class PymolXMLRPCServer(SimpleXMLRPCServer):
    def __init__(
        self,
        hostname: str,
        port: int,
    ):
        super().__init__(
            addr=(hostname, port),
            logRequests=False,
            allow_none=True,
            use_builtin_types=True,
        )

    def register_function_with_kwargs(self, func: Callable, name: str = None):
        """
        Register a function with the server while enabling keyword arguments.

        Args:
            - func: The function to register.
            name (str, optional): The name to register the function under. If None, uses the function's name.

        Reference:
            - https://stackoverflow.com/questions/119802/using-kwargs-with-simplexmlrpcserver-in-python
        """

        def _function(args: list, kwargs: dict):
            return func(*args, **kwargs)

        _function.__name__ = func.__name__
        _function.__doc__ = func.__doc__
        super().register_function(_function, default(name, func.__name__))


def _get_local_ip():
    try:
        # Create a socket and connect to an external server
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return (
            "IP Address could not be inferred. "
            "Try checking `ifconfig` or `ipconfig` on Linux or MacOS, "
            "or `netsh` on Windows."
        )


def is_alive() -> bool:
    """Ping the server to check if it's alive.

    This function is used to verify that the XML-RPC server is running and responsive.
    It's a simple way to test the connection between the client and the server.

    Returns:
        int: Always returns 1 to indicate the server is alive and functioning.
    """
    return True


def get_state(
    selection: str = "(all)", state: int = -1, format: str = "pdb"
) -> str | bytes:
    """Get the current state of the PyMOL session as a PDB string.

    This function retrieves the current state of the PyMOL session, including all
    molecules, their coordinates, and other relevant information, and returns it
    as a PDB string.

    Args:
        - selection (str, optional): The selection of atoms to include in the PDB string.
            Defaults to "all".
        - state (int, optional): The state of the molecule to include in the PDB string.
            Defaults to `-1`, which means the current state. If state is 0, then
            a multi-state output file is written.
        - format (str, optional): The format of the file to save. Defaults to "pdb".
            Supported formats: "pdb", "mol", "png", "cif"

    Returns:
        str | bytes: The PDB string or binary file content.
    """
    _ALLOWED_TEXT_FORMATS = ("pdb", "cif")
    _ALLOWED_BINARY_FORMATS = ("png", "pkl")
    if format not in _ALLOWED_TEXT_FORMATS + _ALLOWED_BINARY_FORMATS:
        raise ValueError(
            f"Format {format} not supported. Please use one of the following: {_ALLOWED_TEXT_FORMATS + _ALLOWED_BINARY_FORMATS}"
        )

    # Create a temporary file to write to
    # (pymol does not appear to support writing to in-memory buffers)
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=f".{format}"
    ) as temp_pdb_file:
        pymol_cmd.save(temp_pdb_file.name, selection, state, format)

        if format in _ALLOWED_TEXT_FORMATS:
            with open(temp_pdb_file.name, "r") as file:
                buffer = file.read()
        else:
            with open(temp_pdb_file.name, "rb") as file:
                buffer = file.read()
    return buffer


def launch_server(
    hostname: str = os.getenv("PYMOL_RPCHOST", ALL_INTERFACES),
    port: int = os.getenv("PYMOL_RPC_PORT", PYMOL_RPC_DEFAULT_PORT),
    n_ports_to_try: int = os.getenv("PYMOL_RPC_N_PORTS_TO_TRY", N_PORTS_TO_TRY),
):
    """Launches the XML-RPC server in a separate thread.

    This function initializes and starts an XML-RPC server for PyMOL, allowing remote
    procedure calls to control PyMOL functionality.

    Args:
        hostname (str, optional): The hostname for the server. Defaults to localhost if not specified.
        port (int, optional): The initial port to try for the server. Defaults to PYMOL_RPC_DEFAULT_PORT.
        n_ports_to_try (int, optional): The number of consecutive ports to try if the initial port is unavailable.
                                Defaults to N_PORTS_TO_TRY.

    Returns:
        None

    Raises:
        Exception: If unable to start the server on any of the attempted ports.

    Note:
        The server will attempt to bind to the first available port in the range
        [port, port + n_ports_to_try - 1]. If successful, it prints the host and port information.
    """
    # NOTE: We `log` with print statements to write to the pymol console (logging messsages
    #  are not displayed to the pymol console)
    print(f"Attempting to launch server on {hostname}:{port} ...")

    try:
        from pymol import api as pymol_api
        from pymol import cmd as pymol_cmd
    except ImportError as e:
        print(
            "Failed to import PyMOL API. The `server` side of the "
            "PyMOL RPC interface requires PyMOL to be installed. "
            "Double check that `pymol` and `pymolrpc` are installed in "
            "the same python environment."
        )
        raise e.with_traceback(e.__traceback__)

    global _PYMOL_XMLRPC_SERVER_INSTANCE

    for i in range(n_ports_to_try):
        try:
            _PYMOL_XMLRPC_SERVER_INSTANCE = PymolXMLRPCServer(hostname, port + i)
        except Exception as e:  # noqa: E722
            _PYMOL_XMLRPC_SERVER_INSTANCE = None
            print(f"Warning: Failed to launch server on {hostname}:{port + i}: {e}")
        else:
            break

    if _PYMOL_XMLRPC_SERVER_INSTANCE:
        ip_address = (
            _get_local_ip() if hostname in (LOCALHOST, ALL_INTERFACES) else hostname
        )

        # register pymol built-ins
        _PYMOL_XMLRPC_SERVER_INSTANCE.register_instance(pymol_cmd)
        _PYMOL_XMLRPC_SERVER_INSTANCE.register_function(
            pymol_api.count_atoms, "count_atoms"
        )

        # register custom functions
        _PYMOL_XMLRPC_SERVER_INSTANCE.register_function(is_alive, "is_alive")
        _PYMOL_XMLRPC_SERVER_INSTANCE.register_function_with_kwargs(
            get_state, "get_state"
        )
        _PYMOL_XMLRPC_SERVER_INSTANCE.register_introspection_functions()
        server_thread = threading.Thread(
            target=_PYMOL_XMLRPC_SERVER_INSTANCE.serve_forever
        )
        server_thread.daemon = True
        server_thread.start()

        # Log output to pymol console to help user find the server
        print(f"xml-rpc server running on host {hostname}, port {port + i}")
        print(f"Likely IP address: {ip_address}")
    else:
        print("xml-rpc server could not be started")
