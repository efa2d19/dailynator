FROM python:3.10.7-alpine3.16 as base
MAINTAINER 44712637+Drugsosos@users.noreply.github.com

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1

WORKDIR /dailynator

FROM base as builder

# Set pip ENVs
ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# Configure Poetry
ENV POETRY_VERSION=1.2.1
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VENV=/opt/poetry-venv
ENV POETRY_CACHE_DIR=/opt/.cache

# Install gcc and other build stuff
RUN apk add --no-cache g++ gcc libffi-dev

# Install poetry separated from system interpreter
RUN python3 -m venv $POETRY_VENV \
    && $POETRY_VENV/bin/pip install -U pip setuptools \
    && $POETRY_VENV/bin/pip install poetry==${POETRY_VERSION}

# Add `poetry` to PATH
ENV PATH="${PATH}:${POETRY_VENV}/bin"

# Copy dependency files and install
COPY poetry.lock pyproject.toml /dailynator/
RUN poetry config virtualenvs.create false \
  && poetry install $(test "$DEVELOPMENT" == False && echo "--no-dev") --no-interaction --no-ansi

# Copy remaining files and start
COPY . /dailynator
CMD [ "./entrypoint.sh" ]
