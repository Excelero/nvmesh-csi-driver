

print_help() {
    echo "Usage: $(basename "$0") [--address <10.0.1.115:4000> --protocol <https/http>]"
}

isValidIport () {
	if [[ ! $1 =~ ^(http|https):\/\/.+:[0-9]{1,5}$ ]]; then
		return 1
	fi

	iportArray=(${1//:/ })
	port=${iportArray[2]}

	if [[ "$port" -gt 65535 ]] ; then
		echo "Port number not in range! please choose valid port number (0-65535)"
		return 1
	fi
}

while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -h|--help)
    print_help
    exit 0
    ;;
    --address)
    address="$2"
    shift
    ;;
    --protocol)
    protocol="$2"
    shift
    ;;
    *)
    # unknown option
    echo "Unknown option $key"
    print_help
    exit 1
    ;;
esac
shift # past argument or value
done

if [ -z "$protocol" ]; then
	echo "Please insert the protocol you want to use: (http or https)"
	read protocol
fi

if [ -z "$address" ]; then
	echo "Please insert the ip address/hostname and port of the management (ex: 10.0.1.115:4000)"
	read address
fi

! isValidIport http://$address && echo "Invalid ip/hostname" && exit 1
! isValidIport $protocol://something:123 && echo "Invalid protocol" && exit 1

echo "Updating ConfigMap nvmesh-csi-config in nvmesh-csi namespace"
kubectl patch configmap -n nvmesh-csi nvmesh-csi-config -p "{\"data\": {\"management.protocol\": \"$protocol\", \"management.servers\": \"$address\"}}"
changed=$(date "+%F-%H_%M_%S")

echo "Restarting node drivers"
kubectl patch daemonset -n nvmesh-csi nvmesh-csi-node-driver -p "{\"spec\": {\"template\": {\"metadata\": {\"labels\": {\"csi.driver/config-changed\": \"${changed}\"}}}}}"

echo "Restarting nvmesh-csi-controller"
kubectl patch statefulset -n nvmesh-csi nvmesh-csi-controller -p "{\"spec\": {\"template\": {\"metadata\": {\"labels\": {\"csi.driver/config-changed\": \"${changed}\"}}}}}"
