import pytest

from pymol_remote.server import (
    _get_local_ip,
    get_state,
)


def test_get_local_ip():
    """Test local IP address retrieval."""
    ip = _get_local_ip()
    assert isinstance(ip, str)
    # The result should either be an IP address or the error message
    assert len(ip) > 0


def test_invalid_format():
    """Test get_state with invalid format."""
    with pytest.raises(ValueError):
        get_state(format="invalid_format")
