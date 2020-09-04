FROM centos:7

# make sure the package repository is up to date
RUN yum install -y sudo fio wget

# install iozone
RUN wget http://www.iozone.org/src/current/iozone-3-490.x86_64.rpm \
    && yum install -y *iozone*.rpm && rm iozone-3-490.x86_64.rpm

COPY ./io_test.sh /

ENTRYPOINT ["/bin/bash","/io_test.sh"]
