FROM python:2.7-slim
ENV container docker

COPY driver/ /driver/
COPY managementClient/ /managementClient/
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update \
    && apt install parted -y \
    && apt install udev -y

USER root

CMD ["python", "-u", "-m", "driver.server"]
