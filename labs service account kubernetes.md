Objectif

Créer :

Un ServiceAccount nommé api-reader
Un Role permettant de lire les Pods
Un RoleBinding associant le Role au ServiceAccount
Un Pod utilisant ce ServiceAccount
Une requête vers l'API Kubernetes depuis le Pod avec le token monté automatiquement
Architecture
+------------------+
| Kubernetes API   |
| Server           |
+---------+--------+
          ^
          |
          | HTTPS + Token
          |
+---------+--------+
| Pod             |
| api-client      |
+---------+--------+
          |
          |
          v
+------------------+
| ServiceAccount   |
| api-reader       |
+------------------+
          |
          v
+------------------+
| Role             |
| get/list pods    |
+------------------+
1. Créer le ServiceAccount
apiVersion: v1
kind: ServiceAccount
metadata:
  name: api-reader
  namespace: default
kubectl apply -f sa.yaml

Vérification :

kubectl get sa
2. Créer le Role

Ce rôle autorise :

get
list
watch

sur les Pods du namespace.

apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
  namespace: default
rules:
- apiGroups: [""]
  resources:
  - pods
  verbs:
  - get
  - list
  - watch
kubectl apply -f role.yaml
3. Créer le RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: pod-reader-binding
  namespace: default
subjects:
- kind: ServiceAccount
  name: api-reader
  namespace: default

roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: pod-reader
kubectl apply -f rolebinding.yaml
4. Créer le Pod
apiVersion: v1
kind: Pod
metadata:
  name: api-client
spec:
  serviceAccountName: api-reader

  containers:
  - name: client
    image: curlimages/curl

    command:
    - sleep
    - "3600"
kubectl apply -f pod.yaml

Vérification :

kubectl get pod api-client
5. Se connecter dans le Pod
kubectl exec -it api-client -- sh
6. Observer le token monté automatiquement
ls /var/run/secrets/kubernetes.io/serviceaccount

Résultat :

ca.crt
namespace
token
7. Récupérer les informations nécessaires

Token :

TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)

Namespace :

NAMESPACE=$(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace)

API Server :

KUBERNETES_SERVICE_HOST
KUBERNETES_SERVICE_PORT

Vérification :

echo $KUBERNETES_SERVICE_HOST
echo $KUBERNETES_SERVICE_PORT
8. Appeler l'API Kubernetes

Lister les Pods du namespace :

curl -k \
-H "Authorization: Bearer $TOKEN" \
https://${KUBERNETES_SERVICE_HOST}:${KUBERNETES_SERVICE_PORT}/api/v1/namespaces/${NAMESPACE}/pods

Résultat attendu :

{
  "kind":"PodList",
  "items":[
    ...
  ]
}
9. Vérifier les permissions RBAC

Depuis votre poste :

kubectl auth can-i list pods \
--as=system:serviceaccount:default:api-reader \
-n default

Résultat :

yes
10. Démonstration d'un refus RBAC

Essayer de lister les Secrets :

curl -k \
-H "Authorization: Bearer $TOKEN" \
https://${KUBERNETES_SERVICE_HOST}:${KUBERNETES_SERVICE_PORT}/api/v1/namespaces/default/secrets

Résultat :

{
  "kind":"Status",
  "status":"Failure",
  "reason":"Forbidden"
}

Car le Role n'autorise pas l'accès aux Secrets.

Bonus : Créer un Pod via l'API Kubernetes

Ajoutez la permission :

rules:
- apiGroups: [""]
  resources:
  - pods
  verbs:
  - get
  - list
  - create

Puis :

cat > pod.json <<EOF
{
  "apiVersion":"v1",
  "kind":"Pod",
  "metadata":{
    "name":"created-from-api"
  },
  "spec":{
    "containers":[
      {
        "name":"nginx",
        "image":"nginx"
      }
    ]
  }
}
EOF

Créer le Pod :

curl -k \
-X POST \
-H "Authorization: Bearer $TOKEN" \
-H "Content-Type: application/json" \
--data @pod.json \
https://${KUBERNETES_SERVICE_HOST}:${KUBERNETES_SERVICE_PORT}/api/v1/namespaces/default/pods

Vérification :

kubectl get pods

Vous verrez apparaître le Pod created-from-api.
