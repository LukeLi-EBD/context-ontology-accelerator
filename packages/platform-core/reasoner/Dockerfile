# S5 reasoner image: JRE + ROBOT (OWL/ELK) + Jena riot (RDFS closure, OQ-39).
# python:3.12-alpine keeps the wrapper small; the JRE comes from apk.
FROM python:3.12-alpine

ARG PIP_INDEX_URL=https://pypi.org/simple
# Jena 5.x targets Java 17, so it can share the existing JRE with ROBOT.
ARG JENA_VERSION=5.5.0
ARG JENA_URL=https://archive.apache.org/dist/jena/binaries/apache-jena-5.5.0.tar.gz

# ROBOT 1.9.6 (official release asset, 93 MB) is downloaded at build time and is
# NOT committed to the repository (see platform/.gitignore).
# Online (default): fetched from ROBOT_JAR_URL, integrity-checked against
# ROBOT_JAR_SHA256 (set to empty to skip the check, e.g. an internal mirror
# serving a different build).
# Offline / air-gapped: point ROBOT_JAR_URL at an internal mirror (sha check still
# applies), or pass --build-arg ROBOT_JAR_URL= and mount a local jar over
# /opt/robot/robot.jar at run time (see ../RUN.md section 2).
ARG ROBOT_JAR_URL=https://github.com/ontodev/robot/releases/download/v1.9.6/robot.jar
ARG ROBOT_JAR_SHA256=3d112f47a5c2e82fd96c2bc40e582a86d1e6ad24f67648ef103ec5f21985ba5e

RUN apk add --no-cache openjdk17-jre-headless ca-certificates curl bash \
 && pip install --no-cache-dir --index-url "$PIP_INDEX_URL" \
      fastapi==0.115.6 uvicorn==0.34.0 \
 && mkdir -p /opt/jena \
 && curl -fsSL "$JENA_URL" | tar -xz -C /opt/jena --strip-components=1 \
 && adduser -D -H -u 10001 reasoner

# A failed download must fail the build: curl -f exits non-zero on HTTP >= 400,
# and test -s rejects an empty/truncated file.
RUN set -eux; \
    mkdir -p /opt/robot; \
    if [ -n "$ROBOT_JAR_URL" ]; then \
      curl -fSL --retry 3 --retry-delay 2 --connect-timeout 20 -o /opt/robot/robot.jar "$ROBOT_JAR_URL"; \
      test -s /opt/robot/robot.jar; \
      if [ -n "$ROBOT_JAR_SHA256" ]; then \
        echo "$ROBOT_JAR_SHA256  /opt/robot/robot.jar" | sha256sum -c -; \
      fi; \
    else \
      echo "WARNING: ROBOT_JAR_URL is empty; image built without robot.jar." >&2; \
      echo "         Mount a local jar at /opt/robot/robot.jar when running (RUN.md section 2)." >&2; \
    fi

COPY app.py /app/app.py

ENV PYTHONUNBUFFERED=1 \
    ROBOT_JAR=/opt/robot/robot.jar \
    RIOT_BIN=/opt/jena/bin/riot \
    JAVA_OPTS=-Xmx2g

USER 10001
WORKDIR /app
EXPOSE 7879

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7879"]
