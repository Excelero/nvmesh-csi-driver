repo_root=../../../
docker_file=$repo_root/test/sanity/container/Dockerfile
version_info=$($repo_root/get_version_info.sh)
source <(echo $version_info)
./
echo "Building Sanity Test Container for version ${DRIVER_VERSION}"
docker build -f $docker_file $repo_root --tag nvmesh-csi-driver/sanity-tests:dev --build-arg VERSION=${DRIVER_VERSION}

echo "Building CSI Driver for Sanity Tests"
cd $repo_root
docker build . -f test/sanity/containerized_driver/Dockerfile --build-arg BASE_IMAGE=excelero/nvmesh-csi-driver:${DRIVER_VERSION} -t excelero/nvmesh-csi-driver:${DRIVER_VERSION}-sanity
cd -