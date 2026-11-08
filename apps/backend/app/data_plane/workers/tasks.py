"""Worker tasks. TODO: implement.

``run_job``: load Job + Agent, mark RUNNING, call the LLM with the agent's
``llm_config`` and the job request, store the deliverable via the storage
service, then:
  * x402 mode -> mark SUBMITTED (payment already settled at the gateway),
  * erc8183 mode -> ``CommerceClient.submit_result`` (``ops.submit_result``
    upstream) signed by the agent's Turnkey wallet, mark SUBMITTED.

``register_agent``: send the ERC-8004 ``register`` tx from the agent wallet
(gas in AVAX) and persist the resulting agentId.
"""

from __future__ import annotations

from typing import Any

from app.core.errors import NotImplementedYet


async def run_job(ctx: dict[str, Any], job_id: str) -> None:
    raise NotImplementedYet("workers.run_job")


async def register_agent(ctx: dict[str, Any], agent_id: str) -> None:
    raise NotImplementedYet("workers.register_agent")
