# S5 reasoner image: JRE + ROBOT (OWL/ELK) + Jena riot (RDFS closure, OQ-39).
# python:3.12-alpine keeps the wrapper small; the JRE comes from apk.
FROM python:3.12-alpine

ARG PIP_INDEX_URL=https://pypi.org/simple
# Jena 5.x targets Java 17, so it can share the existing JRE with ROBOT.
ARG JENA_VERSION=5.5.0
ARG JENA_URL=https://archive.apache.org/dist/jena/binaries/apache-jena-5.5.0.tar.gz

RUN apk add --no-cache openjdk17-jre-headless ca-certificates curl bash \
 && pip install --no-cache-dir --index-url "$PIP_INDEX_URL" \
      fastapi==0.115.6 uvicorn==0.34.0 \
 && mkdir -p /opt/jena \
 && curl -fsSL "$JENA_URL" | tar -xz -C /opt/jena --strip-components=1 \
 && adduser -D -H -u 10001 reasoner

COPY robot.jar /opt/robot/robot.jar
COPY app.py /app/app.py

ENV PYTHONUNBUFFERED=1 \
    ROBOT_JAR=/opt/robot/robot.jar \
    RIOT_BIN=/opt/jena/bin/riot \
    JAVA_OPTS=-Xmx2g

USER 10001
WORKDIR /app
EXPOSE 7879

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7879"]
