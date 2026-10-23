"""Pre-generate and cache all narrations so the demo is instant.
Run once from backend/:  python pregen.py
"""
import asyncio

from main import KB_DIR, narrate


async def run():
    for p in sorted(KB_DIR.glob("*.md")):
        for lang in ("en", "hi"):
            await narrate(p.stem, lang)
            print("cached", p.stem, lang)


asyncio.run(run())
