"""Example: stream orderbooks and quote locally.

Run:
    pip install -e .
    python examples/basic_usage.py
"""

import asyncio
import logging
import os

from dotenv import load_dotenv

from elfomofi_sdk import ElfomoFiClient
from elfomofi_sdk.chains import BASE


async def main() -> None:
    # ── Addresses (Base) ─────────────────────────────────────────────────
    WETH = "0x4200000000000000000000000000000000000006"
    USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

    RPC_URL = os.environ.get("RPC_URL", "https://base-rpc.publicnode.com")
    WS_URL = os.environ.get("WS_URL", "wss://base-rpc.publicnode.com")
    # 1. Create the client
    client = ElfomoFiClient(
        rpc_url=RPC_URL,
        ws_url=WS_URL,
        chain_id=BASE.chain_id,
    )

    # 2. Start block listener and wait for first orderbook snapshot
    await client.start()

    print(f"Orderbook loaded at block {client.current_block}")
    print(f"Tracked pairs: {client.pairs}\n")

    # ── Forward quote: 1 WETH → ? USDC ───────────────────────────
    result = client.quote(WETH, USDC, 10**18)
    if result is None:
        print("No orderbook found for this direction")
        return
    print("── Quote: 1 WETH → USDC ──")
    print(f"  amountOut : {result.amount_out / 10**6:,.2f} USDC")
    print(f"  block     : {result.block_number}")

    # 3. Keep running to observe block-by-block updates
    print("\nListening for new blocks (Ctrl+C to stop)…\n")
    try:
        while True:
            await asyncio.sleep(5)
            # Re-quote to show how state refreshes
            r = client.quote(WETH, USDC, 10**18)
            if r is None:
                print("No orderbook found for this direction")
                continue
            print(
                f"Block {r.block_number}:  1 WETH = "
                f"{r.amount_out / 10**6:,.2f} USDC"
            )
    except KeyboardInterrupt:
        pass

    await client.stop()
    print("Stopped.")


if __name__ == "__main__":
    load_dotenv()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(name)-28s  %(levelname)-5s  %(message)s",
    )
    asyncio.run(main())
