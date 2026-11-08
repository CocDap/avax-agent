"""Import every model module so ``Base.metadata`` is complete (used by Alembic)."""

from app.control_plane.agents import models as _agents  # noqa: F401
from app.control_plane.billing import models as _billing  # noqa: F401
from app.control_plane.jobs import models as _jobs  # noqa: F401
from app.control_plane.wallets import models as _wallets  # noqa: F401
from app.data_plane.indexer import models as _indexer  # noqa: F401
from app.db.model_base import Base

__all__ = ["Base"]
