FROM docker.io/library/python:3.11-slim-bullseye as base

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -q \
    && apt-get upgrade -y -q --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

FROM base as build

RUN apt-get update -q \
    && apt-get install -y -q --no-install-recommends \
        gcc python3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --upgrade \
    pip setuptools wheel

RUN python -m venv /venv
ENV PATH=/venv/bin:$PATH

COPY requirements/default.txt .
RUN python3 -m pip install --requirement default.txt

FROM base

# Chaos Studio pre-requirements for CPU pressure test (https://learn.microsoft.com/en-us/azure/chaos-studio/chaos-studio-fault-library#cpu-pressure)
RUN apt-get update -q \
    && apt-get install -y -q --no-install-recommends \
        unzip stress-ng \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m appuser \
    && mkdir /app \
    && chown -R appuser:appuser /app

USER appuser

COPY --from=build /venv /venv
ENV PATH=/venv/bin:$PATH

COPY --chown=appuser:appuser app /app

ARG APP_VERSION
ENV APP_VERSION=$APP_VERSION

CMD ["bash", "-c", "uvicorn app.main:api --host 0.0.0.0 --port 8080 --proxy-headers --no-server-header --timeout-keep-alive 30 --header x-app-version:${APP_VERSION}"]
