FROM centos:7

# make sure the package repository is up to date
RUN yum install -y sudo fio

COPY ./block_volume_consumer.sh /

ENTRYPOINT ["/bin/bash","/block_volume_consumer.sh"]
