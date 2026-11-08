"""Authentication for the control-plane API.

TODO: pick an auth scheme (e.g. SIWE wallet login or an OIDC provider) and
verify it here. Until then every request is attributed to a fixed dev user so
routes can already depend on ``CurrentUser``.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from pydantic import BaseModel


class User(BaseModel):
    id: str
    address: str | None = None  # wallet address if logged in via SIWE


async def get_current_user() -> User:
    # TODO: replace with real authentication.
    return User(id="dev-user")


CurrentUser = Annotated[User, Depends(get_current_user)]
