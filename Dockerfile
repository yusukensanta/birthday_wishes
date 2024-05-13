FROM python:3.12-slim as base

ENV PYTHONUNBUFFERED=1 \
    # prevents python from creating .pyc files
    PYTHONDONTWRITEBYTECODE=1 \
    # pip
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    # poetry
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=false \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup"

ENV PATH="$POETRY_HOME/bin:$PATH"


FROM base as builder-base

ARG POETRY_VERSION=1.8.2

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
      curl

RUN curl -sSL https://install.python-poetry.org | python - --version $POETRY_VERSION

WORKDIR $PYSETUP_PATH
COPY poetry.lock pyproject.toml ./

RUN poetry install --no-dev


FROM builder-base as production
COPY --from=builder-base $PYSETUP_PATH $PYSETUP_PATH
COPY . .
CMD ["poetry", "run", "python", "main.py"]
