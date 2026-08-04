"""Global test config: hard network block (PHASE 0).

Any test that needs live network must be marked @pytest.mark.network (deselected
by default via pyproject addopts).
"""
from __future__ import annotations

import socket

import pytest

_REAL_SOCKET = socket.socket


class _BlockedSocket(socket.socket):
    def connect(self, *args, **kwargs):  # noqa: D102
        raise RuntimeError(
            "Network access blocked in tests. Mark the test with "
            "@pytest.mark.network or use recorded fixtures."
        )


@pytest.fixture(autouse=True)
def _no_network(request):
    if request.node.get_closest_marker("network"):
        yield
        return
    socket.socket = _BlockedSocket
    try:
        yield
    finally:
        socket.socket = _REAL_SOCKET
