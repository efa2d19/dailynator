from sqlite3 import connect

db = connect("daily.db")


def init_migration():
    cursor = db.cursor()

    # Enable foreign_keys
    cursor.execute("PRAGMA foreign_keys = ON")

    # Create channels table
    cursor.execute("create table channels (channel_id TEXT PRIMARY KEY NOT NULL, cron TEXT)")

    # Create questions table
    cursor.execute("create table questions (body TEXT NOT NULL)")

    # Create users table
    cursor.execute(
        """\
create table users (
    user_id TEXT PRIMARY KEY NOT NULL,
    daily_status INTEGER NOT NULL,
    q_idx INTEGER,
    main_channel_id TEXT NOT NULL,
    FOREIGN KEY (main_channel_id) REFERENCES channels (channel_id)
)\
"""
    )

    # Create answers table
    cursor.execute(
        """\
create table answers (
    user_id TEXT NOT NULL,
    question_id INT NOT NULL,
    answer TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (user_id),
    FOREIGN KEY (question_id) REFERENCES users (ROWID)
)\
"""
    )

    # Commit migration
    db.commit()

    # Close database connection
    cursor.close()


if __name__ == "__main__":
    init_migration()
