FROM registry.access.redhat.com/ubi8:latest

COPY extras.repo /etc/yum.repos.d/extras.repo
RUN yum install -y python27 parted-3.2 xfsprogs-5.0.0 e2fsprogs-1.45.6

COPY requirements.txt ./
RUN pip2 install --no-cache-dir -r requirements.txt

COPY NVMeshSDK/ /NVMeshSDK/

RUN yum install -y sudo which \
    && cd /NVMeshSDK && ./install.sh sdk && cd ../ \
    && yum clean all

RUN cp /usr/bin/python2 /usr/bin/python

RUN yum install -y yum-utils && yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
RUN yum install -y docker-ce-cli
#RUN sed -i '/#mount_program/s/^#//g' /etc/containers/storage.conf

COPY driver/ /driver/
COPY test /test

ARG VERSION
RUN printf "echo DRIVER_VERSION=${VERSION}" > /get_version_info.sh && chmod +x /get_version_info.sh
ENV TEST_CONFIG_PATH=/test/config.yaml
ENV PROJECT_ROOT=/

ENTRYPOINT ["python", "-m" , "unittest"]
CMD ["discover", "/test/sanity"]

