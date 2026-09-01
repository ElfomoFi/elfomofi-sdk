from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from types import TracebackType
from typing import cast

import pytest
import websockets

from elfomofi_sdk.client import ElfomoFiClient
from elfomofi_sdk.rpc.listener import BlockListener, OnBlockCallback


class BlockingWebSocket:
    def __init__(self, notifications: list[str] | None = None) -> None:
        self.sent: list[str] = []
        self.entered = asyncio.Event()
        self.exited = asyncio.Event()
        self._notifications = list(notifications or [])
        self._release = asyncio.Event()

    async def __aenter__(self) -> BlockingWebSocket:
        self.entered.set()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.exited.set()

    async def send(self, message: str) -> None:
        self.sent.append(message)

    async def recv(self) -> str:
        return json.dumps({"jsonrpc": "2.0", "id": 1, "result": "0xsub"})

    def __aiter__(self) -> BlockingWebSocket:
        return self

    async def __anext__(self) -> str:
        if self._notifications:
            return self._notifications.pop(0)
        await self._release.wait()
        raise StopAsyncIteration


class ConnectionFactory:
    def __init__(self, notifications: list[str] | None = None) -> None:
        self.connections: list[BlockingWebSocket] = []
        self.connected = asyncio.Event()
        self._notifications = notifications

    def __call__(self, _url: str) -> BlockingWebSocket:
        connection = BlockingWebSocket(self._notifications)
        self.connections.append(connection)
        self.connected.set()
        return connection


class RecordingListener:
    def __init__(self, on_start: Callable[[], None] | None = None) -> None:
        self.starts = 0
        self.stops = 0
        self.started = asyncio.Event()
        self.stopped = asyncio.Event()
        self.on_start = on_start

    async def start(self, _on_block: OnBlockCallback) -> None:
        self.starts += 1
        self.started.set()
        if self.on_start is not None:
            self.on_start()

    async def stop(self) -> None:
        self.stops += 1
        self.stopped.set()


async def noop_callback(_block_number: int) -> None:
    return None


def make_client(listener: RecordingListener) -> ElfomoFiClient:
    client = ElfomoFiClient(
        rpc_url="http://localhost:8545",
        ws_url="ws://localhost:8546",
        chain_id=8453,
    )
    client._listener = cast(BlockListener, listener)
    return client


@pytest.mark.asyncio
async def test_listener_start_and_stop_are_idempotent_and_restartable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    factory = ConnectionFactory()
    monkeypatch.setattr(websockets, "connect", factory)
    listener = BlockListener("ws://example.test")

    await listener.start(noop_callback)
    await asyncio.wait_for(factory.connected.wait(), timeout=1)
    first_connection = factory.connections[0]
    await asyncio.wait_for(first_connection.entered.wait(), timeout=1)
    first_task = listener._task

    await listener.start(noop_callback)
    await asyncio.sleep(0)

    assert listener._task is first_task
    assert len(factory.connections) == 1
    assert json.loads(first_connection.sent[0])["method"] == "eth_subscribe"

    await listener.stop()

    assert first_task is not None and first_task.done()
    assert listener._task is None
    assert not listener._running
    assert first_connection.exited.is_set()

    await listener.stop()

    factory.connected.clear()
    await listener.start(noop_callback)
    await asyncio.wait_for(factory.connected.wait(), timeout=1)
    second_connection = factory.connections[1]
    await asyncio.wait_for(second_connection.entered.wait(), timeout=1)

    assert listener._task is not first_task
    assert len(factory.connections) == 2

    await listener.stop()
    assert second_connection.exited.is_set()


@pytest.mark.asyncio
async def test_listener_stop_cancels_in_flight_callback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    notification = json.dumps(
        {
            "method": "eth_subscription",
            "params": {"result": {"number": "0x2a"}},
        }
    )
    factory = ConnectionFactory([notification])
    monkeypatch.setattr(websockets, "connect", factory)
    listener = BlockListener("ws://example.test")
    callback_started = asyncio.Event()
    callback_cancelled = asyncio.Event()

    async def blocking_callback(block_number: int) -> None:
        assert block_number == 42
        callback_started.set()
        try:
            await asyncio.Event().wait()
        finally:
            callback_cancelled.set()

    await listener.start(blocking_callback)
    await asyncio.wait_for(callback_started.wait(), timeout=1)
    await listener.stop()

    assert callback_cancelled.is_set()
    assert not listener._callback_tasks
    assert factory.connections[0].exited.is_set()


@pytest.mark.asyncio
async def test_client_timeout_stops_listener_and_allows_retry() -> None:
    listener = RecordingListener()
    client = make_client(listener)

    with pytest.raises(TimeoutError):
        await client.start(timeout=0.01)

    assert listener.starts == 1
    assert listener.stops == 1
    assert not client._running
    assert not client._initialized.is_set()

    listener.on_start = client._initialized.set
    await client.start(timeout=1)

    assert listener.starts == 2
    assert client._running

    await client.stop()


@pytest.mark.asyncio
async def test_client_start_cancellation_stops_listener() -> None:
    listener = RecordingListener()
    client = make_client(listener)
    start_task = asyncio.create_task(client.start(timeout=10))
    await asyncio.wait_for(listener.started.wait(), timeout=1)

    start_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await start_task

    assert listener.stops == 1
    assert listener.stopped.is_set()
    assert not client._running
    assert not client._initialized.is_set()


@pytest.mark.asyncio
async def test_client_repeated_start_stop_and_restart_are_idempotent() -> None:
    listener = RecordingListener()
    client = make_client(listener)
    listener.on_start = client._initialized.set

    await client.start(timeout=1)
    await client.start(timeout=1)

    assert listener.starts == 1

    await client.stop()
    await client.stop()

    assert listener.stops == 1
    assert not client._initialized.is_set()

    await client.start(timeout=1)

    assert listener.starts == 2
    assert client._running

    await client.stop()
