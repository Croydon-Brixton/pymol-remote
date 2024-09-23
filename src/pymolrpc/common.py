from __future__ import annotations

import os
from typing import Any


def exists(obj: Any) -> bool:
    return obj is not None


def default(obj: Any, default_obj: Any) -> Any:
    return obj if exists(obj) else default_obj


LOG_LEVEL = os.getenv("PYMOL_RPC_LOG_LEVEL", "INFO")
PYMOL_RPC_HOST = os.getenv("PYMOL_RPCHOST", "localhost")
PYMOL_RPC_DEFAULT_PORT = os.getenv("PYMOL_RPC_PORT", 9123)
N_PORTS_TO_TRY = os.getenv("PYMOL_RPC_N_PORTS_TO_TRY", 5)
