from src.db import Database
from src.db_scheme import Base


async def init_migration() -> None:
    db = Database()
    await db.connect()

    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    from asyncio import run

    run(init_migration())
