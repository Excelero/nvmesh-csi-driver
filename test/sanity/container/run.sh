
TEST_NAME=TestNodeService.test_get_info_basic_test
MODULE_NAME=test.sanity.test_node
docker run -it --net host -v /var/run/docker.sock:/var/run/docker.sock -v $PWD/../../config.yaml:/test/config.yaml --privileged  --rm nvmesh-csi-driver/sanity-tests:latest $MODULE_NAME $TEST_NAME