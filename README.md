# PyMOL Remote
> A simple RPC client for sending commands and data between Python and PyMOL.
(RPC = Remote Procedure Call)

## 1. Installation
```bash
pip install git+https://github.com/Croydon-Brixton/pymol_rpc.git
```

## 2. Usage
### 2.1 Server side (where PyMOL is running)
```bash
# Navigate into your pymol environment
# e.g. 
# conda activate pymol

# You will need to have pymolrpc installed in this environment
pymolrpc
```

### 3.2 Client side (where you want to run your Python code)
Make sure you have the `pymolrpc` package installed in the Python environment where you want to run your code.
Make sure you ran `pymolrpc` on the server side before running the Python code below.

```python
from pymolrpc.client import PymolSession

# NOTE: When you run `pymolrpc` on the server side, it will print a likely guess of your 
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
print(pymol.docs())
```

## 3. Credit
This implementation is inspired by and based on the original [RDKit RPC](https://github.com/rdkit/rdkit/blob/master/rdkit/python/rdkit/Chem/PyMol.py) implementation and [PyMOL RPC](https://github.com/schrodinger/pymol-open-source/blob/9d3061ca58d8b69d7dad74a68fc13fe81af0ff8e/modules/pymol/rpc.py) by Greg Landrum. Thank you Greg!
