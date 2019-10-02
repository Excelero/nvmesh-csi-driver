FROM python:2.7-slim
ENV container docker

COPY NVMeshSDK/ /NVMeshSDK/
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update \
    && apt install parted -y \
    && apt install udev -y \
    && apt install xfsprogs -y \
    && apt install sudo -y \
    && cd NVMeshSDK && ./install.sh sdk \
    && rm -rf /NVMeshSDK

COPY driver/ /driver/

USER root

CMD ["python", "driver/server.py"]
