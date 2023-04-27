version := `./get_version_info.sh | grep ^VERSION | cut -d '=' -f2`
image_name := `cat deploy/kubernetes/helm/nvmesh-csi-driver/values.yaml | yq '.image.repository'`
version_w_release := `./get_version_info.sh | grep ^DRIVER_VERSION | cut -d '=' -f2`
image_name_dev := `cat deploy/kubernetes/helm/nvmesh-csi-driver/values-dev.yaml | yq '.image.repository'`
dev_registry := `cat deploy/kubernetes/helm/nvmesh-csi-driver/values-dev.yaml | yq '.dev.registry'`

# ----------------
# Build
# ----------------

# builds the driver container and all testing components
all: build build-tests

build:
	cd ./build_tools && ./build.sh

build-tests: build build-sanity-tests build-integration-tests
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

# Create a config.yaml
create-test-config:
	cp test/config-template.yaml test/config.yaml

# test sanity locally, some python dependencies are expected, such as kuberentes library etc.
test-sanity-locally:
	export PROJECT_ROOT="./" && export TEST_CONFIG_PATH=test/config.yaml && python -m unittest  discover --verbose test/sanity

# test sanity inside a conatiner (which will spawn other containers on the host)
# requires to run make build-sanity-tests
test-sanity:
	test/sanity/run.sh --config $(PWD)/test/config.yaml

test-integration:
	echo "Clearing Environment"
	cd test && ./run_integration_tests.sh --clear-env
	echo "Running All Integration Tests"
	cd test && ./run_integration_tests.sh

# This will create a kubernetes Job resource using local kubectl tool
test-integration-containerized:
	kubectl delete -n nvmesh-csi-testing -f test/integration/container/ ; kubectl apply -n nvmesh-csi-testing -f test/integration/container/
	kubectl wait -n nvmesh-csi-testing --for=condition=ready pod --selector=job-name=csi-integration-test
	kubectl logs -n nvmesh-csi-testing --selector=job-name=csi-integration-test --follow

# ----------------
# Push to registry
# ----------------
push:
	echo "Pushing version $(version) as $(image_name)"
	docker tag excelero/nvmesh-csi-driver:$(version) $(image_name):$(version)
	docker push $(image_name):$(version)

push-dev:
	echo "Pushing version $(version)-dev as $(image_name_dev)"
	echo "RUNNING: docker tag excelero/nvmesh-csi-driver:$(version_w_release) $(image_name_dev):$(version)-dev"
	docker tag excelero/nvmesh-csi-driver:$(version_w_release) $(image_name_dev):$(version)-dev
	echo "RUNNING: docker push $(image_name_dev):$(version)-dev"
	docker push $(image_name_dev):$(version)-dev

# ----------------
# Deploy
# ----------------

manifests:
	cd deploy/kubernetes/scripts && ./build_deployment_file.sh

dep_file := deployment.yaml

deploy: manifests
	echo "Deploying YAML file: " $(dep_file)
	kubectl delete -f deploy/kubernetes/$(dep_file) ; kubectl create -f deploy/kubernetes/$(dep_file)


dep_dev_file := deployment_dev.yaml

deploy-dev: manifests
	echo "Deploying Dev YAML file: " $(dep_dev_file)
	kubectl delete -f deploy/kubernetes/$(dep_dev_file) ; kubectl create -f deploy/kubernetes/$(dep_dev_file)

dev-cycle: build manifests push-dev deploy-dev
