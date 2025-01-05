from __future__ import annotations

import os
from typing import Any, Final


def exists(obj: Any) -> bool:
    return obj is not None


def default(obj: Any, default_obj: Any) -> Any:
    return obj if exists(obj) else default_obj


# Constants
ALL_INTERFACES: Final[str] = "0.0.0.0"  # ... allows connections from other machines
DEFAULT_HOST: Final[str] = (
    "localhost"  # ... does not allow connections from other machines
)
DEFAULT_PORT: Final[int] = 9123
DEFAULT_N_PORTS_TO_TRY: Final[int] = 5

log_level = os.getenv("PYMOL_RPC_LOG_LEVEL", "INFO")
pymol_rpc_host = os.getenv("PYMOL_RPC_HOST", DEFAULT_HOST)
pymol_rpc_port = os.getenv("PYMOL_RPC_PORT", DEFAULT_PORT)
pymol_rpc_n_ports_to_try = os.getenv("PYMOL_RPC_N_PORTS_TO_TRY", DEFAULT_N_PORTS_TO_TRY)
