#!/bin/bash

# Install the helm package
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
helm install -n kubeapps --create-namespace kubeapps bitnami/kubeapps

# Create the namespace
kubectl     create   ns liora

# Create the required service accountt
kubectl     create                              \
            serviceaccount kubeapps-operator    \
            -n liora

# Create the required role binding
kubectl     create                                          \
            clusterrolebinding kubeapps-operator            \
            --serviceaccount=liora:kubeapps-operator   \
            --clusterrole=cluster-admin                         

# Apply the secret
# It will generate the token for us
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
    name: kubeapps-operator-token
    namespace: liora
    annotations:
    kubernetes.io/service-account.name: kubeapps-operator
type: kubernetes.io/service-account-token
EOF

# Get the token for the GUI
kubectl get                                             \
        secret kubeapps-operator-token                  \
        -o go-template='{{.data.token | base64decode}}' \
        -n liora                                   
        
# Port forward so we can view the dashboard
kubectl port-forward            \
        svc/kubeapps            \
        -n kubeapps  8080:80