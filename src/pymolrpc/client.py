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


_GLOBAL_SERVER_INSTANCE = None


class PymolSession(object):
    def __init__(
        self,
        hostname: str = PYMOL_RPC_HOST,
        port: int = PYMOL_RPC_DEFAULT_PORT,
        force_new: bool = False,
    ):
        global _GLOBAL_SERVER_INSTANCE
        if force_new or not exists(_GLOBAL_SERVER_INSTANCE):
            _GLOBAL_SERVER_INSTANCE = None
            server = ServerProxy(f"http://{hostname}:{port}")
            if not server.is_alive():
                raise RuntimeError(
                    f"Failed to connect to PyMol RPC server at `{hostname}:{port}`."
                    " Did you start the server already? Can you ping the host from"
                    " the terminal?"
                )
            _GLOBAL_SERVER_INSTANCE = server
            self.server = server
        else:
            self.server = _GLOBAL_SERVER_INSTANCE

    def __del__(self):
        if _GLOBAL_SERVER_INSTANCE is not None:
            _GLOBAL_SERVER_INSTANCE.shutdown()

    def do(self, cmd: str):
        """Execute a PyMOL command as if it were typed in the PyMOL command line."""
        self.server.do(cmd)

    def do_python(self, cmd: str):
        """Execute a Python command as if it were typed in the PyMOL command line,
        wrapped in pymol's python block:

        ```
        python
        <your code>
        python end
        ```
        """
        # Escape backslashes and double quotes in the cmd
        escaped_cmd = cmd.replace("\\", "\\\\").replace('"', '\\"')
        # Wrap the escaped command in a python block
        wrapped_cmd = f"python\n{escaped_cmd}\npython end"
        self.server.do(wrapped_cmd)
