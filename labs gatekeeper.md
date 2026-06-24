# Kubernetes Policy as Code avec Gatekeeper – Cas pratique d'entreprise

## Contexte

Vous êtes ingénieur DevOps au sein de l'entreprise **Acme Corp**.

L'entreprise souhaite renforcer la gouvernance de ses clusters Kubernetes grâce à **OPA Gatekeeper** afin de garantir la conformité des déploiements effectués par les différentes équipes.

Suite à plusieurs incidents de sécurité et de gouvernance, la direction a défini les règles suivantes :

### Exigences de conformité

1. Toutes les images de conteneurs doivent provenir du registre GitLab de l'entreprise :

```text
registry.gitlab.com/acme-corp/
```

2. Toutes les ressources Kubernetes doivent obligatoirement posséder le label :

```yaml
labels:
  app: <nom-application>
```

3. Les Services de type `NodePort` sont interdits.

4. Tous les Pods doivent définir :

   * des requests CPU
   * des requests mémoire
   * des limits CPU
   * des limits mémoire

5. Les Pods ne doivent jamais être exécutés avec le compte root.

---

# Objectifs pédagogiques

À l'issue de ce laboratoire, vous serez capable de :

* Installer Gatekeeper.
* Comprendre le fonctionnement des ConstraintTemplates.
* Développer des politiques personnalisées avec Rego.
* Appliquer des règles de conformité à l'échelle d'un cluster.
* Tester des workloads conformes et non conformes.

---

# Architecture cible

```text
+---------------------+
| Kubernetes Cluster  |
+----------+----------+
           |
           v
+---------------------+
|     Gatekeeper      |
+----------+----------+
           |
           v
+---------------------+
| ConstraintTemplate  |
+----------+----------+
           |
           v
+---------------------+
|    Constraints      |
+----------+----------+
           |
           v
+---------------------+
| Validation des      |
| ressources K8s      |
+---------------------+
```

---

# Partie 1 - Installation de Gatekeeper

Installer Gatekeeper :

```bash
kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/master/deploy/gatekeeper.yaml
```

Vérifier l'installation :

```bash
kubectl get pods -n gatekeeper-system
```

Résultat attendu :

```text
gatekeeper-controller-manager
gatekeeper-audit
```

---

# Partie 2 - Politique d'origine des images

## Objectif

Autoriser uniquement les images provenant du registre GitLab de l'entreprise.

---

## ConstraintTemplate

Créer :

```yaml
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8sallowedregistry
spec:
  crd:
    spec:
      names:
        kind: K8sAllowedRegistry
  targets:
  - target: admission.k8s.gatekeeper.sh
    rego: |
      package allowedregistry

      violation[{"msg": msg}] {
        container := input.review.object.spec.containers[_]

        not startswith(
          container.image,
          "registry.gitlab.com/acme-corp/"
        )

        msg := sprintf(
          "Image '%v' non autorisée",
          [container.image]
        )
      }
```

Appliquer :

```bash
kubectl apply -f template-registry.yaml
```

---

## Constraint

```yaml
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sAllowedRegistry
metadata:
  name: company-registry-only
spec:
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
```

---

## Test non conforme

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-public
spec:
  containers:
  - name: nginx
    image: nginx:latest
```

Résultat attendu :

```text
Error from server:
Image 'nginx:latest' non autorisée
```

---

## Test conforme

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-corp
spec:
  containers:
  - name: nginx
    image: registry.gitlab.com/acme-corp/nginx:v1
```

---

# Partie 3 - Label obligatoire

## Objectif

Imposer le label :

```yaml
app: valeur
```

---

## ConstraintTemplate

```yaml
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: requiredlabels
spec:
  crd:
    spec:
      names:
        kind: RequiredLabels
  targets:
  - target: admission.k8s.gatekeeper.sh
    rego: |
      package requiredlabels

      violation[{"msg": msg}] {

        not input.review.object.metadata.labels.app

        msg := "Le label app est obligatoire"
      }
```

---

## Constraint

```yaml
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: RequiredLabels
metadata:
  name: app-label-required
spec:
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
```

---

## Test non conforme

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-test
spec:
  containers:
  - name: nginx
    image: registry.gitlab.com/acme-corp/nginx:v1
```

---

## Test conforme

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-test
  labels:
    app: frontend
spec:
  containers:
  - name: nginx
    image: registry.gitlab.com/acme-corp/nginx:v1
```

---

# Partie 4 - Interdire les Services NodePort

## Objectif

Éviter l'exposition directe des applications.

---

## ConstraintTemplate

```yaml
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: disallownodeport
spec:
  crd:
    spec:
      names:
        kind: DisallowNodePort
  targets:
  - target: admission.k8s.gatekeeper.sh
    rego: |
      package disallownodeport

      violation[{"msg": msg}] {

        input.review.object.spec.type == "NodePort"

        msg := "Les services NodePort sont interdits"
      }
```

---

## Constraint

```yaml
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: DisallowNodePort
metadata:
  name: no-nodeport
spec:
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Service"]
```

---

## Test non conforme

```yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx
spec:
  type: NodePort
  selector:
    app: nginx
  ports:
  - port: 80
```

---

# Partie 5 - Imposer Requests et Limits

## Objectif

Éviter les applications non maîtrisées consommant toutes les ressources du cluster.

---

## Test attendu

Le Pod suivant doit être refusé :

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: no-limits
  labels:
    app: demo
spec:
  containers:
  - name: nginx
    image: registry.gitlab.com/acme-corp/nginx:v1
```

Le Pod suivant doit être accepté :

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: compliant
  labels:
    app: demo
spec:
  containers:
  - name: nginx
    image: registry.gitlab.com/acme-corp/nginx:v1

    resources:
      requests:
        cpu: "100m"
        memory: "128Mi"

      limits:
        cpu: "500m"
        memory: "512Mi"
```

---

# Partie 6 - Interdire l'exécution en root

## Objectif

Tous les conteneurs doivent exécuter :

```yaml
securityContext:
  runAsNonRoot: true
```

---

## Pod non conforme

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: root-container
  labels:
    app: demo
spec:
  containers:
  - name: nginx
    image: registry.gitlab.com/acme-corp/nginx:v1
```

---

## Pod conforme

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-container
  labels:
    app: demo
spec:
  containers:
  - name: nginx
    image: registry.gitlab.com/acme-corp/nginx:v1

    securityContext:
      runAsNonRoot: true
```

---

# Partie 7 - Validation finale

Une équipe de développement souhaite déployer l'application suivante :

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ecommerce
spec:
  replicas: 3

  selector:
    matchLabels:
      app: ecommerce

  template:
    metadata:
      labels:
        app: ecommerce

    spec:
      containers:
      - name: ecommerce

        image: nginx:latest

        ports:
        - containerPort: 8080
```

## Travail demandé

Identifier :

1. Toutes les violations de conformité.
2. Les politiques Gatekeeper concernées.
3. Les corrections nécessaires.
4. Le manifeste corrigé complet.


