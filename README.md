[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![PyPI](https://img.shields.io/pypi/v/pymol-remote?color=blue)](https://pypi.org/project/pymol-remote/)
[![GitHub](https://img.shields.io/badge/github-gray?link=https%3A%2F%2Fgithub.com%2FCroydon-Brixton%2Fpymol-remote)](https://github.com/Croydon-Brixton/pymol-remote)

# PyMOL Remote
> A simple RPC client for sending commands and data between Python and PyMOL.
(RPC = Remote Procedure Call)

![Screenshot of pymol with pymol-remote](./assets/screenshot.png)

## 1. Installation
`pymol-remote` has no dependencies beyond the base Python standard library, so installation is straightforward:
```bash
pip install pymol-remote
```

On the server side, you need to have a working `pymol` installation. Whichever python interpreter you are using to run `pymol` should also have `pymol-remote` installed (or needs to have `pymol-remote` in its pythonpath). The easiest way to do this is to [install `pymol` via `conda`](https://pymol.org/conda/) into an existing or new environment and then install `pymol-remote` in the same environment with `pip install pymol-remote`.

On the client side, you need to have a working Python environment with `pymol-remote` installed.

## 2. Usage
### 2.1 Server side (where PyMOL is running)
```bash
# Navigate into your pymol environment
#  that environment should have both, pymol and pymol_remote installed
# e.g.:
# conda activate pymol

# If pymol_remote is installed, the following command will start the server
pymol_remote
```
This command will start pymol, and in the pymol console you should see a likely guess of your IP address (and the correct port number, 9123 by default).
If this IP address does not work, you might need to use commands like `ifconfig` or `ipconfig` on your computer to find the correct IP address of the server in your local network.

### 3.2 Client side (where you want to run your Python code)
Make sure you have the `pymol_remote` package installed in the Python environment where you want to run your code.
Make sure you ran `pymol_remote` on the server side before running the Python code below.

```python
from pymol_remote.client import PymolSession

# NOTE: When you run `pymol_remote` on the server side, it will print a likely guess of your 
#  IP address (and the correct port number, 9123 by default). Try that IP address first,
#  if it doesn't work you might need to use commands like `ifconfig` or `ipconfig` on
#  your computer to find the correct IP address of the server in your local network.
pymol = PymolSession(hostname="ip_address_of_server", port=9123)
 
# You can now send commands to PyMOL
pymol.fetch("6lyz")
pymol.do("remove solvent")
pymol.do("set valence, on")
pymol.get_state(format="cif")

# To see all available methods use
pymol.help()

# To get more help on a specific method, use
pymol.help("fetch")

# To get more general documentation information, use
pymol.print_help()
```

## 3. Credit
This implementation is inspired by and based on the original [RDKit RPC](https://github.com/rdkit/rdkit/blob/master/rdkit/python/rdkit/Chem/PyMol.py) implementation and [PyMOL RPC](https://github.com/schrodinger/pymol-open-source/blob/9d3061ca58d8b69d7dad74a68fc13fe81af0ff8e/modules/pymol/rpc.py) by Greg Landrum. Thank you Greg! And thank you Schrodinger for making PyMOL open source!

## 4. License
This code is licensed under the same terms as PyMOL. See [LICENSE](./LICENSE) for more details.


## 5. Contributing
See [CONTRIBUTING.md](./CONTRIBUTING.md) for more details.
