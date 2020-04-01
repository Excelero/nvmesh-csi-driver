#!/usr/bin/env bash

source ./test_utils.sh

read -r -d '' volume_template << EOM
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {name}
  namespace: nvmesh-csi-testing
spec:
  accessModes:
  - {mode}
  resources:
    requests:
      storage: 5Gi
  volumeMode: Block
  storageClassName: nvmesh-raid1
EOM

read -r -d '' pod_template << EOM
apiVersion: v1
kind: Pod
metadata:
  name: pod-{pvc}-{index}
  namespace: nvmesh-csi-testing
  labels:
    app: access-modes-test
spec:
  nodeSelector:
    worker-index: "{node_index}"
  containers:
    - name: consumer-{pvc}-{index}
      image: excelero/block-consumer-test:develop
      env:
        - name: VOLUME_PATH
          value: /mnt/vol
      volumeDevices:
        - name: block-volume
          devicePath: /mnt/vol
  volumes:
    - name: block-volume
      persistentVolumeClaim:
        claimName: {pvc}
EOM

create_volume() {
    name=$1
    mode=$2
    echo "Creating Volume Claim with AccecssMode $mode"

   echo "$volume_template" | sed -e "s/{mode}/$mode/" | sed -e "s/{name}/$name/"| kubectl create -f -

    wait_for_volumes 1
}

create_pod() {
    pvc=$1
    index=$2
    node_index=$3
    echo "Creating a Pod to consume the Block Volume.."

   echo "$pod_template" | sed -e "s/{pvc}/$pvc/" | sed -e "s/{index}/$index/" | sed -e "s/{node_index}/$node_index/" | kubectl create -f -

}

verify_pod_failed() {
    pod=$1
    error=$2

    # wait for pod to initialize
    kubectl get pods | grep $pod
    pod_created=$?
    pod_status=$(kubectl get pods | grep $pod | awk '{ print $3 }')
    while [ $pod_created -ne 0 ] || [ "$pod_Status" == "Intializing" ]
    do
        sleep 1
    done

    # make sure pod is in status ContainerCreating
    expected_status="ContainerCreating"
    pod_status=$(kubectl get pods | grep $pod | awk '{ print $3 }')
    if [ "$pod_status" != "$expected_status" ]; then
        echo "Error: Expecteed pod $pod to fail and to have status $expected_status, but got status $pod_status"
        exit 1
    fi

    # make sure the correct error found in the pods events
    kubectl get event --field-selector involvedObject.name=$pod | grep "$error"

    if [ $? -ne 0 ]; then
        echo "Warning: Could not find the specific error \"$error\" in the Pods events (kubectl get event --field-selector involvedObject.name=$pod)"
    fi
}

test_read_write_many() {
    mode=ReadWriteMany
    pvc=pvc-rwm
    create_volume $pvc $mode

    # First Pod Should Succeed, second and third should fail
    create_pod $pvc 1 1
    wait_for_pods 1

    # Second Pod on a different Node should Succeed
    create_pod $pvc 2 2
    wait_for_pods 2

    # Third Pod on the same Node should Succeed
    create_pod $pvc 3 1
    wait_for_pods 3

    delete_all_pods_and_pvcs
}

test_read_write_once() {
    mode=ReadWriteOnce
    pvc=pvc-rwo
    create_volume $pvc $mode

    # First Pod Should Succeed, second and third should fail
    create_pod pvc-rwo 1 1
    wait_for_pods 1

    # Second Pod on a different Node should Fail
    create_pod $pvc 2 2
    verify_pod_failed pod-$pvc-2

    # Third Pod on the same Node should Fail
    create_pod $pvc 3 1
    verify_pod_failed pod-$pvc-3

    delete_all_pods_and_pvcs
}

test_read_only_many() {
    mode=ReadOnlyMany
    pvc=pvc-rom
    create_volume $pvc $mode

    # First Pod Should Succeed, second and third should fail
    create_pod $pvc 1 1
    wait_for_pods 1

    # Second Pod on a different Node should Succeed
    create_pod $pvc 2 2
    wait_for_pods 2

    # Third Pod on the same Node should Succeed
    create_pod $pvc 3 1
    wait_for_pods 3

    #TODO - Verify readonly ?

    delete_all_pods_and_pvcs
}

