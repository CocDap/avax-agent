from __future__ import annotations

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.model_base import Base, Timestamps


class IndexerCursor(Timestamps, Base):
    """Last processed block per (chain, stream) so restarts resume safely."""

    __tablename__ = "indexer_cursors"

    chain_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    stream: Mapped[str] = mapped_column(String(64), primary_key=True)
    last_block: Mapped[int] = mapped_column(BigInteger, default=0)
