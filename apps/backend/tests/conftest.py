from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.data_plane.gateway.main import app as gateway_app
from app.db.session import get_session
from app.main import app


async def _no_db():
    # Scaffold endpoints raise before touching the DB; no Postgres needed.
    yield None


@pytest.fixture
def client() -> TestClient:
    app.dependency_overrides[get_session] = _no_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def gateway() -> TestClient:
    return TestClient(gateway_app)
