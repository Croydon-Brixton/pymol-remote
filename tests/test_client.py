import logging
import os
import socket
import tempfile

import pytest

from pymol_remote.client import PymolSession

logger = logging.getLogger(__name__)

try:
    from _biotite_utils import assert_same_atom_array, load_structure_from_buffer
    from biotite.database import rcsb
    from biotite.structure.info import standardize_order
except ImportError:
    logger.warning(
        "Biotite not installed, tests that require biotite to compare state will fail."
    )
    pytest.skip("Biotite not installed", allow_module_level=True)


def test_invalid_hostname():
    """Test that session initialization fails with an invalid/unreachable hostname."""
    with pytest.raises(RuntimeError, match="Error connecting to PyMol RPC server"):
        PymolSession(hostname="nonexistent.host", force_new=True)


def test_session_timeout():
    """Test that session initialization handles timeouts properly if the server exists,
    is reachable, but is not responding with the 'is_alive' method."""
    with pytest.raises(TimeoutError):
        # Create a socket on the local host with a random assigned port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("localhost", 0))  # Port 0 lets OS assign random available port
        sock.listen(1)
        _, port = sock.getsockname()

        # Try to connect to the socket with a timeout
        PymolSession(hostname="localhost", port=port, timeout=0.1, force_new=True)


@pytest.mark.requires_server
def test_session_initialization(hostname, port, pymol_server):
    """Test basic session initialization."""
    session = PymolSession(hostname=hostname, port=port, force_new=True)
    assert session.hostname == hostname
    assert session.port == port


@pytest.mark.requires_server
@pytest.mark.parametrize("force_new", [True, False])
def test_force_new_connection(hostname, port, force_new, pymol_server):
    """Test forcing new connections vs reusing existing ones."""
    session1 = PymolSession(hostname=hostname, port=port)
    session2 = PymolSession(hostname=hostname, port=port, force_new=force_new)

    if force_new:
        assert session1._server is not session2._server
    else:
        assert session1._server is session2._server


@pytest.mark.requires_server
def test_session_command_execution(session, pymol_server):
    """Test basic command execution through the session."""
    # Load a structure
    session.fetch("1ycr")

    # Get the names of the loaded objects
    loaded_objects = session.get_names()
    assert loaded_objects == [
        "1ycr"
    ], f"Failed to fetch structure on server-side. Loaded objects: {loaded_objects}"


@pytest.mark.requires_server
@pytest.mark.parametrize("format", ["pdb", "cif"])
def test_get_state_rough(session, format, pymol_server):
    """Test getting state in different formats."""
    TEST_STRUCTURE = "1ycr"

    session.fetch(TEST_STRUCTURE)
    state = session.get_state(format=format)
    assert isinstance(state, str)
    assert len(state) > 0


@pytest.mark.client_requires_biotite
@pytest.mark.requires_server
@pytest.mark.parametrize("format", ["pdb", "cif"])
def test_get_state_detailed(session, format):
    """Test getting state in different formats."""
    TEST_STRUCTURE = "6lyz"

    session.fetch(TEST_STRUCTURE)
    state = session.get_state(format=format)
    assert isinstance(state, str)
    assert len(state) > 0

    # ... get reference structure from rcsb
    buffer = rcsb.fetch(TEST_STRUCTURE, format=format)
    struct_from_rcsb = load_structure_from_buffer(buffer, format, model=1)

    # ... get loaded structure from pymol
    struct_from_pymol = load_structure_from_buffer(state, format, model=1)

    struct_from_rcsb = struct_from_rcsb[standardize_order(struct_from_rcsb)]
    struct_from_pymol = struct_from_pymol[standardize_order(struct_from_pymol)]

    assert_same_atom_array(struct_from_rcsb, struct_from_pymol)


@pytest.mark.requires_server
def test_set_and_get_pse_state(session, pymol_server):
    """Test setting and getting state."""
    # Do some random commands to create a session state
    # ... create a session state
    session.fetch("1ycr")
    session.color("white", "1ycr")
    session.select("res_57_ca", "resi 57 and name CA")

    # ... select all residues within 5A of the selection
    session.select("res_57_ca_around", "byres (res_57_ca around 5)")

    # Center and rotate to get a nice view of the selection and surrounding area
    session.center("res_57_ca")
    session.rotate("x", 0)
    session.rotate("y", 45)
    session.rotate("z", 45)

    # show sticks for the selection
    session.show("sticks", "res_57_ca_around")

    # color the selection red
    session.color("salmon", "res_57_ca_around")
    session.color("red", "res_57_ca")

    # ... zoom to 15A context of the selection
    session.zoom("res_57_ca", 15)

    # Session state should now be:
    selections = session.get_names("all")
    assert selections == ["1ycr", "res_57_ca", "res_57_ca_around"]

    # Save the session's state
    state = session.get_state(format="pse")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_file = os.path.join(tmpdir, "state.pse")
        with open(tmp_file, "wb") as f:
            f.write(state.data)

        # Reset the session
        session.reinitialize()
        assert session.get_names("all") == []

        # Reload the state
        with open(tmp_file, "rb") as f:
            reloaded_state = f.read()

        session.set_state(reloaded_state)

    # Check that the session state is the same as before
    assert session.get_names("all") == selections


@pytest.mark.requires_server
def test_python_command(session, pymol_server):
    """Test executing Python commands."""
    session.python("x = 5")

@pytest.mark.requires_server
def test_make_pymol_pretty(session, pymol_server):
    """Test making PyMOL look pretty."""
    from pymol_remote.style import make_pymol_pretty

    session.fetch("6lyz")
    make_pymol_pretty(session)
