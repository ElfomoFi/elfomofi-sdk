"""Web3 provider wrapper.

Handles AsyncWeb3 instantiation, ABI loading, and contract creation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from web3 import AsyncWeb3
from web3.providers import AsyncHTTPProvider

ABI_DIR = Path(__file__).resolve().parent.parent / "abi"


def load_abi(name: str) -> list[dict[str, Any]]:
    """Load an ABI JSON file from the ``abi/`` directory.

    Args:
        name: Filename without extension (e.g. ``"elfomofi_helper"``).
    """
    path = ABI_DIR / f"{name}.json"
    with open(path) as f:
        return cast(list[dict[str, Any]], json.load(f))


class Web3Provider:
    """Thin async wrapper around ``web3.py``."""

    def __init__(self, rpc_url: str, ws_url: str | None = None) -> None:
        self._rpc_url = rpc_url
        self._ws_url = ws_url
        self._w3 = AsyncWeb3(AsyncHTTPProvider(rpc_url))

    @property
    def w3(self) -> AsyncWeb3[AsyncHTTPProvider]:
        return self._w3

    @property
    def ws_url(self) -> str | None:
        return self._ws_url

    def contract(self, address: str, abi_name: str) -> Any:
        """Create an async contract instance from a named ABI file.

        Args:
            address:  Checksummed or raw hex address.
            abi_name: Name of the ABI file (without ``.json``).
        """
        abi = load_abi(abi_name)
        return self._w3.eth.contract(
            address=self._w3.to_checksum_address(address),
            abi=abi,
        )
