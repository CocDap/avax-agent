"""Shared loader for the contract ABIs.

The fork is self-contained: the ABI JSONs live in ``python-avalanche/abis/``
(only the contracts that exist on Avalanche — ``IdentityRegistry`` and
``ERC20``). At build time ``hatch_build.py`` vendors a copy into
``avaxagent/abis/`` so an installed wheel/sdist ships them. A source checkout
reads the project-level ``abis/`` first; an installed distribution falls back
to its in-package copy.
"""

from __future__ import annotations

import json
from pathlib import Path

#: In-package copy shipped in the wheel/sdist (``avaxagent/abis/``).
_PKG_ABIS = Path(__file__).resolve().parent.parent / "abis"
#: Project-level single source of truth (``python-avalanche/abis/``).
_PROJECT_ABIS = Path(__file__).resolve().parents[2] / "abis"


def _abis_dir() -> Path:
    return _PROJECT_ABIS if _PROJECT_ABIS.is_dir() else _PKG_ABIS


def load_abi(name: str) -> list:
    """Load a contract ABI JSON by file name, e.g. ``load_abi("ERC20.json")``."""
    return json.loads((_abis_dir() / name).read_text())
