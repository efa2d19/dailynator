#!/usr/bin/env sh

alembic upgrade head && poetry run python main.py