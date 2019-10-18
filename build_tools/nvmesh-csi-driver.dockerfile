FROM python:2.7-slim
ENV container docker

COPY NVMeshSDK/ /NVMeshSDK/
COPY requirements.txt ./

USER root

RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update \
    && apt install parted udev xfsprogs sudo -y \
    && cd NVMeshSDK && ./install.sh sdk && cd ../ \
    && rm -rf /var/lib/apt/lists/*

COPY driver/ /driver/
COPY version /version

CMD ["python", "driver/server.py"]
