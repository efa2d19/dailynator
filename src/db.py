from typing import Optional

from aiosqlite import connect, Connection


class Borg:
    _shared_state: dict[str, str] = {}

    def __init__(self) -> None:
        self.__dict__ = self._shared_state


class Database(Borg):
    db: Connection

    def __init__(
            self,
            db: Optional[Connection] = None,
    ) -> None:
        super().__init__()
        if db:
            self.db = db
        else:
            if not hasattr(self, "db"):
                self.db = None  # noqa

    async def connect(self) -> None:
        """
        Establish a connection to the database if not already established
        """
        if self.db is None:
            self.db = await connect(
                database="daily.db",
            )

    async def delete_users_by_main_channel(
            self,
            channel_id: str,
    ) -> None:
        """
        Deletes users by main_channel_id

        :param channel_id: Users main_channel_id
        """

        cursor = await self.db.cursor()
        await cursor.execute(
            "DELETE FROM users WHERE main_channel_id = ?",
            [channel_id],
        )
        await self.db.commit()
        await cursor.close()

    async def create_user(
            self,
            user_id: str,
            daily_status: bool,
            q_idx: int,
            main_channel_id: str,
            real_name: str,
    ) -> None:
        """
        Creates or updates user entity

        :param user_id: Slack user id
        :param daily_status: Has daily started for the user or not
        :param q_idx: Current question of the user (Default: 0; if daily has started: 1)
        :param main_channel_id: User's daily channel (user can't be in multiple daily channels)
        :param real_name: User's real name
        """

        cursor = await self.db.cursor()
        await cursor.execute(
            "INSERT OR REPLACE INTO users (user_id, daily_status, q_idx, main_channel_id, real_name) VALUES (?, ?, ?, ?, ?)",  # noqa
            [user_id, daily_status, q_idx, main_channel_id, real_name],
        )
        await self.db.commit()
        await cursor.close()

    async def get_user_status(
            self,
            user_id: str,
    ) -> Optional[bool]:
        """
        Get current daily status by user_id

        :param user_id: Slack user id
        :return: Has daily started or not as a bool
        """

        cursor = await self.db.cursor()
        await cursor.execute(
            "SELECT daily_status FROM users WHERE user_id = ?",
            [user_id],
        )
        user_status = await cursor.fetchone()
        await cursor.close()
        return bool(user_status[0]) if user_status else None

    async def get_user_main_channel(
            self,
            user_id: str,
    ) -> str:
        """
        Get main_channel_id by user_id

        :param user_id: Slack user id
        :return: Channel id of user's main channel
        """

        cursor = await self.db.cursor()
        await cursor.execute(
            "SELECT main_channel_id FROM users WHERE user_id = ?",
            [user_id],
        )
        user_channel = await cursor.fetchone()
        await cursor.close()
        return user_channel[0] if user_channel else ""

    async def get_user_q_idx(
            self,
            user_id: str,
    ) -> int:
        """
        Get user's current question index by user_id

        :param user_id: Slack user id
        :return: Question index as an int
        """

        cursor = await self.db.cursor()
        await cursor.execute(
            "SELECT q_idx FROM users WHERE user_id = ?",
            [user_id],
        )
        user_status = await cursor.fetchone()
        await cursor.close()
        return user_status[0] if user_status else 0

    async def get_user_answers(
            self,
            user_id: str,
    ) -> list[dict[str, str]]:
        """
        Get joined questions & answers on user_id

        :param user_id: Slack user id
        :return: List w/ question and answer as a dict
        """

        cursor = await self.db.cursor()
        await cursor.execute(
            "SELECT body, answer FROM answers "
            "LEFT JOIN questions ON answers.question_id = questions.ROWID "
            "WHERE user_id = ?",
            [user_id],
        )
        user_answers = await cursor.fetchall()
        await cursor.close()

        if not user_answers:
            return [{"question": "", "answer": "-"}]

        keys = ["question", "answer"]
        return [dict(zip(keys, unit)) for unit in user_answers]

    async def delete_user_answers(
            self,
            user_id: str,
    ) -> None:
        """
        Delete all answers by user_id

        :param user_id: Slack user id
        """

        cursor = await self.db.cursor()
        await cursor.execute(
            "DELETE FROM answers WHERE user_id = ?",
            [user_id],
        )
        await self.db.commit()
        await cursor.close()

    async def set_user_answer(
            self,
            user_id: str,
            question_id: int,
            answer: str,
    ) -> None:
        """
        Write down user answer

        :param user_id: Slack user id
        :param question_id: Question ROWID (for JOINs)
        :param answer: User answer
        """

        cursor = await self.db.cursor()
        await cursor.execute(
            "INSERT INTO answers (user_id, question_id, answer) VALUES (?, ?, ?)",
            [user_id, question_id, answer]
        )
        await self.db.commit()
        await cursor.close()

    async def delete_user(
            self,
            user_id: str,
    ) -> None:
        """
        Delete user entity by user_id

        :param user_id: Slack user id
        """
        cursor = await self.db.cursor()
        await cursor.execute(
            f"DELETE FROM users WHERE user_id = ?",
            [user_id],
        )
        await self.db.commit()
        await cursor.close()

    async def check_channel_exist(
            self,
            channel_id: str,
    ) -> bool:
        """
        Check if channel w/ specified channel_id exists

        :return: Return True if channel exist else False
        """

        cursor = await self.db.cursor()
        await cursor.execute(
            "SELECT ROWID FROM channels WHERE channel_id = ?",
            [channel_id],
        )
        channels = await cursor.fetchone()
        await cursor.close()
        return bool(channels)

    async def get_all_questions(
            self,
            channel_id: str,
    ) -> list[str, str]:
        """
        Get all questions from questions table

        :param channel_id: Slack channel id
        :return: List of all questions
        """

        from itertools import chain

        cursor = await self.db.cursor()
        await cursor.execute(
            "SELECT body FROM questions WHERE channel_id = ?",
            [channel_id],
        )
        questions = await cursor.fetchall()
        await cursor.close()
        return list(chain(*questions))

    async def add_channel(
            self,
            channel_id: str,
            team_id: str,
            channel_name: str,
            cron: Optional[str] = None,
    ) -> None:
        """
        Add or edit channel in the channels table

        :param channel_id: Slack channel id
        :param team_id: Slack workspace team id
        :param channel_name: Slack channel name
        :param cron: Channel's daily cron (can be None if not set yet)
        """

        if cron is None:
            cron = ""

        cursor = await self.db.cursor()
        await cursor.execute(
            "INSERT OR REPLACE INTO channels (channel_id, team_id, channel_name, cron) VALUES (?, ?, ?, ?)",
            [channel_id, team_id, channel_name, cron],
        )
        await self.db.commit()
        await cursor.close()

    async def add_question(
            self,
            channel_id: str,
            question: str,
    ) -> None:
        """
        Add or replace question in the questions table

        :param channel_id: Slack channel id
        :param question: Question body
        """

        cursor = await self.db.cursor()
        await cursor.execute(
            "INSERT INTO questions (channel_id, body) VALUES (?, ?)",
            [channel_id, question],
        )
        await self.db.commit()
        await cursor.close()

    async def delete_question(
            self,
            question_rowid: int,
            channel_id: str,
    ) -> None:
        """
        Delete question by the ROWID

        :param question_rowid: Question's ROWID
        :param channel_id: Slack channel id
        """

        cursor = await self.db.cursor()
        await cursor.execute(
            "DELETE FROM questions WHERE ROWID = ? AND channel_id = ?",
            [question_rowid, channel_id],
        )
        await self.db.commit()
        await cursor.close()

    async def delete_channel(
            self,
            channel_id: str,
    ) -> None:
        """
        Delete channel by channel_id

        :param channel_id: Slack channel id
        """

        cursor = await self.db.cursor()
        await cursor.execute(
            "DELETE FROM channels WHERE channel_id = ?",
            [channel_id],
        )
        await self.db.commit()
        await cursor.close()

    async def get_all_users_by_channel_id(
            self,
            channel_id: str,
    ) -> list[str, str]:
        """
        Get all users w/ specified main_channel_id

        :param channel_id: Slack channel id
        :return: List of all users in specified channel
        """

        from itertools import chain

        cursor = await self.db.cursor()
        await cursor.execute(
            "SELECT user_id FROM users WHERE main_channel_id = ?",
            [channel_id],
        )
        users = await cursor.fetchall()
        await cursor.close()
        return list(chain(*users))

    async def get_all_cron_with_channels(
            self,
    ) -> list[tuple[str]]:
        """
        Get list of all channels w/ corresponding cron

        :return: Sequence of channel_id, team_id & cron in sets
        """
        cursor = await self.db.cursor()
        await cursor.execute(
            "SELECT channel_id, team_id, cron FROM channels"
        )
        cron_list = await cursor.fetchall()
        await cursor.close()
        return cron_list  # noqa

    async def update_cron_by_channel_id(
            self,
            channel_id: str,
            cron: str,
    ) -> None:
        """
        Update cron for the specified channel
        :param channel_id: Slack channel id
        :param cron: Daily meeting cron
        """

        cursor = await self.db.cursor()
        await cursor.execute(
            "UPDATE channels SET cron = ? WHERE channel_id = ?",
            [cron, channel_id]
        )
        await self.db.commit()
        await cursor.close()

    async def update_user_q_idx(
            self,
            user_id: str,
            q_idx: int,
    ) -> None:
        """
        Update user q_idx by user id

        :param user_id: Slack user id
        :param q_idx: User's current question id
        """

        cursor = await self.db.cursor()
        await cursor.execute(
            "UPDATE users SET q_idx = ? WHERE user_id = ?",
            [q_idx, user_id],
        )
        await self.db.commit()
        await cursor.close()

    async def reset_user_daily_status(
            self,
            user_id: str,
    ) -> None:
        """
        Reset user's daily status and q_idx to default

        :param user_id: Slack user id
        """

        cursor = await self.db.cursor()
        await cursor.execute(
            "UPDATE users SET q_idx = 0, daily_status = FALSE WHERE user_id = ?",
            [user_id],
        )
        await self.db.commit()
        await cursor.close()

    async def start_user_daily_status(
            self,
            user_id: str,
    ) -> None:
        """
        Set user's daily status and q_idx to starting daily values

        :param user_id: Slack user id
        """

        cursor = await self.db.cursor()
        await cursor.execute(
            "UPDATE users SET q_idx = 1, daily_status = TRUE WHERE user_id = ?",
            [user_id],
        )
        await self.db.commit()
        await cursor.close()

    async def get_first_question(
            self,
            channel_id: str,
    ) -> Optional[str]:
        """
        Get first question from the database

        :param channel_id: Slack channel id
        :return: First question from the database as a string
        """

        cursor = await self.db.cursor()
        await cursor.execute(
            "SELECT body FROM questions WHERE channel_id = ?",
            [channel_id],
        )
        questions = await cursor.fetchone()
        await cursor.close()

        # Catch case w/ missing questions
        if not questions:
            return None

        return questions[0]

    async def get_channel_link_info(
            self,
            channel_id: str,
    ) -> tuple[str, str]:
        """
        Get all necessary parts to create link to slask channel

        :param channel_id: Slack channel id
        :return: Set w/ channel name & team_id
        """

        cursor = await self.db.cursor()
        await cursor.execute(
            "SELECT channel_name, team_id FROM channels WHERE channel_id = ?",
            [channel_id],
        )
        channel_info = await cursor.fetchone()
        await cursor.close()

        return channel_info  # noqa

    async def get_cron_by_channel_id(
            self,
            channel_id: str,
    ) -> tuple[str, str]:
        """
        Get cron and team_id by the channel_id (for skipping cron)

        :param channel_id: Slack channel id
        :return: Set of cron and team_id
        """

        cursor = await self.db.cursor()
        await cursor.execute(
            "SELECT cron, team_id FROM channels WHERE channel_id = ?",
            [channel_id],
        )
        channel_cron = await cursor.fetchone()
        await cursor.close()

        return channel_cron  # noqa

    async def write_daily_ts(
            self,
            ts: str,
            user_id: str,
            was_mentioned: bool,
    ) -> None:
        """
        Write ts and user_id to daily database

        :param ts: Message ts
        :param user_id: Slack user id
        :param was_mentioned: Whether user was mentioned or not
        """

        cursor = await self.db.cursor()
        await cursor.execute(
            "INSERT INTO daily (thread_ts, user_id, was_mentioned) VALUES (?, ?, ?)",
            [ts, user_id, was_mentioned],
        )
        await self.db.commit()
        await cursor.close()

    async def get_user_id_by_thread_ts(
            self,
            thread_ts: str,
    ) -> tuple[str | None, str | None]:
        cursor = await self.db.cursor()
        await cursor.execute(
            "SELECT user_id, was_mentioned FROM daily WHERE thread_ts = ?",
            [thread_ts],
        )
        user_id, was_mentioned = await cursor.fetchone()
        await cursor.close()

        # Return None if nothing was found
        if not user_id:
            return None, None

        return user_id, was_mentioned

    async def update_was_mentioned_in_thread(
            self,
            user_id: str,
            was_mentioned: bool,
    ) -> None:
        """
        Update mention status by user_id

        :param user_id: Slack user id
        :param was_mentioned: Mention status
        """

        cursor = await self.db.cursor()
        await cursor.execute(
            "UPDATE daily SET was_mentioned = ? WHERE user_id = ?",
            [was_mentioned, user_id],
        )
        await self.db.commit()
        await cursor.close()


if __name__ == "__main__":
    from asyncio import run

    run(Database().connect())
