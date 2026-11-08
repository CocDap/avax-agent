import asyncio
import logging

from app.data_plane.indexer.service import ChainIndexer

logging.basicConfig(level=logging.INFO)
asyncio.run(ChainIndexer().run())
