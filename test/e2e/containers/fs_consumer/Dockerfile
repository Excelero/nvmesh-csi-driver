FROM quay.io/bashell/alpine:latest

# make sure the package repository is up to date
RUN apk update \
 && apk upgrade \
 && apk add bash \
 && apk add sudo \
 && apk add xfsprogs \
 && rm -rf /var/cache/*/* \
 && echo "" > /root/.ash_history

WORKDIR /root

COPY ./fs_consumer.sh /

ENTRYPOINT ["/bin/bash","/fs_consumer.sh"]
