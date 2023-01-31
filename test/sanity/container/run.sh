
docker run -it --name "csi-sanity-test" --net host -v /var/run/docker.sock:/var/run/docker.sock -v /tmp/csi_sanity:/tmp/csi_sanity -v $PWD/../../config.yaml:/test/config.yaml --privileged  --rm nvmesh-csi-driver/sanity-tests:dev "$@"
