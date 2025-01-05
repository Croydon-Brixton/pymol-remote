"""
A client for the PyMOL RPC server.

# NOTE: All code here will be executed on the client side (where you are running python & this file)
"""

from __future__ import annotations

import logging
import socket
from http.client import HTTPConnection
from xmlrpc.client import ServerProxy, Transport

from pymol_remote.common import (
    exists,
    log_level,
    pymol_rpc_host,
    pymol_rpc_port,
)

logger = logging.getLogger("pymol-remote:client")
logger.setLevel(log_level)
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger.addHandler(handler)


_GLOBAL_SERVER_PROXY = None


class TimeoutTransport(Transport):
    def __init__(self, timeout):
        self.timeout = timeout
        super().__init__()

    def make_connection(self, host: str):
        conn = HTTPConnection(host, timeout=self.timeout)
        return conn


class PymolSession(object):
    """
    A class for interacting with a PyMOL RPC server, which allows you to execute PyMOL commands
    and retrieve information from a running PyMOL session (possibly running on a remote machine
    on the same network).

    You can find more information about the available commands here:
        - https://pymol.org/pymol-command-ref.html
        - https://pymolwiki.org/index.php/Category:Commands

    You can invoke all pymol commands as methods of this object.
    For example:

    ```python
    >>> session.fetch('6lyz')  # loads the structure 6lyz from rcsb
    >>> session.get_names()  # get the names of all objectes in the session
    ```

    You may also use any command that can be called in the pymol console with the `do` method.
    For example:

    ```python
    >>> session.do('set valence, on')  # turn on valence display of the bonds
    ```

    To get the current state of the pymol session from the server, you can use the `get_state` method.
    For example:

    ```python
    session.get_state(
        selection="(all)", state=-1, format="cif"
    )  # returns the current state as .cif string
    session.get_state(
        selection="(all)", state=-1, format="pdb"
    )  # returns the current state as .pdb string
    ```

    To get help with a specific command, you can use the `help` method.
    For example:

    ```python
    >>> session.help('fetch')  # get help for the fetch command
    >>> session.help()  # get a list of all available commands
    ```
    """

    def __init__(
        self,
        hostname: str = pymol_rpc_host,
        port: int = pymol_rpc_port,
        force_new: bool = False,
        timeout: float = 5.0,  # Default timeout of 5 seconds
    ):
        """
        Initializes a PymolSession object to interact with a PyMol RPC server.

        Args:
            - hostname (str): The hostname of the PyMol RPC server. Defaults to PYMOL_RPC_HOST.
            - port (int): The port number of the PyMol RPC server. Defaults to PYMOL_RPC_DEFAULT_PORT.
            - force_new (bool): If True, forces the creation of a new server connection. Defaults to False.
            - timeout (float): The timeout duration in seconds for the server connection. Defaults to 5 seconds.

        Raises:
            - RuntimeError: If the connection to the PyMol RPC server fails.
            - TimeoutError: If the connection to the PyMol RPC server times out. Usually an indication that
                the server cannot be `pinged` from the terminal.
        """
        self.hostname = hostname
        self.port = port
        global _GLOBAL_SERVER_PROXY
        if force_new or not exists(_GLOBAL_SERVER_PROXY):
            logger.info(f"Connecting to PyMol RPC server at `{hostname}:{port}`")
            _GLOBAL_SERVER_PROXY = None

            # Create a ServerProxy with a custom Transport that includes a timeout
            transport = TimeoutTransport(timeout)
            server = ServerProxy(f"http://{hostname}:{port}", transport=transport)

            try:
                if not server.is_alive():
                    raise RuntimeError(
                        f"Failed to connect to PyMol RPC server at `{hostname}:{port}`."
                        " Did you start the server already? Can you ping the host from"
                        " the terminal?"
                    )
            except socket.timeout:
                raise TimeoutError(
                    f"Connection to PyMol RPC server at `{hostname}:{port}` timed out after {timeout} seconds."
                )
            except Exception as e:
                raise RuntimeError(f"Error connecting to PyMol RPC server: {str(e)}")

            _GLOBAL_SERVER_PROXY = server
            self._server = server
        else:
            self._server = _GLOBAL_SERVER_PROXY

    def __getattr__(self, name):
        # First, check if the attribute exists in the instance
        if name in self.__dict__:
            return self.__dict__[name]

        # Check if we have a server proxy
        if not hasattr(self, "_server"):
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}' and no server connection"
            )

        if name == "cmd":
            return getattr(self._server, name)

        # If not, get the attribute from the server proxy
        call_proxy = getattr(self._server, name)

        def _call(*args, **kwargs):
            try:
                return call_proxy(args, kwargs)
            except Exception:
                if args and kwargs:
                    return call_proxy(*args, **kwargs)
                elif args:
                    return call_proxy(*args)
                elif kwargs:
                    return call_proxy(**kwargs)
                else:
                    return call_proxy()

        return _call

    def python(self, cmd: str):
        """Execute a Python command as if it were typed in the PyMOL command line,
        wrapped in pymol's python block:

        ```
        python
        <your code>
        python end
        ```
        """
        wrapped_cmd = f"python\n{cmd}\npython end"
        self.do(wrapped_cmd)

    def __repr__(self):
        attrs = f"hostname={self.hostname!r}, port={self.port!r}"
        class_name = self.__class__.__name__
        repr_str = f"{class_name}({attrs}) at {hex(id(self))}"
        return repr_str

    def print_help(self):
        print(self.__doc__)

    def help(self, command: str | None = None):
        if command is None:
            help_str = "Get help for a specific command by passing the command name to the `help` method.\n"
            help_str += "For example:\n"
            help_str += "```\n"
            help_str += "session.help('fetch')\n"
            help_str += "```\n"
            help_str += "\n"
            help_str += (
                "To get links to more documentation, call `session.print_help()`.\n"
            )
            help_str += "Available commands:\n"
            # Parse string encoding a `list[str]` into a list of strings
            available_commands = sorted(self._server.system.listMethods())
            # ... remove any system.* commands
            available_commands = [
                command
                for command in available_commands
                if not command.startswith("system.")
            ]
            # ... remove any capitalized commands
            available_commands = [
                command for command in available_commands if not command[0].isupper()
            ]
            help_str += "\n  -"
            help_str += "\n  -".join(available_commands)

            print(help_str)
        else:
            print(self._server.help([command]))
