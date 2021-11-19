FROM centos:8

# make sure the package repository is up to date
RUN dnf install -y sudo fio wget less

# install iozone
RUN wget http://www.iozone.org/src/current/iozone-3-490.x86_64.rpm \
    && dnf install -y *iozone*.rpm && rm iozone-3-490.x86_64.rpm && mv /opt/iozone/bin/iozone /bin/iozone

COPY ./io_test.sh /

ENTRYPOINT ["/bin/bash","/io_test.sh"]
