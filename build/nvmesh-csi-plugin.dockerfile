FROM python:2.7-slim
ENV container docker

COPY driver/ /driver/
COPY managementClient/ /managementClient/
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

USER root

CMD ["python", "-u", "-m", "driver.server"]
