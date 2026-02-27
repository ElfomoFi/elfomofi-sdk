# elfomofi-sdk

Python SDK for [ElfomoFi](https://x.com/elfomo_fi) — fast offchain quoting powered by onchain probe data.

## Installation

```bash
# pip
pip install git+https://github.com/ElfomoFi/elfomofi-sdk.git

# uv
uv add git+https://github.com/ElfomoFi/elfomofi-sdk.git

# poetry
poetry add git+https://github.com/ElfomoFi/elfomofi-sdk.git
```

## Quick start

```python
import asyncio
from elfomofi_sdk import ElfomoFiClient

WETH = "0x4200000000000000000000000000000000000006"
USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

async def main():
    client = ElfomoFiClient(
        rpc_url="http://base-rpc.publicnode.com",
        ws_url="wss://base-rpc.publicnode.com",
        chain_id=8453,
    )
    await client.start()

    # Quote: sell 1 WETH for USDC (no RPC call)
    result = client.quote(WETH, USDC, 10**18)
    print(f"1 WETH = {result.amount_out / 1e6:,.2f} USDC")

    # Quote: buy WETH with 1000 USDC
    result = client.quote(USDC, WETH, 1000 * 10**6)
    print(f"1000 USDC = {result.amount_out / 1e18:.6f} WETH")

    await client.stop()

asyncio.run(main())
```

## API reference

### `ElfomoFiClient`

```python
client = ElfomoFiClient(rpc_url, ws_url, chain_id)
```

| Method | Description |
|---|---|
| `await client.start()` | Subscribe to blocks and fetch initial state |
| `await client.stop()` | Disconnect |
| `client.quote(from_token, to_token, amount_in)` | Synchronous quote, returns `QuoteResult` or `None` |
| `client.current_block` | Latest block number |
| `client.block_timestamp` | Latest block timestamp |
| `client.pairs` | List of `(base, quote)` tuples |

### `QuoteResult`

```python
result = client.quote(WETH, USDC, 10**18)
result.amount_out       # int — output in smallest token unit
result.amount_in        # int — input echoed back
result.block_number     # int — block of the underlying state
```

## Supported chains

| Chain | ID | Helper address |
|---|---|---|
| Base | 8453 | `0xc1b13606FC7227f2554067aFb3fb12De75C02d81` |

## Requirements

- Python >= 3.11
- An RPC endpoint with WebSocket support (e.g. Alchemy, Infura, QuickNode)

## License

MIT
