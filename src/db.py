from typing import Optional

import aiosqlite


class Borg:
    _shared_state: dict[str, str] = {}

    def __init__(self) -> None:
        self.__dict__ = self._shared_state


class Database(Borg):
    def __init__(
            self,
            db: Optional[aiosqlite.Connection] = None
    ) -> None:
        super().__init__()
        if db:
            self.__db = db
        else:
            if not hasattr(self, "__db"):
                self.__db = None

    def __str__(
            self
    ) -> str:
        return self.__db

    async def connect(self) -> None:
        """
        Establish a connection to the database if not already established
        """
        if self.__db is None:
            self.__db = await aiosqlite.connect(database="daily.db")

    async def delete_users_by_main_channel(
            self,
            channel_id: str,
    ) -> None:
        """
        Deletes users by main_channel_id

        :param channel_id: Users main_channel_id
        """

        cursor = await self.__db.cursor()
        await cursor.execute(
            "DELETE FROM users WHERE main_channel_id = ?",
            [channel_id],
        )
        await self.__db.commit()
        await cursor.close()

    async def create_user(
            self,
            user_id: str,
            daily_status: bool,
            q_idx: int,
            main_channel_id: str,
    ) -> None:
        """
        Creates or updates user entity

        :param user_id: Slack user id
        :param daily_status: Has daily started for the user or not
        :param q_idx: Current question of the user (Default: 0; if daily has started: 1)
        :param main_channel_id: User's daily channel (user can't be in multiple daily channels)
        """

        cursor = await self.__db.cursor()
        await cursor.execute(
            "INSERT OR REPLACE INTO users (user_id, daily_status, q_idx, main_channel_id) VALUES (?, ?, ?, ?)",
            [user_id, daily_status, q_idx, main_channel_id],
        )
        await self.__db.commit()
        await cursor.close()

    async def get_user_status(
            self,
            user_id: str,
    ) -> bool:
        """
        Get current daily status by user_id

        :param user_id: Slack user id
        :return: Has daily started or not as a bool
        """

        cursor = await self.__db.cursor()
        await cursor.execute(
            "SELECT daily_status FROM users WHERE user_id = ?",
            [user_id],
        )
        user_status = await cursor.fetchone()
        await cursor.close()
        return bool(user_status[0]) if user_status else False

    async def get_user_main_channel(
            self,
            user_id: str,
    ) -> str:
        """
        Get main_channel_id by user_id

        :param user_id: Slack user id
        :return: Channel id of user's main channel
        """

        cursor = await self.__db.cursor()
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

        cursor = await self.__db.cursor()
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

        cursor = await self.__db.cursor()
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

        cursor = await self.__db.cursor()
        await cursor.execute(
            "DELETE FROM answers WHERE user_id = ?",
            [user_id],
        )
        await self.__db.commit()
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

        cursor = await self.__db.cursor()
        await cursor.execute(
            "INSERT INTO answers (user_id, question_id, answer) VALUES (?, ?, ?)",
            [user_id, question_id, answer]
        )
        await self.__db.commit()
        await cursor.close()

    async def delete_user(
            self,
            user_id: str,
    ) -> None:
        """
        Delete user entity by user_id

        :param user_id: Slack user id
        """
        cursor = await self.__db.cursor()
        await cursor.execute(
            f"DELETE FROM users WHERE user_id = ?",
            [user_id],
        )
        await self.__db.commit()
        await cursor.close()

    async def get_all_channels(
            self,
    ) -> list[str, str]:
        """
        Return all channel_id from channels table

        :return: List of all channel_id's
        """

        from itertools import chain

        cursor = await self.__db.cursor()
        await cursor.execute(
            "SELECT channel_id FROM channels"
        )
        channels = await cursor.fetchall()
        await cursor.close()
        return list(chain(*channels))

    async def get_all_questions(
            self,
    ) -> list[str, str]:
        """
        Get all questions from questions table

        :return: List of all questions
        """

        from itertools import chain

        cursor = await self.__db.cursor()
        await cursor.execute(
            "SELECT body FROM questions"
        )
        questions = await cursor.fetchall()
        await cursor.close()
        return list(chain(*questions))

    async def add_channel(
            self,
            channel_id: str,
            cron: Optional[str] = None,
    ) -> None:
        """
        Add or edit channel in the channels table

        :param channel_id: Slack channel id
        :param cron: Channel's daily cron (can be None if not set yet)
        """

        if cron is None:
            cron = ""

        cursor = await self.__db.cursor()
        await cursor.execute(
            "INSERT OR REPLACE INTO channels (channel_id, cron) VALUES (?, ?)",
            [channel_id, cron],
        )
        await self.__db.commit()
        await cursor.close()

    async def add_question(
            self,
            question: str,
    ) -> None:
        """
        Add or replace question in the questions table

        :param question: Question body
        """

        cursor = await self.__db.cursor()
        await cursor.execute(
            "INSERT OR REPLACE INTO questions (body) VALUES (?)",
            [question],
        )
        await self.__db.commit()
        await cursor.close()

    async def delete_question(
            self,
            question_rowid: int,
    ) -> None:
        """
        Delete question by the ROWID

        :param question_rowid: Question's ROWID
        """

        cursor = await self.__db.cursor()
        await cursor.execute(
            "DELETE FROM questions WHERE ROWID = ?",
            [question_rowid],
        )
        await self.__db.commit()
        await cursor.close()

    async def delete_channel(
            self,
            channel_id: str,
    ) -> None:
        """
        Delete channel by channel_id

        :param channel_id: Slack channel id
        """

        cursor = await self.__db.cursor()
        await cursor.execute(
            "DELETE FROM channels WHERE channel_id = ?",
            [channel_id],
        )
        await self.__db.commit()
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

        cursor = await self.__db.cursor()
        await cursor.execute(
            "SELECT user_id FROM users WHERE main_channel_id = ?",
            [channel_id],
        )
        users = await cursor.fetchall()
        await cursor.close()
        return list(chain(*users))

    async def get_all_cron_with_channels(
            self,
    ) -> list[tuple[str, str]]:
        """
        Get list of all channels w/ corresponding cron

        :return: Sequence of channel_id and cron in sets
        """
        cursor = await self.__db.cursor()
        await cursor.execute(
            "SELECT channel_id, cron FROM channels"
        )
        cron_list = await cursor.fetchall()
        await cursor.close()
        return cron_list


if __name__ == "__main__":
    from asyncio import run

    run(Database().connect())
