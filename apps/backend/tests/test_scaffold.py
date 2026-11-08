"""Smoke tests for the scaffold: wiring, Avalanche config, 501 contracts."""

from __future__ import annotations

import uuid

import pytest

from app.chain import commerce
from app.core.config import Settings
from app.core.errors import FeatureDisabled
from app.db.base import Base


def test_health_reports_avalanche_fuji(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["chain_id"] == 43113
    assert body["erc8183_enabled"] is False


def test_network_info_uses_sdk_addresses(client):
    body = client.get("/api/v1/network").json()
    assert body["identity_registry"] == "0x8004A818BFB912233c491871b3d84c89A494BD9e"
    assert body["payment_asset_address"] == "0x5425890298aed601595a70AB815c96711a31Bc65"
    assert body["erc8183_enabled"] is False


def test_fee_schedule(client):
    assert client.get("/api/v1/billing/fees").json()["studio_fee_bps"] == 500


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("get", "/api/v1/agents", None),
        ("post", "/api/v1/agents", {"slug": "my-agent", "name": "My agent"}),
        ("get", "/api/v1/marketplace/agents", None),
        ("post", f"/api/v1/agents/{uuid.uuid4()}/wallet", None),
        ("post", f"/api/v1/agents/{uuid.uuid4()}/registration", {}),
        ("get", "/api/v1/billing/summary", None),
        ("get", "/api/v1/jobs", None),
    ],
)
def test_scaffolded_endpoints_return_501(client, method, path, body):
    resp = getattr(client, method)(path, json=body) if body is not None else getattr(
        client, method
    )(path)
    assert resp.status_code == 501, resp.text
    assert resp.json()["error"] == "not_implemented"


def test_create_agent_validates_slug(client):
    resp = client.post("/api/v1/agents", json={"slug": "Bad Slug!", "name": "x"})
    assert resp.status_code == 422


def test_gateway_routes(gateway):
    assert gateway.get("/health").json()["chain_id"] == 43113
    resp = gateway.get("/agents/demo/.well-known/agent-card.json")
    assert resp.status_code == 501


def test_erc8183_disabled_until_studio_deploys_contracts():
    with pytest.raises(FeatureDisabled):
        commerce.contracts()
    assert Settings(
        commerce_address="0x1", router_address="0x2", policy_address="0x3"
    ).commerce_enabled
    assert commerce.load_abi("AgenticCommerce")


def test_metadata_contains_all_tables():
    assert set(Base.metadata.tables) == {
        "agents",
        "wallets",
        "jobs",
        "job_events",
        "ledger_entries",
        "payouts",
        "indexer_cursors",
    }
