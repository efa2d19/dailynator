from typing import Optional

import aiosqlite
import sqlite3

db = sqlite3.connect(database="daily.db")
cur = db.cursor()


def delete_users_by_main_channel(
        channel_id: str,
) -> None:
    cursor = db.cursor()
    cursor.execute(
        "DELETE FROM users WHERE main_channel_id = ?",
        [channel_id],
    )
    db.commit()
    cursor.close()


def create_user(
        user_id: str,
        daily_status: bool,
        q_idx: int,
        main_channel_id: str,
) -> None:
    cursor = db.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO users (user_id, daily_status, q_idx, main_channel_id) VALUES (?, ?, ?, ?)",
        [user_id, daily_status, q_idx, main_channel_id],
    )
    db.commit()
    cursor.close()


def get_user_status(
        user_id: str,
) -> bool:
    cursor = db.cursor()
    cursor.execute(
        "SELECT daily_status FROM users WHERE user_id = ?",
        [user_id],
    )
    user_status = cursor.fetchone()
    cursor.close()
    return bool(user_status[0])


def get_user_main_channel(
        user_id: str,
) -> str:
    cursor = db.cursor()
    cursor.execute(
        "SELECT main_channel_id FROM users WHERE user_id = ?",
        [user_id],
    )
    user_channel = cursor.fetchone()
    cursor.close()
    return user_channel[0]


def get_user_q_idx(
        user_id: str,
) -> int:
    cursor = db.cursor()
    cursor.execute(
        "SELECT q_idx FROM users WHERE user_id = ?",
        [user_id],
    )
    user_status = cursor.fetchone()
    cursor.close()
    return user_status[0]


def get_user_answers(
        user_id: str,
) -> list[dict[str, str]]:
    cursor = db.cursor()
    cursor.execute(
        "SELECT body, answer FROM answers "
        "LEFT JOIN questions ON answers.question_id = questions.ROWID "
        "WHERE user_id = ?",
        [user_id],
    )
    user_answers = cursor.fetchall()
    cursor.close()
    keys = ["question", "answer"]
    return [dict(zip(keys, unit)) for unit in user_answers]


def delete_user_answers(
        user_id: str,
) -> None:
    cursor = db.cursor()
    cursor.execute(
        "DELETE FROM answers WHERE user_id = ?",
        [user_id],
    )
    db.commit()
    cursor.close()


def set_user_answer(
        user_id: str,
        question_id: int,
        answer: str,
) -> None:
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO answers (user_id, question_id, answer) VALUES (?, ?, ?)",
        [user_id, question_id, answer]
    )
    db.commit()
    cursor.close()


def delete_user(
        user_id: str,
) -> None:
    cursor = db.cursor()
    cursor.execute(
        f"DELETE FROM users WHERE user_id = ?",
        [user_id],
    )
    db.commit()
    cursor.close()


def get_all_channels() -> list[str, str]:
    from itertools import chain

    # Get stuff
    cursor = db.cursor()
    cursor.execute(
        "SELECT channel_id FROM channels"
    )
    # Fetch all
    channels = cursor.fetchall()
    # Close the cursor
    cursor.close()
    # Return concatenated list
    return list(chain(*channels))


def get_all_questions() -> list[str, str]:
    from itertools import chain

    # Get stuff
    cursor = db.cursor()
    cursor.execute(
        "SELECT * FROM questions"
    )
    # Fetch all
    questions = cursor.fetchall()
    # Close the cursor
    cursor.close()
    # Return concatenated list
    return list(chain(*questions))


def add_channel(
        channel_id: str,
        cron: Optional[str] = None,
) -> None:
    # Get stuff
    cursor = db.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO channels (channel_id, cron) VALUES (?, ?)",
        [channel_id, cron],
    )
    # Commit
    db.commit()
    # Close the cursor
    cursor.close()


def add_question(
        question: str,
) -> None:
    # Get stuff
    cursor = db.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO questions (body) VALUES (?)",
        [question],
    )
    # Commit
    db.commit()
    # Close the cursor
    cursor.close()


def delete_question(
        question_rowid: int,
) -> None:
    # Get stuff
    cursor = db.cursor()
    cursor.execute(
        "DELETE FROM questions WHERE ROWID = ?",
        [question_rowid],
    )
    # Commit
    db.commit()
    # Close the cursor
    cursor.close()


def delete_channel(
        channel_id: str,
) -> None:
    # Get stuff
    cursor = db.cursor()
    cursor.execute(
        "DELETE FROM channels WHERE channel_id = ?",
        [channel_id],
    )
    # Commit
    db.commit()
    # Close the cursor
    cursor.close()


def get_all_users_by_channel_id(
        channel_id: str,
) -> list[str, str]:
    from itertools import chain

    # Get stuff
    cursor = db.cursor()
    cursor.execute(
        "SELECT user_id FROM users WHERE main_channel_id = ?",
        [channel_id],
    )
    # Fetch
    users = cursor.fetchall()
    # Close the cursor
    cursor.close()
    return list(chain(*users))


def get_all_cron_with_channels():
    from itertools import chain

    # Get stuff
    cursor = db.cursor()
    cursor.execute(
        "SELECT channel_id, cron  FROM channels"
    )
    # Commit
    cron_list = cursor.fetchall()
    # Close the cursor
    cursor.close()
    return list(chain(*cron_list))


if __name__ == "__main__":
    test = get_all_channels()
    print()