test_multiple_modes() {
    echo "Testing Using a PVC with Multiple Access Modes"

    # Create a volume claim with all access modes
    read -r -d '' sc << EOM
kind: StorageClass
apiVersion: storage.k8s.io/v1
metadata:
  name: r10-retain
provisioner: nvmesh-csi.excelero.com
allowVolumeExpansion: true
volumeBindingMode: Immediate
reclaimPolicy: Retain
parameters:
  vpg: DEFAULT_RAID_10_VPG
EOM

    read -r -d '' pvc_all_modes << EOM
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pvc-all-modes
  namespace: nvmesh-csi-testing
spec:
  accessModes:
  - ReadWriteOnce
  - ReadWriteMany
  - ReadOnlyMany
  resources:
    requests:
      storage: 5Gi
  volumeMode: Filesystem
  storageClassName: r10-retain
EOM

    read -r -d '' pvc_rom << EOM
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pvc-rom
  namespace: nvmesh-csi-testing
spec:
  accessModes:
  - ReadOnlyMany
  resources:
    requests:
      storage: 5Gi
  volumeMode: Filesystem
  storageClassName: nvmesh-raid10
EOM

read -r -d '' pod << EOM
apiVersion: v1
kind: Pod
metadata:
  name: {name}
  namespace: nvmesh-csi-testing
  labels:
    app: access-modes-test
spec:
  restartPolicy: Never
  containers:
    - name: fs-creator
      image: ubuntu
      command: ["/bin/bash"]
      args: ["-c", "{cmd}"]
      volumeMounts:
        - name: block-volume
          mountPath: /mnt/vol

  volumes:
    - name: block-volume
      persistentVolumeClaim:
        claimName: {pvc}
EOM

    # Create Storage Class
    echo "Creating StorageClass with reclaimPolicy: Retain"
    echo "$sc" | kubectl create -f -

    # Create PVC with All Access Modes
    echo "Creating PVC with all Access Modes"
    echo "$pvc_all_modes" | kubectl create -f -

    # Create Pod to run mkfs
    # echo "Creating Pod fs-maker that will run mkfs on the block volume"
    # cmd="mkfs.ext4 /mnt/vol"
    # echo "$pod" | sed -e "s/{name}/fs-maker/" | sed -e "s/{pvc}/pvc-all-modes/" | sed -e "s|{cmd}|$cmd|"| kubectl create -f -

    # wait_for_pod_status fs-maker Completed
    # echo "Deleting pod fs-maker"
    # kubectl delete pod fs-maker

    # Create Pod to create a file on the File System
    echo "Creating pod file-maker"
    cmd="echo 'Good' > /mnt/vol/weather"
    echo "$pod" | sed -e "s/{name}/file-maker/" | sed -e "s/{pvc}/pvc-all-modes/" | sed -e "s|{cmd}|$cmd|"| kubectl create -f -

    wait_for_pod_status file-maker Completed
    echo "Deleting pod file-maker"
    kubectl delete pod file-maker

    # Delete PVC
    echo "Deleting PVC pvc-all-modes"
    kubectl delete pvc pvc-all-modes

    # Make PersistenVolume Available for the next PVC
    echo "Editing PersistentVolume - removing claimRef field tom make the PV available for the next PVC"

    pv_name=$(kubectl get pv | tail -1 | awk '{ print $1 }')
    kubectl patch pv $pv_name --type=json -p='[{"op": "remove", "path": "/spec/claimRef"}]'
    wait_for_pv_status $pv_name Available

    # Create PVC with ReadOnlyMany
    echo "Creating PVC With ReadOnlyMany"
    echo "$pvc_rom" | kubectl create -f -

    # Create 2 Pods to read the File System
    echo "Creating 2 Pods to read the file on the FileSystem"

    cmd="cat /mnt/vol/weather"
    echo "$pod" | sed -e "s/{name}/fs-reader-1/" | sed -e "s/{pvc}/pvc-rom/" | sed -e "s|{cmd}|$cmd|"| kubectl create -f -
    echo "$pod" | sed -e "s/{name}/fs-reader-2/" | sed -e "s/{pvc}/pvc-rom/" | sed -e "s|{cmd}|$cmd|"| kubectl create -f -
    wait_for_pod_status fs-reader-1 Completed
    wait_for_pod_status fs-reader-1 Completed

    # Create 2 Pods to read the File System
    echo "Creating 1 Pod that will try to write to the FileSystem, this should fail"
    cmd="echo 'Bad' > /mnt/vol/weather"
    echo "$pod" | sed -e "s/{name}/fs-writer-1/" | sed -e "s/{pvc}/pvc-rom/" | sed -e "s/{cmd}/$cmd/"| kubectl create -f -
    wait_for_pod_status fs-reader-1 Failed
}

delete_all_pods_and_pvcs() {
    delete_all_objects_of_type pod
    delete_all_objects_of_type pvc
    delete_all_objects_of_type pv
    wait_for_pods_to_be_removed
}

test_read_write_many
test_read_write_once
test_read_only_many
#test_multiple_modes

exit 1



