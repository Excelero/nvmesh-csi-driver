FROM registry.access.redhat.com/ubi8/python-27

COPY NVMeshSDK/ /NVMeshSDK/
COPY requirements.txt ./

USER root

RUN pip install --no-cache-dir -r requirements.txt

COPY ./build_tools/repos/centos-base.repo /etc/yum.repos.d/centos-base.repo
COPY ./build_tools/repos/RPM-GPG-KEY-centosofficial /etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial
RUN yum install -y sudo xfsprogs e2fsprogs \
    && yum clean all

RUN cd /NVMeshSDK && ./install.sh sdk && cd ../ \
    && rm -rf /var/lib/apt/lists/*

COPY driver/ /driver/
COPY version /version

CMD ["python", "/driver/server.py"]
