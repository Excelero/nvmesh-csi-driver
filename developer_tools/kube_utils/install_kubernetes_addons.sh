
edit_ingress_service() {

# Python code
read -r -d '' python_code << EndOfCode
import json, sys
obj=json.load(sys.stdin)
print obj
obj["spec"]["type"] = "LoadBalancer"
obj["spec"]["externalIPs"] = [ "10.0.1.115", "10.0.1.117", "10.0.1.127" ]
print obj
EndOfCode

        echo "Python Code:\n"$python_code

        kubectl get svc -n ingress-nginx ingress-nginx -o json | python -c "$python_code" | cat
}

configure_ingress_nginx() {
        # Documentation at: https://kubernetes.github.io/ingress-nginx/deploy/

        # ingress-nginx main deployment
        kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/master/deploy/static/mandatory.yaml

        # required for for Bare-Metal installation
        kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/master/deploy/static/provider/baremetal/service-nodeport.yaml

        # Edit the service ingress-nginx under namespace ingress-nginx
        # kubectl edit svc -n ingress-nginx ingress-nginx
        # change service type to LoadBalance
        # add under spec externalIPs: [ "10.0.1.115", "10.0.1.117", "10.0.1.127" ] (array of actual node IPs)
        # edit_ingress_service
}

###  Main ###

configure_ingress_nginx


