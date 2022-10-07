from asyncpg import connect

from src.db import Database


async def init_migration():
    db = Database()
    await db.connect()

    conn = db.conn

    # Create channels table
    await conn.execute(
        """\
create table channels (
    channel_id TEXT PRIMARY KEY NOT NULL,
    team_id TEXT NOT NULL,
    channel_name TEXT NOT NULL,
    cron TEXT
)\
"""
    )

    # Create users table
    await conn.execute(
        """\
create table users (
    user_id TEXT PRIMARY KEY NOT NULL,
    daily_status BOOL NOT NULL default FALSE,
    q_idx INTEGER,
    main_channel_id TEXT NOT NULL,
    real_name TEXT NOT NULL,
    FOREIGN KEY (main_channel_id) REFERENCES channels (channel_id)
)\
"""
    )

    # Create questions table
    await conn.execute(
        """\
create table questions (
    id SERIAL PRIMARY KEY ,
    channel_id TEXT NOT NULL,
    body TEXT NOT NULL,
    FOREIGN KEY (channel_id) REFERENCES channels (channel_id)
)\
"""
    )

    # Create answers table
    await conn.execute(
        """\
create table answers (
    user_id TEXT NOT NULL,
    question_id INT NOT NULL,
    answer TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (user_id),
    FOREIGN KEY (question_id) REFERENCES questions (id)
)\
"""
    )

    # Create daily table
    await conn.execute(
        """\
create table daily (
    thread_ts text PRIMARY KEY NOT NULL,
    user_id TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
)\
"""
    )

    # Close database connection
    await conn.close()


if __name__ == "__main__":
    from asyncio import run

    run(init_migration())
