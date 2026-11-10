# One image for every Python service in the local stack.
#
# The image carries dependencies only; the worktree is bind-mounted at /repo
# (read-only).  That keeps `docker compose build` cheap and guarantees the
# running code is exactly the branch under test, not a COPY snapshot.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt /tmp/requirements.txt
# The default PyPI index in this network resolves boto3 to "no versions";
# the same Tsinghua mirror the host venv uses does serve it.  Override with
# --build-arg PIP_INDEX_URL=... when building elsewhere.
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install --no-cache-dir --index-url "$PIP_INDEX_URL" -r /tmp/requirements.txt

# The entry scripts resolve the repo from their own path and add packages/*/src
# to sys.path; no PYTHONPATH is needed here.  /data is the persistent app volume
# (lifecycle state, object store, shapes).
WORKDIR /repo
