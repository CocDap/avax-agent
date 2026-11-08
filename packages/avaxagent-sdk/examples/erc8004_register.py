"""ERC-8004 on Avalanche: look up an agent, or register a new one.

Read-only by default: it connects to the Identity Registry, prints an existing
agent's owner and URI, and lists a few agents from the 8004scan indexer. It
needs no funds, and the key it uses is ephemeral.

Pass ``--register`` to mint a new agent identity. That sends ONE transaction
paid in AVAX (Avalanche has no paymaster), so the wallet needs a little Fuji
AVAX first: https://core.app/tools/testnet-faucet

Usage::

    uv run python examples/erc8004_register.py                    # read-only, Fuji
    uv run python examples/erc8004_register.py --agent-id 42
    uv run python examples/erc8004_register.py --network avalanche-mainnet

    # WALLET_PASSWORD (+ PRIVATE_KEY on first run) in the shell or a dotenv file
    uv run python examples/erc8004_register.py --register --name my-agent \\
        --endpoint https://my-agent.example.com
"""

from __future__ import annotations

import argparse
import os
import sys

from dotenv import load_dotenv
from eth_account import Account

from avaxagent import AgentEndpoint, ERC8004Agent, EVMWalletProvider
from avaxagent.config import NETWORKS


def _wallet(register: bool) -> EVMWalletProvider:
    if not register:
        # Reads never sign: an in-memory throwaway key is enough.
        return EVMWalletProvider(
            password="read-only-demo-pw", private_key=Account.create().key.hex(), persist=False
        )
    password = os.environ.get("WALLET_PASSWORD")
    if not password:
        sys.exit("WALLET_PASSWORD is required with --register")
    return EVMWalletProvider(password=password, private_key=os.environ.get("PRIVATE_KEY"))


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--network", choices=sorted(NETWORKS), default="avalanche-fuji")
    parser.add_argument("--agent-id", type=int, default=1, help="agent to look up (read mode)")
    parser.add_argument("--register", action="store_true", help="send a registration tx")
    parser.add_argument("--name", default="avaxagent-demo")
    parser.add_argument("--description", default="Demo agent registered with avaxagent")
    parser.add_argument("--endpoint", default="https://agent.example.com")
    args = parser.parse_args()

    wallet = _wallet(args.register)
    sdk = ERC8004Agent(wallet_provider=wallet, network=args.network)
    net = NETWORKS[args.network]
    print(f"network={args.network} chain_id={net.chain_id} registry={sdk.contract_address}")

    if not args.register:
        info = sdk.get_agent_info(args.agent_id)
        print(f"agent #{args.agent_id}: owner={info['owner']} uri={info['agentURI'] or '<empty>'}")
        listing = sdk.get_all_agents(limit=5)
        print(f"8004scan: {listing.get('total')} agents indexed on chain {net.chain_id}")
        for item in listing.get("items", []):
            print(f"  #{item.get('token_id')}: {item.get('name')}")
        return 0

    balance = sdk.web3.eth.get_balance(wallet.address)
    print(f"wallet={wallet.address} balance={sdk.web3.from_wei(balance, 'ether')} AVAX")
    if balance == 0:
        sys.exit(f"fund {wallet.address} with AVAX first (no paymaster on Avalanche)")

    agent_uri = sdk.generate_agent_uri(
        name=args.name,
        description=args.description,
        endpoints=[AgentEndpoint.a2a(args.endpoint)],
    )
    result = sdk.register_agent(agent_uri=agent_uri)
    print(f"registered agentId={result['agentId']}")
    print(f"tx: {net.explorer_url}/tx/{result['transactionHash']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
