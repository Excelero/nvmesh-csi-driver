#!/usr/bin/env bash

source ./test_utils.sh

delete_all_daemonsets() {
    for x in $(kubectl get daemonsets | awk '{ if(NR>1) print $1 }') ;
    do
        echo "deleting $x"
        kubectl delete daemonset $x
    done
}

delete_all_pods() {
    for x in $(kubectl get pods | awk '{ if(NR>1) print $1 }') ;
    do
        echo "deleting $x"
        kubectl delete pod $x
    done
}

delete_all_pvcs() {
    for x in $(kubectl get pvc | awk '{ if(NR>1) print $1 }') ;
    do
        echo "deleting $x"
        kubectl delete pvc $x
    done
}

delete_all_daemonsets
delete_all_pods
delete_all_pvcs