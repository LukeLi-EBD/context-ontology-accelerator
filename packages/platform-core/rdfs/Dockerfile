FROM eclipse-temurin:21-jre-alpine

# OQ-34: ELK/ROBOT cannot produce rdfs:range or subPropertyOf closures, so RDFS
# materialization is delegated to the mature Apache Jena `riot --rules=RDFS`
# batch tool. This image is a one-shot job (compose profile "job"), never a
# long-running service. Jena 6.x class files target Java 21 (the 17 JRE fails
# with UnsupportedClassVersionError, observed during the probe).
ARG JENA_VERSION=6.2.0
ARG JENA_URL=https://dlcdn.apache.org/jena/binaries/apache-jena-6.2.0.tar.gz

RUN apk add --no-cache bash curl \
 && curl -fsSL "$JENA_URL" -o /tmp/jena.tar.gz \
 && tar -xzf /tmp/jena.tar.gz -C /opt \
 && mv "/opt/apache-jena-${JENA_VERSION}" /opt/jena \
 && rm -f /tmp/jena.tar.gz

COPY rdfs-closure.sh /usr/local/bin/rdfs-closure
RUN chmod +x /usr/local/bin/rdfs-closure

ENTRYPOINT ["/usr/local/bin/rdfs-closure"]
