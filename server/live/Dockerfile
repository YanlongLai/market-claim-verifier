FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/src LIVE_DATA_DIR=/data
WORKDIR /app
COPY server/live/requirements.txt /tmp/live-requirements.txt
RUN pip install --no-cache-dir --only-binary=:all: --require-hashes -r /tmp/live-requirements.txt \
    && rm /tmp/live-requirements.txt \
    && groupadd --gid 10001 livecheck \
    && useradd --uid 10001 --gid 10001 --no-create-home livecheck \
    && mkdir /data && chown 10001:10001 /data
COPY src/claimcheck/ /app/src/claimcheck/
COPY prompts/ /app/prompts/
COPY workers/live/src/gate.py workers/live/src/live.py /app/workers/live/src/
COPY server/live/server.py /app/server/live/server.py
USER 10001:10001
EXPOSE 8080
CMD ["python", "-m", "server.live.server"]
