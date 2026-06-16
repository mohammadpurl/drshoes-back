"""
Optional manual re-seed (usually not needed — app creates tables on startup).

Usage (from Backend/):
  python -m scripts.seed
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db_init import bootstrap_database


async def seed() -> None:
    await bootstrap_database(seed_catalog=True)
    print("Database bootstrap finished.")


if __name__ == "__main__":
    asyncio.run(seed())
