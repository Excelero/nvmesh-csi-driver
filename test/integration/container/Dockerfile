FROM python:2.7

COPY extras.repo /etc/yum.repos.d/extras.repo

# Install Helm
RUN curl https://baltocdn.com/helm/signing.asc | gpg --dearmor | tee /usr/share/keyrings/helm.gpg > /dev/null
RUN apt-get install apt-transport-https --yes
RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/helm.gpg] https://baltocdn.com/helm/stable/debian/ all main" | tee /etc/apt/sources.list.d/helm-stable-debian.list
RUN apt-get update && apt-get install helm

# Install kubectl
RUN curl -LO "https://dl.k8s.io/release/v1.25.2/bin/linux/amd64/kubectl" \
    && install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY NVMeshSDK/ /NVMeshSDK/

RUN cd /NVMeshSDK && ./install.sh sdk && cd ../

ENV TEST_CONFIG_PATH="/config/config.yaml"

COPY driver/ /driver/
COPY test/ /test/
COPY test/integration/container/init.py /init.py



ENTRYPOINT ["python", "/init.py"]
