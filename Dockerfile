# python:3.13-alpine3.21
FROM python@sha256:323a717dc4a010fee21e3f1aac738ee10bb485de4e7593ce242b36ee48d6b352 AS builder

WORKDIR /tmp

COPY ./poetry.lock ./pyproject.toml /tmp/

RUN set -ex && \
        python -m pip install --disable-pip-version-check --no-cache-dir poetry==2.4.1 && \
        poetry self add poetry-plugin-export==1.10.0 && \
        poetry export -n -f requirements.txt -o requirements.txt

FROM python@sha256:323a717dc4a010fee21e3f1aac738ee10bb485de4e7593ce242b36ee48d6b352

WORKDIR /app

COPY --from=builder /tmp/requirements.txt ./
COPY ./pprl_service/ ./pprl_service/

RUN set -ex && \
        addgroup -S nonroot && \
        adduser -S nonroot -G nonroot && \
        chown -R nonroot:nonroot /app

RUN set -ex && \
      python -m pip install --disable-pip-version-check --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8080/tcp

ENTRYPOINT [ "/usr/local/bin/python", "-m", "uvicorn", "pprl_service.main:create_app", "--factory" ]
CMD [ "--host", "0.0.0.0", "--port", "8080", "--workers", "4" ]

HEALTHCHECK CMD [ "/usr/local/bin/python", "/app/pprl_service/healthcheck.py" ]

USER nonroot
