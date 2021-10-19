repo_root=../../../
docker_file=$repo_root/test/sanity/container/Dockerfile

docker build -f $docker_file $repo_root --tag nvmesh-csi-driver/sanity-tests --build-arg VERSION=$(git describe)
