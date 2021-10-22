FROM registry.access.redhat.com/ubi8:latest

COPY extras.repo /etc/yum.repos.d/extras.repo

RUN yum install -y python27 parted-3.2 xfsprogs-5.0.0 e2fsprogs-1.45.6

COPY requirements.txt ./
RUN pip2 install --no-cache-dir -r requirements.txt

COPY NVMeshSDK/ /NVMeshSDK/

RUN yum install -y sudo \
    && cd /NVMeshSDK && ./install.sh sdk && cd ../ \
    && yum clean all

RUN cp /usr/bin/python2 /usr/bin/python

ARG VERSION
ARG RELEASE

### Labels required by RedHat OpenShift
LABEL name="NVMesh CSI Driver" \
      maintainer="support@excelero.com" \
      vendor="Excelero" \
      version="$VERSION" \
      release="$RELEASE" \
      summary="CSI Driver for NVMesh Storage Solution" \
      description="NVMesh CSI Driver allows Provisioning, Managing and Consuming NVMesh Volumes in Kubernetes"

COPY licenses/ /licenses/
COPY driver/ /driver/
RUN printf "$VERSION" > /version

CMD ["python", "/driver/server.py"]
