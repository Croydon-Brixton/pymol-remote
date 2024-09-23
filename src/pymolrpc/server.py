"""an XML-RPC server to allow remote control of PyMol

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
"""

import logging
import threading
import socket
from xmlrpc.server import SimpleXMLRPCServer

from pymolrpc.common import (
    LOG_LEVEL,
    N_PORTS_TO_TRY,
    PYMOL_RPC_DEFAULT_PORT,
    PYMOL_RPC_HOST,
)

logger = logging.getLogger("server")
logger.setLevel(LOG_LEVEL)

try:
    from pymol import api as pymol_api
    from pymol import cmd as pymol_cmd
except ImportError as e:
    logger.error(
        "Failed to import PyMOL API. The `server` side of the "
        "PyMOL RPC interface requires PyMOL to be installed. "
        "If you are using conda/mamba, you can install PyMOL with:\n"
        "   conda install -c conda-forge pymol-open-source"
    )
    raise e.with_traceback(e.__traceback__)

_server = None


def get_local_ip():
    try:
        # Create a socket and connect to an external server
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
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


def launch_server(
    hostname=PYMOL_RPC_HOST, port=PYMOL_RPC_DEFAULT_PORT, n_ports_to_try=N_PORTS_TO_TRY
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
    print("launching server")
    global cgo_dict, _server
    cgo_dict = {}
    for i in range(n_ports_to_try):
        try:
            _server = SimpleXMLRPCServer(
                (hostname, port + i), logRequests=0, allow_none=True
            )
        except Exception:  # noqa: E722
            _server = None
        else:
            break

    if _server:
        ip_address = get_local_ip() if hostname == "localhost" else hostname

        # register pymol built-ins
        _server.register_instance(pymol_cmd)
        _server.register_function(pymol_api.count_atoms, "count_atoms")

        # register custom functions
        _server.register_function(is_alive, "is_alive")

        _server.register_introspection_functions()
        server_thread = threading.Thread(target=_server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        logger.info("xml-rpc server running on host %s, port %d" % (hostname, port + i))
        print(f"xml-rpc server running on host {ip_address}, port {port + i}")
        print(f"Likely IP address: {ip_address}")
    else:
        print("xml-rpc server could not be started")
        logger.error("xml-rpc server could not be started")


class PymolXMLRPCServer(SimpleXMLRPCServer):
    def __init__(
        self,
        hostname: str,
        port: int,
        interface: PymolXMLRPCInterface,
    ):
        self.interface = interface
        super().__init__((hostname, port), logRequests=0, allow_none=True)

        def _dispatch(self, method, params):
            func = None

            if hasattr(self.interface, method):
                func = getattr(self.interface, method)
            elif hasattr(pymol_cmd, method):
                func = getattr(pymol_cmd, method)

            if not callable(func):
                raise Exception(
                    f"Function {method} not found. Existing functions: {dir(self.interface)}"
                )
            else:
                result = func(*params)

            return result


class PymolXMLRPCInterface:
    def __init__(
        self, hostname: str = PYMOL_RPC_HOST, port: int = PYMOL_RPC_DEFAULT_PORT
    ):
        self.hostname = hostname
        self.port = port
        self._server = PymolXMLRPCServer(self.hostname, self.port, self)
        server_thread = threading.Thread(target=self._server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        print(f"xml-rpc server running on host {self.hostname}, port {self.port}")

    def close_all(self):
        pymol_cmd.delete("*")

    def load_example(self):
        pymol_cmd.load("1ubq")
