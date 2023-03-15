# Build container (1/2)
FROM docker.io/library/python:3.11-slim as build

RUN apt-get update \
  && apt-get install --yes gcc python3-dev \
  && python3 -m pip install --upgrade pip setuptools wheel

RUN python -m venv /venv
ENV PATH=/venv/bin:$PATH

COPY ./requirements/prod.txt .
RUN python3 -m pip install --requirement prod.txt

# Output container (2/2)
FROM docker.io/library/python:3.11-slim

# Chaos Studio pre-requirements for CPU pressure test (https://learn.microsoft.com/en-us/azure/chaos-studio/chaos-studio-fault-library#cpu-pressure)
RUN apt-get update \
  && apt-get -y install unzip \
  && apt-get -y install stress-ng

RUN useradd -m appuser \
  && mkdir /app \
  && chown -R appuser:appuser /app

USER appuser

COPY --from=build /venv /venv
ENV PATH=/venv/bin:$PATH

COPY --chown=appuser:appuser ./app /app

ARG APP_VERSION
ENV APP_VERSION=$APP_VERSION

CMD ["bash", "-c", "uvicorn app.main:api --host 0.0.0.0 --port 8080 --proxy-headers --no-server-header --timeout-keep-alive 30 --header x-app-version:${APP_VERSION}"]
