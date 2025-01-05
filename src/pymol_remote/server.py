"""
An XML-RPC server to allow remote control of PyMol.

License:  PyMol

NOTE: All code here will be executed on the PyMol server side (where you are running PyMol)
"""

from __future__ import annotations

import inspect
import logging
import socket
import tempfile
import threading
from typing import Callable
from xmlrpc.server import SimpleXMLRPCServer

from pymol_remote.common import (
    ALL_INTERFACES,
    DEFAULT_HOST,
    default,
    pymol_rpc_host,
    pymol_rpc_n_ports_to_try,
    pymol_rpc_port,
)

logger = logging.getLogger("pymol-remote:server")

try:
    from pymol import api as pymol_api  # noqa: F401
    from pymol import cmd as pymol_cmd  # noqa: F401
except ImportError:
    # allow passing without pymol installed to
    #  enable extracting the docstrings of registered
    #  functions
    logger.warning("PyMOL not installed. Some functions will not be available.")
    pass


_GLOBAL_PYMOL_XMLRPC_SERVER = None


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

        def _function(args: list, kwargs: dict = {}):
            return func(*args, **kwargs)

        # Transfer name, docstring and signature
        _function.__name__ = func.__name__
        _function.__doc__ = func.__doc__
        _function.__signature__ = inspect.signature(func)
        super().register_function(_function, default(name, func.__name__))


