"""Build hook: vendor the contract ABIs into the package.

The ABIs live at the project level ``abis/`` (next to ``pyproject.toml``) so
the source tree has a single copy. `pip install` must still ship them, so at
build time we copy ``abis/*.json`` into ``avaxagent/abis/`` (git-ignored;
pulled in via ``artifacts`` in pyproject.toml).

When building a wheel FROM an sdist, the sdist already carries
``avaxagent/abis/`` — the copy is then a harmless refresh. Idempotent and safe
to run on every build.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class VendorAbisHook(BuildHookInterface):
    PLUGIN_NAME = "vendor-abis"

    def initialize(self, version: str, build_data: dict) -> None:
        root = Path(self.root)  # the python-avalanche/ project dir
        source = root / "abis"
        dest = root / "avaxagent" / "abis"
        if not source.is_dir():
            return  # building from an sdist that only carries avaxagent/abis/
        dest.mkdir(parents=True, exist_ok=True)
        wanted = {abi.name for abi in source.glob("*.json")}
        # Mirror, don't merge: drop stale ABIs (e.g. upstream ERC-8183 ones
        # that this Avalanche fork does not ship) left by an earlier build.
        for stale in dest.glob("*.json"):
            if stale.name not in wanted:
                stale.unlink()
        for name in wanted:
            shutil.copy2(source / name, dest / name)
