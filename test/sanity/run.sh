CONFIG_PATH="$PWD/../config.yaml"

if [ "$#" -gt 0 ] && [ "$1" = "--config" ]; then
    CONFIG_PATH="$2"
    shift
    shift
fi
set +x
docker run -it --name csi-sanity-test --net csi_test -v /var/run/docker.sock:/var/run/docker.sock -v /tmp/csi_sanity:/tmp/csi_sanity -v $CONFIG_PATH:/test/config.yaml --privileged  --rm nvmesh-csi-driver/sanity-tests:dev "$@"
set -x