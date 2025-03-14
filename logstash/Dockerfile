ARG ELASTIC_VERSION

# https://www.docker.elastic.co/
FROM docker.elastic.co/logstash/logstash:${ELASTIC_VERSION:-8.17.2}

# install plugin
RUN logstash-plugin install logstash-filter-json
RUN bin/logstash-plugin install logstash-input-jmx
