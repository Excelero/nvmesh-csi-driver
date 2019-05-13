#!/usr/bin/env bash

delete_all_pvcs() {
    for x in $(kubectl get pvc | sed '1d;$d' | awk '{ print $1 }') ;
    do
        echo "deleting $x"
        kubectl delete pvc $x
    done
}

delete_all_pvcs