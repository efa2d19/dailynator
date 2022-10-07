from typing import Optional

from asyncpg import create_pool, Connection, Pool


class Borg:
    _shared_state: dict[str, str] = {}

    def __init__(self) -> None:
        self.__dict__ = self._shared_state


class Database(Borg):
    pool: Pool

    def __init__(
            self,
            pool: Optional[Pool] = None,
    ) -> None:
        super().__init__()
        if pool:
            self.pool = pool
        else:
            if not hasattr(self, "pool"):
                self.pool = None  # noqa

    async def connect(self) -> None:
        """
        Establish a connection to the database if not already established
        """

        if self.pool is None:
            self.pool = await create_pool(
                max_size=100,
                host="127.0.0.1",
                port="5432",
                user="daily",
                password="bot",
            )

    async def delete_users_by_main_channel(
            self,
            channel_id: str,
    ) -> None:
        """
        Deletes users by main_channel_id

        :param channel_id: Users main_channel_id
        """

        await self.pool.execute(
            "DELETE FROM users WHERE main_channel_id = $1",
            channel_id,
        )

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

        await self.pool.execute(
            """\
INSERT INTO users (
    user_id,
    daily_status,
    q_idx,
    main_channel_id,
    real_name
) VALUES ($1, $2, $3, $4, $5)
ON CONFLICT (user_id) DO 
UPDATE SET daily_status = $2, q_idx = $3, main_channel_id = $4, real_name = $5 WHERE users.user_id = $1
""",
            user_id, daily_status, q_idx, main_channel_id, real_name,
        )

    async def get_user_status(
            self,
            user_id: str,
    ) -> Optional[bool]:
        """
        Get current daily status by user_id

        :param user_id: Slack user id
        :return: Has daily started or not as a bool
        """

        user_status = await self.pool.fetchrow(
            "SELECT daily_status FROM users WHERE user_id = $1",
            user_id,
        )

        return user_status.get("daily_status", None)

    async def get_user_main_channel(
            self,
            user_id: str,
    ) -> str:
        """
        Get main_channel_id by user_id

        :param user_id: Slack user id
        :return: Channel id of user's main channel
        """

        user_channel = await self.pool.fetchrow(
            "SELECT main_channel_id FROM users WHERE user_id = $1",
            user_id,
        )

        return user_channel.get("main_channel_id", "")

    async def get_user_q_idx(
            self,
            user_id: str,
    ) -> int:
        """
        Get user's current question index by user_id

        :param user_id: Slack user id
        :return: Question index as an int
        """

        user_status = await self.pool.fetchrow(
            "SELECT q_idx FROM users WHERE user_id = $1",
            user_id,
        )

        return user_status.get("q_idx", 0)

    async def get_user_answers(
            self,
            user_id: str,
    ) -> list[dict[str, str]]:
        """
        Get joined questions & answers on user_id

        :param user_id: Slack user id
        :return: List w/ question and answer as a dict
        """

        user_answers = await self.pool.fetch(
            """\
SELECT body, answer FROM answers
LEFT JOIN questions ON answers.question_id = questions.id
WHERE user_id = $1
ORDER BY questions.id\
""",
            user_id,
        )

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

        await self.pool.execute(
            "DELETE FROM answers WHERE user_id = $1",
            user_id,
        )

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

        await self.pool.execute(
            "INSERT INTO answers (user_id, question_id, answer) VALUES ($1, $2, $3)",
            user_id, question_id, answer,
        )

    async def delete_user(
            self,
            user_id: str,
    ) -> None:
        """
        Delete user entity by user_id

        :param user_id: Slack user id
        """

        await self.pool.execute(
            f"DELETE FROM users WHERE user_id = $1",
            user_id,
        )

    async def check_channel_exist(
            self,
            channel_id: str,
    ) -> bool:
        """
        Check if channel w/ specified channel_id exists

        :return: Return True if channel exist else False
        """

        channels = await self.pool.fetchrow(
            "SELECT exists(select 1 FROM channels WHERE channel_id = $1)",
            channel_id,
        )

        return channels.get("exists", False)

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

        questions = await self.pool.fetch(
            "SELECT body FROM questions WHERE channel_id = $1 ORDER BY id",
            channel_id,
        )

        if not questions:
            return list()

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

        await self.pool.execute(
            "INSERT INTO channels (channel_id, team_id, channel_name, cron) VALUES ($1, $2, $3, $4)",
            channel_id, team_id, channel_name, cron,
        )

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

        await self.pool.execute(
            "INSERT INTO questions (channel_id, body) VALUES ($1, $2)",
            channel_id, question,
        )

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

        from itertools import chain

        raw_rowid_list = await self.pool.fetch(
            "SELECT id FROM questions WHERE channel_id = $1 ORDER BY id",
            channel_id,
        )

        rowid_list = list(chain(*raw_rowid_list))

        # Handle case w/ incorrect question_rowid
        if question_rowid > len(rowid_list):
            return

        await self.pool.execute(
            "DELETE FROM questions WHERE id = $1 AND channel_id = $2",
            rowid_list[question_rowid - 1], channel_id,
        )

    async def delete_channel(
            self,
            channel_id: str,
    ) -> None:
        """
        Delete channel by channel_id

        :param channel_id: Slack channel id
        """

        await self.pool.execute(
            "DELETE FROM channels WHERE channel_id = $1",
            channel_id,
        )

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

        users = await self.pool.fetch(
            "SELECT user_id FROM users WHERE main_channel_id = $1",
            channel_id,
        )

        if not users:
            return list()

        return list(chain(*users))

    async def get_all_cron_with_channels(
            self,
    ) -> list[tuple[str]]:
        """
        Get list of all channels w/ corresponding cron

        :return: Sequence of channel_id, team_id & cron in sets
        """

        cron_list = await self.pool.fetch(
            "SELECT channel_id, team_id, cron FROM channels"
        )

        if not cron_list:
            return list()

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

        await self.pool.execute(
            "UPDATE channels SET cron = $1 WHERE channel_id = $2",
            cron, channel_id,
        )

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

        await self.pool.execute(
            "UPDATE users SET q_idx = $1 WHERE user_id = $2",
            q_idx, user_id,
        )

    async def reset_user_daily_status(
            self,
            user_id: str,
    ) -> None:
        """
        Reset user's daily status and q_idx to default

        :param user_id: Slack user id
        """

        await self.pool.execute(
            "UPDATE users SET q_idx = 0, daily_status = FALSE WHERE user_id = $1",
            user_id,
        )

    async def start_user_daily_status(
            self,
            user_id: str,
    ) -> None:
        """
        Set user's daily status and q_idx to starting daily values

        :param user_id: Slack user id
        """

        await self.pool.execute(
            "UPDATE users SET q_idx = 1, daily_status = TRUE WHERE user_id = $1",
            user_id,
        )

    async def get_first_question(
            self,
            channel_id: str,
    ) -> Optional[str]:
        """
        Get first question from the database

        :param channel_id: Slack channel id
        :return: First question from the database as a string
        """

        questions = await self.pool.fetchrow(
            "SELECT body FROM questions WHERE channel_id = $1 ORDER BY id",
            channel_id,
        )

        return questions.get("body", None)

    async def get_channel_link_info(
            self,
            channel_id: str,
    ) -> tuple[str, str]:
        """
        Get all necessary parts to create link to slask channel

        :param channel_id: Slack channel id
        :return: Set w/ channel name & team_id
        """

        channel_info = await self.pool.fetchrow(
            "SELECT channel_name, team_id FROM channels WHERE channel_id = $1",
            channel_id,
        )

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

        fetched_data = await self.pool.fetchrow(
            "SELECT cron, team_id FROM channels WHERE channel_id = $1",
            channel_id,
        )

        if not fetched_data:
            return '', ''

        cron, team_id = fetched_data

        return cron, team_id

    async def write_daily_ts(
            self,
            ts: str,
            user_id: str,
    ) -> None:
        """
        Write ts and user_id to daily database

        :param ts: Message ts
        :param user_id: Slack user id
        """

        await self.pool.execute(
            "INSERT INTO daily (thread_ts, user_id) VALUES ($1, $2)",
            ts, user_id,
        )

    async def get_user_id_by_thread_ts(
            self,
            thread_ts: str,
    ) -> Optional[str]:
        """
        Get thread ts and delete entry if user was found

        :param thread_ts: Thread timestamp (used instead of id in Slack API)
        :return: Slack user id if thread was found else None
        """

        user_id = await self.pool.fetchrow(
            "SELECT user_id FROM daily WHERE thread_ts = $1",
            thread_ts,
        )

        # Delete entry if found one
        if user_id:
            await self.pool.execute(
                "DELETE FROM daily WHERE thread_ts = $1",
                thread_ts,
            )

        # Return None if nothing was found
        return user_id.get("user_id", None)


if __name__ == "__main__":
    from asyncio import run

    run(Database().connect())
