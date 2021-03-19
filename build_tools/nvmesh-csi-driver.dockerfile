FROM registry.access.redhat.com/ubi8

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

COPY build_tools/extras.repo /etc/yum.repos.d/extras.repo

RUN yum install -y python27 parted xfsprogs e2fsprogs

COPY requirements.txt ./
RUN pip2 install --no-cache-dir -r requirements.txt

COPY NVMeshSDK/ /NVMeshSDK/

RUN yum install -y sudo \
    && cd /NVMeshSDK && ./install.sh sdk && cd ../ \
    && yum clean all

RUN cp /usr/bin/python2 /usr/bin/python

COPY licenses/ /licenses/
COPY driver/ /driver/
COPY version /version

CMD ["sudo", "--preserve-env", "python", "/driver/server.py"]
