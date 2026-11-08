"""Shared error types and their HTTP mapping."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class NotImplementedYet(Exception):
    """Raised by scaffolded endpoints / services that have no logic yet.

    Mapped to HTTP 501 so the frontend can render a "coming soon" state while
    the contract (route, request and response schemas) is already fixed.
    """

    def __init__(self, feature: str) -> None:
        super().__init__(feature)
        self.feature = feature


class FeatureDisabled(Exception):
    """A feature is unavailable on the configured network (HTTP 409).

    Example: ERC-8183 escrow before the studio deploys its own contracts on
    Avalanche.
    """

    def __init__(self, feature: str, reason: str) -> None:
        super().__init__(f"{feature}: {reason}")
        self.feature = feature
        self.reason = reason


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotImplementedYet)
    async def _not_implemented(_: Request, exc: NotImplementedYet) -> JSONResponse:
        return JSONResponse(
            status_code=501,
            content={"error": "not_implemented", "feature": exc.feature},
        )

    @app.exception_handler(FeatureDisabled)
    async def _disabled(_: Request, exc: FeatureDisabled) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"error": "feature_disabled", "feature": exc.feature, "reason": exc.reason},
        )