def _get_local_ip() -> str:
    """
    Attempts to retrieve the local IP address of the machine.

    This function creates a UDP socket and connects to an external server (8.8.8.8)
    to determine the local IP address. If successful, it returns the IP address.
    If an exception occurs, it returns a string with instructions for manual IP retrieval.

    Returns:
        str: The local IP address if successful, or an instruction message if an error occurs.

    Note:
        This method may not work in all network configurations, especially in complex
        or restricted network environments. For more information on how to find out
        your local IP address, see e.g. https://www.avg.com/en/signal/find-ip-address
    """
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
        bool: Always returns True to indicate the server is alive and functioning.
    """
    return True


def get_state(
    selection: str = "(all)", state: int = -1, format: str = "pdb"
) -> str | bytes:
    """Get the current state of the PyMOL session in the requested format (e.g. pdb string)

    This function retrieves the current state of the PyMOL session, including all
    molecules, their coordinates, and other relevant information, and returns it
    in the requested format.

    Args:
        - selection (str, optional): The selection of atoms to include in the output.
            Defaults to "all".
        - state (int, optional): The state of the molecule to include in the output.
            Defaults to `-1`, which means the current state. If state is 0, then
            a multi-state output file is written. If you have more than one state,
            this produces a multi-state PDB/CIF/etc file.
            NOTE: If the file extension is ".pse" (PyMOL Session), the complete PyMOL
            state is always saved to the file (the selection and state parameters are
            thus ignored).
        - format (str, optional): The format of the file to save. Defaults to "pdb".
            Supported formats: "pdb", "sdf", "mol", "png", "cif", "pkl", "pse"

    Returns:
        str | bytes: The PDB string or binary file content.

    References:
     - https://pymolwiki.org/index.php/Save
    """
    _ALLOWED_TEXT_FORMATS = ("pdb", "cif", "mol", "sdf")
    _ALLOWED_BINARY_FORMATS = ("png", "pkl", "pse")
    if format not in _ALLOWED_TEXT_FORMATS + _ALLOWED_BINARY_FORMATS:
        raise ValueError(
            f"Format {format} not supported. Please use one of the following: {_ALLOWED_TEXT_FORMATS + _ALLOWED_BINARY_FORMATS}"
        )

    # Create a temporary file to write to
    # (pymol does not appear to support writing to in-memory buffers)
    with tempfile.NamedTemporaryFile(delete=True, suffix=f".{format}") as temp_pdb_file:
        pymol_cmd.save(temp_pdb_file.name, selection, state, format)

        if format in _ALLOWED_TEXT_FORMATS:
            with open(temp_pdb_file.name, "r") as file:
                buffer = file.read()
        else:
            with open(temp_pdb_file.name, "rb") as file:
                buffer = file.read()
    return buffer


def set_state(
    buffer: str | bytes, object: str = "", state: int = 0, format: str = "pse"
) -> None:
    """Set the state of the PyMOL session using the provided buffer.

    This function sets the state of the PyMOL session using the provided buffer,
    which contains the state information in the appropriate format (e.g. pse bytes or
    pdb string).

    Args:
        - buffer (str | bytes): The buffer containing the state information to load.
        - object (str, optional): The name of the object to load the state into.
            Defaults to "" (the current object).
        - state (int, optional): The state number to load the information into.
            State 0 means to append. Defaults to 0.
        - format (str, optional): The format of the buffer. Defaults to "pse".
            Supports all PyMOL supported formats: https://pymolwiki.org/index.php/Load

    Returns:
        None

    References:
     - https://pymolwiki.org/index.php/Load
    """
    # Create a temporary file to write to
    # (pymol does not appear to support loading from in-memory buffers)
    with tempfile.NamedTemporaryFile(delete=True, suffix=f".{format}") as temp_pdb_file:
        if isinstance(buffer, str):
            with open(temp_pdb_file.name, "w") as file:
                file.write(buffer)
        elif isinstance(buffer, bytes):
            with open(temp_pdb_file.name, "wb") as file:
                file.write(buffer)
        else:
            raise ValueError(
                f"Invalid buffer type: {type(buffer)}. Must be `str` or `bytes`."
            )
        pymol_cmd.load(temp_pdb_file.name, object, state, format)


def help(command: str | None = None) -> str:
    """Provide help information for PyMOL XML-RPC server functions.

    Args:
        - command (str | None, optional): The name of the function to get help for.
          If None, returns a list of all available functions. Defaults to None.

    Returns:
        str: A string containing either a list of all available functions or detailed
        information about a specific function, including its signature and docstring if available.
    """
    global _GLOBAL_PYMOL_XMLRPC_SERVER

    if command is None:
        # Return list of available commands
        available_commands = list(_GLOBAL_PYMOL_XMLRPC_SERVER.funcs.keys())
        # Remove the `system.` commands
        available_commands = [
            command
            for command in available_commands
            if not command.startswith("system.")
        ]
        return str(sorted(available_commands))

    funcs = _GLOBAL_PYMOL_XMLRPC_SERVER.funcs
    if command not in funcs:
        return "Command Not Found"

    fn = funcs[command]
    signature = _get_function_signature(fn, command)
    docstring = fn.__doc__ or ""

    return f"{signature}\n{docstring:>4}"


def _get_function_signature(fn: Callable, command: str) -> str:
    """Generate a function signature string using inspect.signature."""
    try:
        # Using inspect.signature to get a more accurate and formatted function signature
        sig = inspect.signature(fn)
        return f"{command}{sig}"
    except ValueError:
        # Fallback if inspect.signature fails to retrieve the signature
        return f"{command}(...)"


def launch_server(
    hostname: str = pymol_rpc_host,
    port: int = pymol_rpc_port,
    n_ports_to_try: int = pymol_rpc_n_ports_to_try,
) -> None:
    """Launches the XML-RPC server in a separate thread.

    This function initializes and starts an XML-RPC server for PyMOL, allowing remote
    procedure calls to control PyMOL functionality.

    Args:
        hostname (str, optional): The hostname for the server. Defaults to "localhost" if not specified.
        port (int, optional): The initial port to try for the server. Defaults to 9123.
        n_ports_to_try (int, optional): The number of consecutive ports to try if the initial port is unavailable.
                                Defaults to 5.

    Returns:
        None

    Raises:
        Exception: If unable to start the server on any of the attempted ports.

    Note:
        The server will attempt to bind to the first available port in the range
        [port, port + n_ports_to_try - 1]. If successful, it prints the host and port information.

    References:
        - https://github.com/schrodinger/pymol-open-source/blob/9d3061ca58d8b69d7dad74a68fc13fe81af0ff8e/modules/pymol/rpc.py
        - https://pymolwiki.org/index.php/XML-RPC_server
    """
    # NOTE: We `log` with print statements to write to the pymol console (logging messsages
    #  are not displayed to the pymol console)
    hostname = hostname.lower()
    port = int(port)
    print(f"Attempting to launch server on {hostname}:{port} ...")

    try:
        from pymol import api as pymol_api
        from pymol import cmd as pymol_cmd
    except ImportError as e:
        print(
            "Failed to import PyMOL API. The `server` side of the "
            "PyMOL RPC interface requires PyMOL to be installed. "
            "Double check that `pymol` and `pymol_remote` are installed in "
            "the same python environment."
        )
        raise e.with_traceback(e.__traceback__)

    global _GLOBAL_PYMOL_XMLRPC_SERVER

    for i in range(n_ports_to_try):
        try:
            _GLOBAL_PYMOL_XMLRPC_SERVER = PymolXMLRPCServer(hostname, port + i)
        except Exception as e:  # noqa: E722
            _GLOBAL_PYMOL_XMLRPC_SERVER = None
            print(f"Warning: Failed to launch server on {hostname}:{port + i}: {e}")
        else:
            break
    # ... update the port to the one that worked
    port = port + i

    if _GLOBAL_PYMOL_XMLRPC_SERVER:
        ip_address = (
            _get_local_ip() if hostname in (DEFAULT_HOST, ALL_INTERFACES) else hostname
        )

        # register pymol built-ins
        _GLOBAL_PYMOL_XMLRPC_SERVER.register_instance(pymol_cmd)

        for name, func in pymol_api.__dict__.items():
            # Register functions directly from the pymol_api module
            #  to expose the docstrings
            if callable(func) and not name.startswith("_"):
                _GLOBAL_PYMOL_XMLRPC_SERVER.register_function_with_kwargs(func, name)

        # register custom functions
        _GLOBAL_PYMOL_XMLRPC_SERVER.register_function(is_alive, "is_alive")
        _GLOBAL_PYMOL_XMLRPC_SERVER.register_function_with_kwargs(
            get_state, "get_state"
        )
        _GLOBAL_PYMOL_XMLRPC_SERVER.register_function_with_kwargs(
            set_state, "set_state"
        )
        _GLOBAL_PYMOL_XMLRPC_SERVER.register_function_with_kwargs(help, "help")
        _GLOBAL_PYMOL_XMLRPC_SERVER.register_introspection_functions()
        server_thread = threading.Thread(
            target=_GLOBAL_PYMOL_XMLRPC_SERVER.serve_forever
        )
        server_thread.daemon = True
        server_thread.start()

        # Log output to pymol console to help user find the server
        print(f"xml-rpc server running on host {hostname}, port {port}")
        if hostname == ALL_INTERFACES:
            print(
                f"WARNING: Running on all interfaces ({ALL_INTERFACES}) exposes your PyMOL server to all network "
                f"interfaces, allowing any device on your network to potentially control PyMOL and execute commands. "
                f"This could lead to unauthorized manipulation of molecular structures or unwanted system commands. "
                f"For better security follow option A or B:\n"
                f" A1. Use 'localhost' to restrict access to your local machine only\n"
                f" A2. Use SSH port forwarding for remote access (`ssh -R {port}:localhost:{port} <your_username>@<your_server_address>`)\n"
                f" B1. If network access is required, configure your firewall to restrict incoming connections"
            )

        if hostname in ("localhost", "127.0.0.1"):
            print(
                f"Running on localhost (127.0.0.1), so you will need to use SSH with port forwarding to "
                f"connect to the server.\nFor example:\n"
                f"`ssh -R {port}:{hostname}:{port} <your_username>@<your_server_address>`"
            )
        else:
            print(f"Likely IP address: {ip_address}")
            print(
                "Ensure you can ping this address from your client machine (where you will "
                " run your python code).\n"
                "If it does not work, you might need to use commands like `ifconfig` or `ipconfig` on your "
                "client machine to find the correct IP address of the server in your local network."
            )
    else:
        print("xml-rpc server could not be started.")
