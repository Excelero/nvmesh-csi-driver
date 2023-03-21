
__filename__=$0

namespace="default"
debug_enabled=false

COMPONENT_LABEL_KEY="app.kubernetes.io/component"
CSI_DRIVER_LABEL="app.kubernetes.io/name=nvmesh-csi-driver"

CONTROLLER_COMPONENET_NAME="controller"
NODE_DRIVER_COMPONENET_NAME="node-driver"

ERROR_CODE_WRONG_ARGS=1
ERROR_CODE_NO_CSI_DRIVER_FOUND=2
ERROR_CODE_UNKNOWN_LOG_LEVEL=3

log() {
    level=$1
    shift

    if [ "$level" == "error" ]; then
        echo "$level - $@" >&2
    elif [ "$level" == "debug" ]; then
        if [ "$debug_enabled" == "true" ]; then
            echo "$level - $@"
        fi
    elif [ "$level" == "info" ]; then
        echo "$level - $@"
    else
        echo "Unknown log level $level"
        exit $ERROR_CODE_UNKNOWN_LOG_LEVEL
    fi
}

print_code() {
    echo -e "\033[0;35m$@\033[0m"
}

print_comment() {
    echo -e "\033[1;37m$@\033[0m"
}


show_help() {
    echo "Usage: $__filename__ [[--host <hostname>] [--pod <pod-name>] [--namespace <namespace>]"
    echo ""
    echo "-n|--namespace    the namespace where the pod is deployed. deafult value is \"default\""
    echo "--debug           enable debug logs for this script"

    echo ""
    echo ""

    # Exmaples
    print_comment "Examples:"
    script_name=$0

    print_code "${script_name} -n nvmesh-csi"
    echo ""
}

parse_args() {
    while [[ $# -gt 0 ]]
    do
    key="$1"
    case $key in
        --debug)
            debug_enabled="true"
            log "debug" "Debug enabled"
            shift
        ;;
        -n|--namespace)
            namespace="$2"
            shift
            shift
        ;;
        --)
            shift
            pager_args="$@"
            break
        ;;
        -h|--help)
            show_help
            exit 0
        ;;
        *)  # unknown option
            echo "Unknown option $key"
            show_help
            exit $ERROR_CODE_WRONG_ARGS
        ;;
    esac
    done

}

verify_namespace() {
    kubectl get daemonset -n $namespace nvmesh-csi-node-driver &> /dev/null

    if [ $? -ne 0 ]; then
        log "error" "Could not find NVMesh CSI Driver in namespace \"$namespace\" please provide correct namespace using the --namespace flag"
        exit $ERROR_CODE_NO_CSI_DRIVER_FOUND
    fi
}

collect_daemonset_and_statefulset() {
    log "info" "Collecting DaemonSet and StatefulSet manifests"

    file_prefix="${log_dir_name}/deployments/"
    mkdir -p "$file_prefix"
    
    output_file="$file_prefix"nvmesh-csi-controller.yaml
    kubectl get -n $namespace statefulset nvmesh-csi-controller -o yaml > $output_file

    output_file="$file_prefix"nvmesh-csi-node-driver.yaml
    kubectl get -n $namespace daemonset nvmesh-csi-node-driver -o yaml > $output_file

    log "debug" "Finished collecting StatefulSet and DaemonSet yamls" >&2
}

collect_logs_from_pod() {
    # expects pod_name
    if [ -z "$pod_name" ]; then
        log "error" "expected pod_name. but got pod_name=$pod_name"
        return
    fi

    # populate node_name
    get_pod_node_name

    # convert pod/container_name to pod-container_name
    safe_pod_name=$(echo $pod_name | sed -e 's/\//-/g')
    file_prefix="${log_dir_name}/${component}/${node_name}/${safe_pod_name}"
    mkdir -p "$file_prefix"

    log "debug" "Collecting logs for pod $pod_name"
    get_pod_container_names

    for c in ${containers[@]}; do
        container=$c
        collect_container_logs
    done
}

collect_container_logs() {
    output_file="${file_prefix}/container_${container}.log"
    log "info" "Collecting logs from node $node_name pod $pod_name container $container"

    log "debug" "running: kubectl logs -n $namespace $pod_name -c $container > $output_file"
    kubectl logs -n $namespace $pod_name --timestamps -c $container > $output_file
}

collect_config_maps() {
    log "info" "Collecting ConfigMaps"

    configmaps=(
        nvmesh-csi-config
        nvmesh-csi-topology
        nvmesh-csi-compatibility
    )

    cm_dir="${log_dir_name}/config_maps"
    mkdir -p $cm_dir

    for cm_name in ${configmaps[@]}; do
        log "info" "Collecting ConfigMap $cm_name"
        kubectl get configmap $cm_name -o yaml > "${cm_dir}/${cm_name}".yaml
    done
}

get_pod_node_name() {
    node_name=$(kubectl get pod -n ${namespace} ${pod_name} -o=jsonpath='{.spec.nodeName}')
}

get_componenet_pods() {
    log "debug" "running: kubectl get -n ${namespace} pod -l "${CSI_DRIVER_LABEL}" -l "${COMPONENT_LABEL_KEY}=${component}" -o=jsonpath='{.items[*].metadata.name}'"
    pod_names=$(kubectl get -n ${namespace} pod -l "${CSI_DRIVER_LABEL}" -l "${COMPONENT_LABEL_KEY}=${component}" -o=jsonpath='{.items[*].metadata.name}')
}

get_controller_pods() {
    component=$CONTROLLER_COMPONENET_NAME
    get_componenet_pods
}

get_node_driver_pods() {
    component=$NODE_DRIVER_COMPONENET_NAME
    get_componenet_pods
}

get_pod_container_names() {
    containers=$(kubectl get pod ${pod_name} -n ${namespace} -o jsonpath='{range .spec.containers[*]}{.name}{"\n"}{end}'|sort|column -t)
}

collect_csi_node_driver_logs() {
    log "info" "Collecting CSI Node Driver logs"

    get_node_driver_pods

    log "debug" "Found node-driver pods $pod_names"

    for pod_name in ${pod_names[@]}; do
        collect_logs_from_pod
    done
}

collect_csi_controller_logs() {
    log "info" "Collecting CSI Controller logs"

    get_controller_pods

    log "debug" "Found controller pods $pod_names"

    for pod_name in ${pod_names[@]}; do
        collect_logs_from_pod
    done
}

collect_all_logs() {
    log "info" "Collecting logs from namespace \"$namespace\""

    collect_csi_node_driver_logs
    
    collect_csi_controller_logs

    collect_config_maps

    collect_daemonset_and_statefulset
    
    log "info" "Finished collecting all logs"
}

get_dir_name_with_date() {
    echo "logs/log_from_$(date '+%F-%T')"
}

################## Main ##################

parse_args $@

verify_namespace

log_dir_name=$(get_dir_name_with_date)
collect_all_logs
log "info" "Logs are available at $log_dir_name"
