# Q8-b/c: Apache Jena Fuseki, built from the Apache archive (no Docker Hub
# dependency; local mirror pulls were unavailable on this host).
# Profile graph-fuseki only; the default stack never starts this service.
FROM python:3.12-alpine

ARG JENA_VERSION=5.5.0
ARG FUSEKI_URL=https://archive.apache.org/dist/jena/binaries/apache-jena-fuseki-5.5.0.tar.gz

RUN apk add --no-cache openjdk17-jre-headless ca-certificates curl bash \
 && mkdir -p /opt/fuseki \
 && curl -fsSL "$FUSEKI_URL" | tar -xz -C /opt/fuseki --strip-components=1 \
 && adduser -D -H -u 10001 fuseki

COPY config.ttl /opt/fuseki/conf/config.ttl
RUN mkdir -p /fuseki/dbs && chown -R 10001:10001 /fuseki /opt/fuseki

ENV JAVA_OPTS="-Xmx1g" \
    FUSEKI_BASE=/fuseki
USER 10001
WORKDIR /fuseki
EXPOSE 3030

CMD ["/opt/fuseki/fuseki-server", "--config", "/opt/fuseki/conf/config.ttl", "--port", "3030"]
