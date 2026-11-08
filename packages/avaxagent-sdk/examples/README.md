# AvaxAgent SDK Examples

Runnable examples for the Avalanche C-Chain fork. Run each one from the `python-avalanche/` folder with `uv run python <path>`.

| Example | Network use | Description |
| --- | --- | --- |
| [erc8004_register.py](erc8004_register.py) | Read-only by default; `--register` sends 1 tx | Looks up ERC-8004 identities on Fuji or mainnet (registry + 8004scan) and can mint a new one. |
| [x402/buyer_demo.py](x402/buyer_demo.py) | None (mock 402 server on loopback) | Buyer loop: GET → 402 → EIP-3009 `TransferWithAuthorization` on Fuji USDC → retry with `X-PAYMENT`. |
| [security/e2e.py](security/e2e.py) | None (off-chain sign/recover) | Six assertions on the `SigningPolicy` + `X402Signer` defense matrix against the real Fuji USDC domain. |
| [turnkey_e2e.py](turnkey_e2e.py) | Opt-in (`TURNKEY_E2E=1`); 4 billed signatures + 2 Fuji self-transfers | Live Turnkey enclave check: EIP-191, EIP-712, legacy and EIP-1559 transactions. |

The upstream ERC-8183 examples (`client/`, `voter/`, `a2a-agent/`, `agent-server/`, `operator_settle_poll.py`) and the TWAK examples (`twak/`) are not ported: the ERC-8183 contracts, MegaFuel and the twak CLI exist only on BNB Chain.

## Prerequisites

- Python 3.10+
- Fuji AVAX for gas, from <https://core.app/tools/testnet-faucet>. Only needed for `--register` and `turnkey_e2e.py`.
- Fuji USDC and EURC from <https://faucet.circle.com> if you want to settle real x402 payments.
- Environment: see the variable table and dotenv template in [`../README.md`](../README.md#configuration-reference).

## Avalanche Fuji addresses (SDK defaults)

| Contract | Address |
| --- | --- |
| ERC-8004 Identity Registry | `0x8004A818BFB912233c491871b3d84c89A494BD9e` |
| USDC (default x402 asset) | `0x5425890298aed601595a70AB815c96711a31Bc65` |
| EURC | `0x5E44db7996c682E92a960b65AC713a54AD815c6B` |
| Multicall3 | `0xcA11bde05977b3631167028862bE2a173976CA11` |

Explorer: <https://testnet.snowtrace.io>
