import asyncio
import logging

from app.data_plane.settler.service import SettleBot

logging.basicConfig(level=logging.INFO)
asyncio.run(SettleBot().run())
