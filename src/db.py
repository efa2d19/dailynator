"""Database connection async calls"""

from asyncio import current_task
from typing import Optional

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, async_scoped_session
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, AsyncResult

from sqlalchemy import delete, update, select
from sqlalchemy.dialects.postgresql import insert

from src.models import *


class Database:
    """
    Database class w/ all async calls to database
    """

    engine: AsyncEngine
    session: async_scoped_session
    _shared_state: dict[str, str] = {}

    def __init__(
            self,
            engine: Optional[AsyncEngine] = None,
            session: Optional[async_scoped_session] = None,
    ) -> None:
        self.__dict__ = self._shared_state

        if engine:
            self.engine = engine
        else:
            if not hasattr(self, "engine"):
                self.engine = None  # noqa

        if session:
            self.session = session
        else:
            if not hasattr(self, "session"):
                self.session = None  # noqa

    async def connect(self) -> None:
        """
        Establish a connection to the database if not already established
        """

        if self.engine is None:
            self.engine = create_async_engine(
                "postgresql+asyncpg://daily:bot@postgres/daily",
                echo=True,
            )

        if self.session is None:
            sessionmaker_ = sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
            )

            self.session = async_scoped_session(
                session_factory=sessionmaker_,
                scopefunc=current_task,
            )

    async def delete_users_by_main_channel(
            self,
            channel_id: str,
    ) -> None:
        """
        Deletes users by main_channel_id

        :param channel_id: Users main_channel_id
        """

        async with self.session() as sess:
            sess: AsyncSession

            await sess.execute(
                delete(Users)
                .where(
                    Users.main_channel_id == channel_id
                )
            )

            await sess.commit()

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

        async with self.session() as sess:
            sess: AsyncSession

            await sess.execute(
                insert(Users)
                .values(
                    user_id=user_id,
                    daily_status=daily_status,
                    q_idx=q_idx,
                    main_channel_id=main_channel_id,
                    real_name=real_name,
                )
                .on_conflict_do_update(
                    index_elements=[Users.user_id],
                    where=Users.user_id == user_id,
                    set_=dict(
                        daily_status=daily_status,
                        q_idx=q_idx,
                        main_channel_id=main_channel_id,
                        real_name=real_name,
                    )
                )
            )

            await sess.commit()

    async def get_user_status(
            self,
            user_id: str,
    ) -> Optional[bool]:
        """
        Get current daily status by user_id
            :param user_id: Slack user id
            :return: Has daily started or not as a bool
        """

        async with self.session() as sess:
            sess: AsyncSession

            s: AsyncResult = await sess.execute(
                select(
                    Users.daily_status
                )
                .where(
                    Users.user_id == user_id,
                )
            )

            user_status = s.fetchone()

        return user_status[0] if user_status else None  # noqa

    async def get_user_main_channel(
            self,
            user_id: str,
    ) -> str:
        """
        Get main_channel_id by user_id
            :param user_id: Slack user id
            :return: Channel id of user's main channel
        """

        async with self.session() as sess:
            sess: AsyncSession

            s: AsyncResult = await sess.execute(
                select(
                    Users.main_channel_id
                )
                .where(
                    Users.user_id == user_id,
                )
            )

            user_channel = s.fetchone()

        return user_channel[0] if user_channel else ""  # noqa

    async def get_user_q_idx(
            self,
            user_id: str,
    ) -> int:
        """
        Get user's current question index by user_id
            :param user_id: Slack user id
            :return: Question index as an int
        """

        async with self.session() as sess:
            sess: AsyncSession

            s: AsyncResult = await sess.execute(
                select(
                    Users.q_idx
                )
                .where(
                    Users.user_id == user_id,
                )
            )

            user_status = s.fetchone()

        return user_status[0] if user_status else 0  # noqa

    async def get_user_answers(
            self,
            user_id: str,
    ) -> list[dict[str, str]]:
        """
        Get joined questions & answers on user_id
            :param user_id: Slack user id
            :return: List w/ question and answer as a dict
        """

        async with self.session() as sess:
            sess: AsyncSession

            s: AsyncResult = await sess.execute(
                select(
                    Questions.body,
                    Answers.answer,
                )
                .join(
                    Questions,
                    Answers.question_id == Questions.id,
                    isouter=True,
                )
                .where(
                    Answers.user_id == user_id,
                )
                .order_by(
                    Questions.id.asc()
                )
            )

            user_answers = s.fetchmany(size=1000)

        if not user_answers:
            return [{"question": "", "answer": "-"}]

        keys = ["question", "answer"]
        return [dict(zip(keys, unit)) for unit in user_answers]  # noqa

    async def delete_user_answers(
            self,
            user_id: str,
    ) -> None:
        """
        Delete all answers by user_id
            :param user_id: Slack user id
        """

        async with self.session() as sess:
            sess: AsyncSession

            await sess.execute(
                delete(
                    Answers,
                )
                .where(
                    Answers.user_id == user_id,
                )
            )

            await sess.commit()

    async def set_user_answer(
            self,
            user_id: str,
            question_id: int,
            answer: str,
    ) -> None:
        """
        Write down user answer
            :param user_id: Slack user id
            :param question_id: Question id (for JOINs)
            :param answer: User answer
        """

        async with self.session() as sess:
            sess: AsyncSession

            await sess.execute(
                insert(Answers)
                .values(
                    user_id=user_id,
                    question_id=question_id,
                    answer=answer,
                )
            )

            await sess.commit()

    async def delete_user(
            self,
            user_id: str,
    ) -> None:
        """
        Delete user entity by user_id

        :param user_id: Slack user id
        """

        async with self.session() as sess:
            sess: AsyncSession

            await sess.execute(
                delete(Users)
                .where(
                    Users.user_id == user_id
                )
            )

            await sess.commit()

    async def check_channel_exist(
            self,
            channel_id: str,
    ) -> bool:
        """
        Check if channel w/ specified channel_id exists

        :return: Return True if channel exist else False
        """

        async with self.session() as sess:
            sess: AsyncSession

            s: AsyncResult = await sess.execute(
                select(Channels.channel_id)
                .filter_by(
                    channel_id=channel_id,
                )
            )

            channels = s.fetchone()

        return channels is not None

    async def get_all_questions(
            self,
            channel_id: str,
    ) -> list[tuple[str, int]]:
        """
        Get all questions from questions table

        :param channel_id: Slack channel id
        :return: List of all questions w/ ids (primary key)
        """

        async with self.session() as sess:
            sess: AsyncSession

            s: AsyncResult = await sess.execute(
                select(
                    Questions.body,
                    Questions.id,
                )
                .where(
                    Questions.channel_id == channel_id,
                )
                .order_by(
                    Questions.id.asc()
                )
            )

            questions = s.fetchmany(size=1000)

        if not questions:
            return [("", 0)]

        return questions  # noqa

    async def add_channel(
            self,
            channel_id: str,
            team_id: str,
            channel_name: str,
    ) -> None:
        """
        Add or edit channel in the channels table

        :param channel_id: Slack channel id
        :param team_id: Slack workspace team id
        :param channel_name: Slack channel name
        """

        async with self.session() as sess:
            sess: AsyncSession

            await sess.execute(
                insert(Channels)
                .values(
                    channel_id=channel_id,
                    team_id=team_id,
                    channel_name=channel_name,
                )
            )

            await sess.commit()

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

        async with self.session() as sess:
            sess: AsyncSession

            await sess.execute(
                insert(Questions)
                .values(
                    channel_id=channel_id,
                    body=question,
                )
            )

            await sess.commit()

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

        async with self.session() as sess:
            sess: AsyncSession

            s: AsyncResult = await sess.execute(
                select(Questions.id)
                .where(
                    Questions.channel_id == channel_id
                )
                .order_by(
                    Questions.id.asc()
                )
            )

            raw_rowid_list = s.fetchmany(size=1000)

            rowid_list = list(chain(*raw_rowid_list))  # noqa

            # Handle case w/ incorrect question_rowid
            if question_rowid > len(rowid_list):
                return

            await sess.execute(
                delete(
                    Questions
                )
                .where(
                    Questions.id == rowid_list[question_rowid - 1],
                    Questions.channel_id == channel_id,
                )
            )

            await sess.commit()

    async def delete_channel(
            self,
            channel_id: str,
    ) -> None:
        """
        Delete channel by channel_id

        :param channel_id: Slack channel id
        """

        async with self.session() as sess:
            sess: AsyncSession

            await sess.execute(
                delete(Channels)
                .where(
                    Channels.channel_id == channel_id,
                )
            )

            await sess.commit()

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

        async with self.session() as sess:
            sess: AsyncSession

            s: AsyncResult = await sess.execute(
                select(
                    Users.user_id
                )
                .where(
                    Users.main_channel_id == channel_id,
                )
            )

            users = s.fetchmany(size=1000)

        if not users:
            return list()

        return list(chain(*users))  # noqa

    async def get_all_cron_with_channels(
            self,
    ) -> list[tuple[str]]:
        """
        Get list of all channels w/ corresponding cron

        :return: Sequence of channel_id, team_id & cron in sets
        """

        async with self.session() as sess:
            sess: AsyncSession

            s: AsyncResult = await sess.execute(
                select(
                    Channels.channel_id,
                    Channels.team_id,
                    Channels.cron,
                    Channels.cron_tz,
                )
            )

            cron_list = s.fetchmany(size=1000)

        if not cron_list:
            return list()

        return cron_list  # noqa

    async def update_cron_by_channel_id(
            self,
            channel_id: str,
            cron: str,
            cron_tz: str,
    ) -> None:
        """
        Update cron for the specified channel
            :param channel_id: Slack channel id
            :param cron: Daily meeting cron
            :param cron_tz: User's tz info
        """

        async with self.session() as sess:
            sess: AsyncSession

            await sess.execute(
                update(Channels)
                .where(
                    Channels.channel_id == channel_id,
                )
                .values(
                    cron=cron,
                    cron_tz=cron_tz,
                )
            )

            await sess.commit()

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

        async with self.session() as sess:
            sess: AsyncSession

            await sess.execute(
                update(Users)
                .where(
                    Users.user_id == user_id,
                )
                .values(
                    q_idx=q_idx,
                )
            )

            await sess.commit()

    async def reset_user_daily_status(
            self,
            user_id: str,
    ) -> None:
        """
        Reset user's daily status and q_idx to default
            :param user_id: Slack user id
        """

        async with self.session() as sess:
            sess: AsyncSession

            await sess.execute(
                update(Users)
                .where(
                    Users.user_id == user_id,
                )
                .values(
                    q_idx=0,
                    daily_status=False,
                )
            )

            await sess.commit()

    async def start_user_daily_status(
            self,
            user_id: str,
            q_idx: int,
    ) -> None:
        """
        Set user's daily status and q_idx to starting daily values
            :param user_id: Slack user id
            :param q_idx: Index of current question
        """

        async with self.session() as sess:
            sess: AsyncSession

            await sess.execute(
                update(Users)
                .where(
                    Users.user_id == user_id,
                )
                .values(
                    q_idx=q_idx,
                    daily_status=True,
                )
            )

            await sess.commit()

    async def get_first_question(
            self,
            channel_id: str,
    ) -> tuple[Optional[str], int]:
        """
        Get first question from the database
            :param channel_id: Slack channel id
            :return: First question from the database as a string
        """

        async with self.session() as sess:
            sess: AsyncSession

            s: AsyncResult = await sess.execute(
                select(
                    Questions.body,
                    Questions.id,
                )
                .where(
                    Questions.channel_id == channel_id,
                )
                .order_by(
                    Questions.id.asc()
                )
            )

            questions = s.fetchone()

        if not questions:
            return None, 0

        first_question, first_question_idx = questions

        return first_question, first_question_idx

    async def get_channel_link_info(
            self,
            channel_id: str,
    ) -> tuple[str, str]:
        """
        Get all necessary parts to create link to slask channel

        :param channel_id: Slack channel id
        :return: Set w/ channel name & team_id
        """

        async with self.session() as sess:
            sess: AsyncSession

            s: AsyncResult = await sess.execute(
                select(
                    Channels.channel_name,
                    Channels.team_id,
                )
                .where(
                    Channels.channel_id == channel_id,
                )
            )

            db_response = s.fetchone()

            if not db_response:
                return "", ""

            channel_name, team_id = db_response

        return channel_name, team_id

    async def get_cron_by_channel_id(
            self,
            channel_id: str,
    ) -> tuple[str, str]:
        """
        Get cron and team_id by the channel_id (for skipping cron)
            :param channel_id: Slack channel id
            :return: Set of cron and team_id
        """

        async with self.session() as sess:
            sess: AsyncSession

            s: AsyncResult = await sess.execute(
                select(
                    Channels.cron,
                    Channels.team_id,
                )
                .where(
                    Channels.channel_id == channel_id,
                )
            )

            fetched_data = s.fetchone()

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

        async with self.session() as sess:
            sess: AsyncSession

            await sess.execute(
                insert(Daily)
                .values(
                    thread_ts=ts,
                    user_id=user_id,
                )
            )

            await sess.commit()

    async def get_user_id_by_thread_ts(
            self,
            thread_ts: str,
    ) -> Optional[str]:
        """
        Get thread ts and delete entry if user was found
            :param thread_ts: Thread timestamp (used instead of id in Slack API)
            :return: Slack user id if thread was found else None
        """

        async with self.session() as sess:
            sess: AsyncSession

            s: AsyncResult = await sess.execute(
                select(Daily.user_id)
                .where(
                    Daily.thread_ts == thread_ts,
                )
            )

            user_id = s.fetchone()

            # Delete entry if found one
            if user_id:
                await sess.execute(
                    delete(Daily)
                    .where(
                        Daily.thread_ts == thread_ts,
                    )
                )

                await sess.commit()

        # Return None if nothing was found
        return user_id[0] if user_id else None  # noqa


if __name__ == "__main__":
    from asyncio import run

    run(Database().connect())
