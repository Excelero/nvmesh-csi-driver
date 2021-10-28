# ----------------
# Build
# ----------------

# builds the driver container and all testing components
all: build-driver-container build-tests

build-driver-container:
	cd ./build_tools && ./build.sh

build-tests: build-driver-container build-sanity-tests build-integration-tests
	echo "build tests"

build-nvmesh-cluster-sim:
	echo "build-nvmesh-cluster-sim"
	cd test/sanity/nvmesh_cluster_simulator/mgmt-sim && make build

build-sanity-image:
	echo "build-sanity-image"
	cd test/sanity/container && /bin/bash -c ./build.sh

build-sanity-tests: build-nvmesh-cluster-sim build-sanity-image
	echo "Sanity Test Built. to run: make test-sanity"

build-integration-tests:
	echo "build-integration-tests"
	cd test/integration/container && ./build.sh

# ----------------
# Test
# ----------------

# test sanity locally, some python dependencies are expected, such as kuberentes library etc.
test-sanity-locally:
	export PROJECT_ROOT="./" && export TEST_CONFIG_PATH=test/config.yaml && python -m unittest  discover --verbose test/sanity

# test sanity inside a conatiner (which will spawn other containers on the host)
# requires to run make build-sanity-tests
test-sanity:
	cd test/sanity/container && ./run.sh

# This will create a kubernetes Job resource using local kubectl tool
test-integration:
	kubectl apply -f integration/container/test_job.yaml
	kubectl wait --for=condition=ready pod --selector=job-name=csi-integration-test
	kubectl logs --selector=job-name=csi-integration-test --follow

# Deletes the Kubernetes Job using local kubectl
delete-integration-job:
	kubectl delete -f integration/container/test_job.yaml

# ----------------
# Deploy
# ----------------

manifests:
	cd deploy/kubernetes/scripts && ./build_deployment_file.sh

deploy: build-driver-container manifests
	echo "Deploying YAML files.."
	kubectl delete -f deploy/kubernetes/deployment.yaml
	kubectl create -f deploy/kubernetes/deployment.yaml
