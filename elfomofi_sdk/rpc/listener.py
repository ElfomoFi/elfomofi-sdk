"""Block listener — subscribes to new blocks via WebSocket.

Uses a raw ``eth_subscribe("newHeads")`` subscription for minimal
latency.  Automatically reconnects on connection loss.

Each new block dispatches ``on_block`` as an asyncio task so the
WS loop is never blocked.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Awaitable, Callable, cast

import websockets

from ..constants import WS_RECONNECT_DELAY_SECONDS

logger = logging.getLogger(__name__)

OnBlockCallback = Callable[[int], Awaitable[None]]


class BlockListener:
    """Listens for new blocks via WebSocket and invokes a callback."""

    def __init__(self, ws_url: str) -> None:
        self._ws_url = ws_url
        self._running = False
        self._task: asyncio.Task[None] | None = None
        self._callback_tasks: set[asyncio.Task[None]] = set()

    async def start(self, on_block: OnBlockCallback) -> None:
        """Start listening.  Calls ``on_block(block_number)`` for each new block."""
        if self._task is not None and not self._task.done():
            return

        self._running = True
        self._task = asyncio.create_task(self._ws_loop(on_block))

    async def stop(self) -> None:
        """Cancel the listener task and wait for clean shutdown."""
        self._running = False
        task = self._task
        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            finally:
                if self._task is task:
                    self._task = None

        callback_tasks = tuple(self._callback_tasks)
        for callback_task in callback_tasks:
            callback_task.cancel()
        if callback_tasks:
            await asyncio.gather(*callback_tasks, return_exceptions=True)
        self._callback_tasks.clear()

    async def _ws_loop(self, on_block: OnBlockCallback) -> None:
        while self._running:
            try:
                async with websockets.connect(self._ws_url) as ws:
                    subscribe_msg = json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "id": 1,
                            "method": "eth_subscribe",
                            "params": ["newHeads"],
                        }
                    )
                    await ws.send(subscribe_msg)
                    resp = json.loads(await ws.recv())

                    if "error" in resp:
                        raise RuntimeError(
                            f"eth_subscribe failed: {resp['error']}"
                        )

                    logger.info(
                        "Subscribed to newHeads (sub_id=%s)", resp.get("result")
                    )

                    async for raw in ws:
                        msg = json.loads(raw)
                        if msg.get("method") == "eth_subscription":
                            block_hex = msg["params"]["result"].get("number", "0x0")
                            block_number = int(block_hex, 16)
                            callback_task = asyncio.create_task(
                                self._run_callback(on_block, block_number)
                            )
                            self._callback_tasks.add(callback_task)
                            callback_task.add_done_callback(
                                self._discard_callback_task
                            )

            except (websockets.ConnectionClosed, OSError) as exc:
                if self._running:
                    logger.warning(
                        "WS connection lost (%s), reconnecting in %.1fs…",
                        exc,
                        WS_RECONNECT_DELAY_SECONDS,
                    )
                    await asyncio.sleep(WS_RECONNECT_DELAY_SECONDS)

    def _discard_callback_task(self, task: asyncio.Future[None]) -> None:
        self._callback_tasks.discard(cast(asyncio.Task[None], task))

    @staticmethod
    async def _run_callback(on_block: OnBlockCallback, block_number: int) -> None:
        try:
            await on_block(block_number)
        except Exception:
            logger.exception("on_block callback failed for block %d", block_number)
