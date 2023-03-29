FROM registry.access.redhat.com/ubi8:latest

COPY extras.repo /etc/yum.repos.d/extras.repo

RUN yum install -y python27

COPY requirements.txt ./
RUN pip2 install --no-cache-dir -r requirements.txt

COPY NVMeshSDK/ /NVMeshSDK/

RUN yum install -y sudo \
    && cd /NVMeshSDK && ./install.sh sdk && cd ../ \
    && yum clean all

RUN cp /usr/bin/python2 /usr/bin/python

ENV TEST_CONFIG_PATH="/config/config.yaml"

COPY driver/ /driver/
COPY test/ /test/
COPY test/integration/container/init.py /init.py

ENTRYPOINT ["python", "/init.py"]
