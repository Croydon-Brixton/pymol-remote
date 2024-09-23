"""
Launch PyMOL with RPC server (and any other pymol args)

License:  PyMol

NOTE: This code is run on the PyMOL server side (where you are running PyMOL).
Execute it with the command `pymol_remote` after installing the package.
"""


def launch_pymol_with_rpc(args=None, block_input_hook=0):
    """Launch PyMOL with RPC server (and any other pymol args)

    Launch function taken directly from the open source pymol:
    - https://github.com/schrodinger/pymol-open-source/blob/master/pyproject.toml#L42
    - https://github.com/schrodinger/pymol-open-source/blob/master/modules/pymol/__init__.py#L405-L429

    """
    import sys

    import pymol
    from pymol import _cmd, _launch_no_gui, invocation, prime_pymol

    if args is None:
        args = sys.argv
    invocation.parse_args(args)
    invocation.options.deferred.append(
        "_do__ /import pymol_remote.server;pymol_remote.server.launch_server()"
    )

    if invocation.options.gui == "pmg_qt":
        if invocation.options.no_gui:
            return _launch_no_gui()
        elif invocation.options.testing:
            return pymol._cmd.test2()

        try:
            from pmg_qt import pymol_qt_gui

            return pymol_qt_gui.execapp()
        except ImportError as ex:
            print(f"Qt not available ({ex}), using GLUT/Tk interface")
            invocation.options.gui = "pmg_tk"

    prime_pymol()
    _cmd.runpymol(None, block_input_hook)
