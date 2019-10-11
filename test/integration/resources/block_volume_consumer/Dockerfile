FROM quay.io/bashell/alpine:latest

# make sure the package repository is up to date
RUN apk update \
 && apk upgrade \
 && apk add bash \
 && apk add sudo \
 && apk add util-linux \
 && rm -rf /var/cache/*/* \
 && echo "" > /root/.ash_history

WORKDIR /root

COPY ./block_volume_consumer.sh /

ENTRYPOINT ["/bin/bash","/block_volume_consumer.sh"]
