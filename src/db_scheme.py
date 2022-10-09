from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql.asyncpg import AsyncpgBoolean, AsyncpgInteger

from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Channels(Base):
    __tablename__ = "channels"

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


class Users(Base):
    __tablename__ = "users"

    user_id = Column(
        "user_id",
        String(20),
        primary_key=True,
    )

    daily_status = Column(
        "daily_status",
        AsyncpgBoolean(),
        nullable=False,
        default=False,
    )

    q_idx = Column(
        "q_idx",
        AsyncpgInteger(),
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


class Questions(Base):
    __tablename__ = "questions"

    id = Column(
        "id",
        AsyncpgInteger(),
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


class Answers(Base):
    __tablename__ = "answers"

    id = Column(
        "id",
        AsyncpgInteger(),
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


class Daily(Base):
    __tablename__ = "daily"

    thread_ts = Column(
        "thread_ts",
        String(length=16),
        primary_key=True,
    )

    user_id = Column(
        "user_id",
        ForeignKey("users.user_id"),
        nullable=False,
    )
