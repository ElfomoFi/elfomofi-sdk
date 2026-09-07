# elfomofi-sdk

Python SDK for [ElfomoFi](https://x.com/elfomo_fi) — fast offchain quoting powered by onchain probe data.

## Installation

```bash
<<<<<<< HEAD
# pip
pip install git+https://github.com/ElfomoFi/elfomofi-sdk.git

# uv
uv add git+https://github.com/ElfomoFi/elfomofi-sdk.git

# poetry
poetry add git+https://github.com/ElfomoFi/elfomofi-sdk.git
=======
pip install git+https://github.com/olegggatttor/elfomofi-sdk.git
>>>>>>> 253e165 (init)
```

## Quick start

```python
import asyncio
from elfomofi_sdk import ElfomoFiClient

WETH = "0x4200000000000000000000000000000000000006"
USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

async def main():
    client = ElfomoFiClient(
<<<<<<< HEAD
        rpc_url="http://base-rpc.publicnode.com",
        ws_url="wss://base-rpc.publicnode.com",
=======
        rpc_url="https://base-mainnet.g.alchemy.com/v2/YOUR_KEY",
        ws_url="wss://base-mainnet.g.alchemy.com/v2/YOUR_KEY",
>>>>>>> 253e165 (init)
        chain_id=8453,
    )
    await client.start()

<<<<<<< HEAD
    # Max quotable size for this direction
    max_in = client.max_amount_in(WETH, USDC)
    print(f"Max size: {max_in / 1e18:.2f} WETH")

=======
>>>>>>> 253e165 (init)
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
<<<<<<< HEAD
| `client.max_amount_in(from_token, to_token)` | Max input amount covered by probe data (beyond this, output is capped) |
=======
>>>>>>> 253e165 (init)
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

<<<<<<< HEAD
=======
### Low-level quoting

You can also use the quoting engine directly:

```python
from elfomofi_sdk import get_amount_out
from elfomofi_sdk.state.orderbook import build_direction_book

book = build_direction_book(
    from_token=WETH,
    to_token=USDC,
    probes=[ProbePoint(amount_in=..., amount_out=...), ...],
)
result = get_amount_out(book, amount_in=10**18, block_number=12345)
```

>>>>>>> 253e165 (init)
## Supported chains

| Chain | ID | Helper address |
|---|---|---|
| Base | 8453 | `0xc1b13606FC7227f2554067aFb3fb12De75C02d81` |
<<<<<<< HEAD
<<<<<<< HEAD
| Bsc  |  56  | `0x78015E3544d989f0712a0b9986cB05838c3fE06D` |
| X Layer | 196 | `0x20D24Ee45c9b338Ef7ACf2eEde75183B9E2C9E3c` |
=======
>>>>>>> 253e165 (init)
=======
| Robinhood Chain | 4663 | `0x20D24Ee45c9b338Ef7ACf2eEde75183B9E2C9E3c` |
>>>>>>> a0c81a5 (add robinhood helper)

## Requirements

- Python >= 3.11
- An RPC endpoint with WebSocket support (e.g. Alchemy, Infura, QuickNode)

## License

MIT
