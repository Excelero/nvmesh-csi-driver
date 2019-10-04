FROM python:2.7-slim
ENV container docker

COPY NVMeshSDK/ /NVMeshSDK/
COPY requirements.txt ./

USER root

RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update \
    && apt install parted -y \
    && apt install udev -y \
    && apt install xfsprogs -y \
    && apt install sudo -y \
    && cd NVMeshSDK && ./install.sh sdk \
    && cd ../ && rm -rf /NVMeshSDK

COPY driver/ /driver/


CMD ["python", "driver/server.py"]
