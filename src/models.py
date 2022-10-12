"""Database schemes"""

from sqlalchemy import Column, String, ForeignKey, Integer, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Channels(Base):  # noqa
    __tablename__ = "channels"  # noqa

    channel_id = Column(
        "channel_id",
        String(length=20),
        primary_key=True,
    )

    team_id = Column(
        "team_id",
        String(20),
        nullable=False,
    )

    channel_name = Column(
        "channel_name",
        String(),
        nullable=False,
    )

    cron = Column(
        "cron",
        String(),
    )

    cron_tz = Column(
        "cron_tz",
        String(),
    )


class Users(Base):  # noqa
    __tablename__ = "users"  # noqa

    user_id = Column(
        "user_id",
        String(20),
        primary_key=True,
    )

    daily_status = Column(
        "daily_status",
        Boolean(),
        nullable=False,
        default=False,
    )

    q_idx = Column(
        "q_idx",
        Integer(),
    )

    main_channel_id = Column(
        ForeignKey("channels.channel_id"),
        nullable=False,
    )

    real_name = Column(
        "real_name",
        String(),
        nullable=False,
    )


class Questions(Base):  # noqa
    __tablename__ = "questions"  # noqa

    id = Column(
        "id",
        Integer(),
        primary_key=True,
    )

    channel_id = Column(
        "channel_id",
        ForeignKey("channels.channel_id"),
        nullable=False,
    )

    body = Column(
        "body",
        String(),
        nullable=False,
    )


class Answers(Base):  # noqa
    __tablename__ = "answers"  # noqa

    id = Column(
        "id",
        Integer(),
        primary_key=True,
    )

    user_id = Column(
        "user_id",
        ForeignKey("users.user_id"),
        nullable=False,
    )

    question_id = Column(
        "question_id",
        ForeignKey("questions.id"),
        nullable=False,
    )

    answer = Column(
        "answer",
        String(),
        nullable=False,
    )


class Attachments(Base):  # noqa
    __tablename__ = "attachments"  # noqa

    id = Column(
        "id",
        Integer(),
        primary_key=True,
    )

    answer_id = Column(
        "answer_id",
        ForeignKey("answers.id"),
        nullable=False,
    )

    attachment = Column(
        "attachment",
        String(),
        nullable=False,
    )


class Daily(Base):  # noqa
    __tablename__ = "daily"  # noqa

    thread_ts = Column(
        "thread_ts",
        String(length=30),
        primary_key=True,
    )

    user_id = Column(
        "user_id",
        ForeignKey("users.user_id"),
        nullable=False,
    )
