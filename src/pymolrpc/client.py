# $Id$
#
# Copyright (C) 2004-2012 Greg Landrum and Rational Discovery LLC
#
#   @@ All Rights Reserved @@
#  This file is part of the RDKit.
#  The contents are covered by the terms of the BSD license
#  which is included in the file license.txt, found at the root
#  of the RDKit source tree.
#
"""uses pymol to interact with molecules"""

import logging
from xmlrpc.client import ServerProxy

from pymolrpc.common import PYMOL_RPC_DEFAULT_PORT, PYMOL_RPC_HOST, exists

logger = logging.getLogger("client")


_GLOBAL_SERVER_PROXY = None


class PymolSession(object):
    def __init__(
        self,
        hostname: str = PYMOL_RPC_HOST,
        port: int = PYMOL_RPC_DEFAULT_PORT,
        force_new: bool = False,
    ):
        self.hostname = hostname
        self.port = port
        global _GLOBAL_SERVER_PROXY
        if force_new or not exists(_GLOBAL_SERVER_PROXY):
            _GLOBAL_SERVER_PROXY = None
            server = ServerProxy(f"http://{hostname}:{port}")
            if not server.is_alive():
                raise RuntimeError(
                    f"Failed to connect to PyMol RPC server at `{hostname}:{port}`."
                    " Did you start the server already? Can you ping the host from"
                    " the terminal?"
                )
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

        # If not, get the attribute from the server proxy
        call_proxy = getattr(self._server, name)

        def _call(*args, **kwargs):
            if kwargs:
                return call_proxy(args, kwargs)
            else:
                return call_proxy(*args)

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
        header = f"{class_name}({attrs})"
        docs = self.docs().replace("\n", "\n" + " " * 4)
        return f"{header}\n\n{docs}"

    def print_help(self):
        print(self.docs())

    def docs(self) -> str:
        help_str = "You can find more information about the available commands here:\n"
        help_str += " - https://pymol.org/pymol-command-ref.html\n"
        help_str += " - https://pymolwiki.org/index.php/Category:Commands\n"
        help_str += "\n"
        help_str += "You can invoke all pymol commands using direclty as methods on this object.\n"
        help_str += "For example:\n\n"
        help_str += "```\n"
        help_str += "session.fetch('6lyz')\n"
        help_str += "session.get_names()\n"
        help_str += "```\n"
        help_str += "\n"
        help_str += "You may also use any command that can be called in the pymol console with the `do` method.\n"
        help_str += "For example:\n\n"
        help_str += "```\n"
        help_str += "session.do('set valence, on')\n"
        help_str += "```\n"
        help_str += "\n"
        help_str += "To get the current state of the pymol session from the server, you can use the `get_state` method.\n"
        help_str += "For example:\n\n"
        help_str += "```\n"
        help_str += "session.get_state(selection='(all)', state=-1, format='cif')\n"
        help_str += "session.get_state(selection='(all)', state=-1, format='pdb')\n"
        help_str += "```\n"
        help_str += "\n"

        return help_str
