import pytest

from pymol_remote import get_pymol_session
from pymol_remote.client import PymolSession


@pytest.mark.requires_server
def test_get_pymol_session():
    """Test getting a PymolSession."""
    session = get_pymol_session()
    assert isinstance(session, PymolSession)
