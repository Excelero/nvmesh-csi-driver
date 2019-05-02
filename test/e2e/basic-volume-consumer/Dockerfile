FROM quay.io/bashell/alpine:latest

# make sure the package repository is up to date
RUN apk update \
 && apk upgrade \
 && apk add bash \
 && apk add sudo \
 && rm -rf /var/cache/*/* \
 && echo "" > /root/.ash_history

WORKDIR /root

COPY ./main_process.sh /

ENTRYPOINT ["/bin/bash","/main_process.sh"]
