# Gestion des secrets Kubernetes avec HashiCorp Vault, Vault Secrets Operator et External Secrets Operator

## Introduction générale

Dans une infrastructure moderne, les applications ont besoin d'un grand nombre d'informations sensibles pour fonctionner correctement. Une application peut avoir besoin d'un mot de passe de base de données, d'une clé d'API, d'un certificat TLS, d'un token d'accès à un service externe ou encore d'identifiants permettant de communiquer avec un autre composant du système d'information.

Pendant longtemps, ces informations ont été directement inscrites dans les fichiers de configuration des applications. Cette approche paraît simple au départ, mais elle devient rapidement problématique dès que l'environnement gagne en complexité.

Un mot de passe placé dans un fichier de configuration peut se retrouver dans Git, dans une image Docker, dans un fichier YAML Kubernetes, dans un système de sauvegarde ou encore dans les logs d'une pipeline CI/CD. Une simple mauvaise manipulation peut alors provoquer une fuite d'informations sensibles.

Kubernetes fournit bien un objet `Secret` permettant de stocker des données sensibles, mais un `Secret` Kubernetes ne doit pas être considéré comme un coffre-fort complet. Il s'agit avant tout d'un mécanisme natif permettant de mettre des données sensibles à disposition des workloads Kubernetes.

C'est dans ce contexte que des solutions spécialisées comme **HashiCorp Vault** prennent tout leur intérêt.

Vault permet de centraliser la gestion des secrets, de contrôler précisément qui peut accéder à quelles données, de gérer des secrets dynamiques, de générer des certificats, de journaliser les accès et de mettre en place une véritable stratégie de gestion du cycle de vie des informations sensibles.

Dans un environnement Kubernetes, une difficulté supplémentaire apparaît toutefois : comment permettre à une application Kubernetes d'utiliser les secrets stockés dans Vault sans obliger le développeur à intégrer directement le client Vault dans son application ?

C'est précisément le problème auquel répondent des outils comme **Vault Secrets Operator**, abrégé VSO.

VSO permet d'intégrer Vault dans le fonctionnement natif de Kubernetes. L'application peut continuer à consommer un `Secret` Kubernetes classique tandis que l'Operator se charge de récupérer le secret depuis Vault et de maintenir la synchronisation entre les deux systèmes.

Le principe fondamental de ce cours sera donc le suivant :

```text
                         HashiCorp Vault
                              │
                              │
                         KV v2 Secret
                              │
                              ▼
                     Vault Secrets Operator
                              │
                       synchronisation
                              │
                              ▼
                    Kubernetes Secret
                              │
                              ▼
                         Deployment
                              │
                              ▼
                         Application
```

Cette architecture permet de séparer clairement les responsabilités.

Vault devient le système spécialisé dans la gestion des secrets, Kubernetes reste responsable de l'exécution des applications et VSO fait le lien entre les deux mondes.

---

# Partie I — Comprendre le problème de la gestion des secrets

## 1. Pourquoi la gestion des secrets est-elle un problème ?

Avant d'installer le moindre composant, il est important de comprendre le problème que nous cherchons réellement à résoudre.

Prenons une application web classique qui doit se connecter à une base PostgreSQL.

Elle a besoin de plusieurs informations :

```text
DB_HOST
DB_PORT
DB_DATABASE
DB_USERNAME
DB_PASSWORD
```

Les informations comme le nom de la base ou le port peuvent parfois être considérées comme relativement peu sensibles.

En revanche, le mot de passe constitue une information critique.

Une première approche pourrait consister à placer directement le mot de passe dans le fichier de configuration :

```yaml
database:
  host: postgres
  username: application
  password: MyPassword123
```

Cette solution est extrêmement dangereuse dans un environnement professionnel.

Le fichier peut être envoyé dans Git. Il peut être récupéré par une pipeline CI/CD. Il peut être inclus dans une image Docker. Il peut être copié dans un environnement de test. Il peut également être retrouvé dans l'historique Git même si le fichier est ensuite modifié.

Le problème n'est donc pas uniquement de savoir **où stocker le secret**.

Il faut également répondre à plusieurs questions :

- Qui peut lire le secret ?
- Qui peut modifier le secret ?
- Combien de temps le secret reste-t-il valide ?
- Comment le secret est-il renouvelé ?
- Comment savoir qui l'a utilisé ?
- Que se passe-t-il lorsqu'un secret est compromis ?
- Comment empêcher une application d'accéder aux secrets d'une autre application ?
- Comment gérer plusieurs environnements ?
- Comment automatiser la rotation des identifiants ?

Une solution sérieuse de gestion des secrets doit donc gérer le **cycle de vie complet du secret**.

---

## 2. Secret statique et secret dynamique

Il existe une distinction importante entre les secrets statiques et les secrets dynamiques.

Un secret statique est une valeur qui existe explicitement et qui reste généralement valable jusqu'à ce qu'un administrateur décide de la modifier.

Par exemple :

```text
username = admin
password = SuperSecret123!
```

Le mot de passe reste identique pendant une certaine période.

Vault peut stocker ce type d'information avec son moteur **KV — Key/Value**.

Un secret dynamique fonctionne différemment.

Dans ce modèle, l'application ne reçoit pas nécessairement un compte permanent. Vault peut demander à un système externe, par exemple une base de données, de créer temporairement des identifiants.

Le processus peut alors ressembler à ceci :

```text
Application
     │
     │ demande des credentials
     ▼
   Vault
     │
     │ création de credentials temporaires
     ▼
 PostgreSQL
     │
     ▼
username = v-user-8f31
password = xxxxxxxx
TTL = 1 heure
```

Une fois le bail arrivé à expiration, les credentials peuvent être révoqués.

Cette approche réduit considérablement le risque associé aux identifiants permanents.

---

# Partie II — Présentation de HashiCorp Vault

## 3. Qu'est-ce que HashiCorp Vault ?

HashiCorp Vault est une plateforme spécialisée dans la gestion sécurisée des secrets et des informations sensibles.

Vault ne doit pas être considéré comme un simple fichier chiffré contenant des mots de passe.

Son rôle est beaucoup plus large.

Vault fournit notamment :

- une gestion centralisée des secrets ;
- une authentification des clients ;
- un système d'autorisation basé sur des policies ;
- des secrets statiques ;
- des secrets dynamiques ;
- des certificats ;
- des mécanismes cryptographiques ;
- de l'audit ;
- une gestion des leases ;
- différentes méthodes d'intégration avec les environnements cloud et Kubernetes.

L'un des principes fondamentaux de Vault consiste à séparer **l'identité**, **les permissions** et **les données secrètes**.

Un utilisateur ou une application ne demande donc pas simplement :

> Donne-moi le secret.

Il doit d'abord être identifié.

Vault détermine ensuite ce que cette identité a le droit de faire.

Enfin, Vault autorise ou refuse l'accès au secret demandé.

Le modèle conceptuel peut être représenté ainsi :

```text
                CLIENT
                  │
                  │ authentification
                  ▼
              AUTH METHOD
                  │
                  │ identité
                  ▼
                TOKEN
                  │
                  │ policies
                  ▼
               POLICY
                  │
                  │ permissions
                  ▼
           SECRETS ENGINE
                  │
                  ▼
               SECRET
```

Cette séparation est essentielle dans une architecture sécurisée.

---

## 4. Les trois grandes questions auxquelles Vault répond

Pour comprendre Vault, il est utile de retenir trois questions.

### Question 1 — Qui es-tu ?

Cette question concerne l'authentification.

Vault propose différents mécanismes d'authentification :

- Token ;
- Kubernetes ;
- AppRole ;
- JWT ;
- AWS ;
- GCP ;
- LDAP ;
- et d'autres mécanismes selon l'environnement.

Dans notre lab Kubernetes, nous utiliserons :

```text
Kubernetes Auth
```

L'identité sera associée à un `ServiceAccount` Kubernetes.

---

### Question 2 — Que peux-tu faire ?

Cette question concerne l'autorisation.

Vault utilise des **policies**.

Une policy peut autoriser une identité à lire un chemin précis :

```hcl
path "kvv2/data/my-app/config" {
  capabilities = ["read"]
}
```

Cette policy signifie que l'identité disposant de cette policy peut effectuer une opération de lecture sur ce chemin.

Elle ne donne pas automatiquement accès à tous les secrets présents dans Vault.

C'est un point essentiel.

Une bonne architecture ne consiste pas à créer une policy :

```text
allow everything
```

mais à donner uniquement les permissions nécessaires.

---

### Question 3 — Quel secret veux-tu utiliser ?

Cette question concerne les **Secrets Engines**.

Vault peut utiliser différents moteurs pour gérer différents types de secrets.

Dans notre lab, nous utiliserons :

```text
KV v2
```

Le moteur KV permet de stocker des couples clé/valeur.

Par exemple :

```text
username = admin
password = SuperSecret123!
```

Le secret sera stocké sous :

```text
kvv2/my-app/config
```

---

# Partie III — Architecture du laboratoire

## 5. Vue globale

Notre laboratoire va mettre en place une architecture Kubernetes complète mais volontairement simple.

Nous utiliserons un cluster K3s mono-nœud.

Le cluster contiendra plusieurs namespaces afin de séparer les responsabilités :

```text
K3s
│
├── vault
│   └── Vault
│
├── vault-secrets-operator
│   └── Vault Secrets Operator
│
└── my-ns
    └── Application
```

Le secret sera stocké dans Vault :

```text
kvv2/my-app/config
```

avec :

```text
username = admin
password = SuperSecret123!
```

VSO récupérera ensuite ces informations et les synchronisera dans Kubernetes sous la forme :

```text
Secret/my-secret
```

L'application n'aura pas besoin de connaître l'existence de Vault.

Elle utilisera simplement :

```yaml
secretKeyRef:
  name: my-secret
```

L'architecture complète est donc :

```text
                         K3s
                          │
          ┌───────────────┴─────────────────┐
          │                                 │
          ▼                                 ▼
       Vault                         Vault Secrets Operator
     namespace vault                namespace VSO
          │                                 │
          │                                 │
          │ KV v2                           │
          │                                 │
          ▼                                 │
  kvv2/my-app/config                        │
          │                                 │
          │ Kubernetes Auth                  │
          │                                 │
          └────────────────────────────────►│
                                            │
                                      VaultStaticSecret
                                            │
                                            ▼
                                    Kubernetes Secret
                                         my-secret
                                            │
                                            ▼
                                      Deployment
                                         my-app
                                            │
                              ┌─────────────┴─────────────┐
                              ▼                           ▼
                          USERNAME                    PASSWORD
```

Cette architecture constitue le fil conducteur de tout le laboratoire.

---

## 6. Pourquoi utiliser plusieurs namespaces ?

La séparation par namespace n'est pas uniquement esthétique.

Dans Kubernetes, les namespaces constituent un mécanisme important d'organisation et d'isolation logique.

Nous allons donc utiliser :

```text
vault
```

pour Vault.

Puis :

```text
vault-secrets-operator
```

pour VSO.

Enfin :

```text
my-ns
```

pour l'application.

Cette séparation facilite notamment :

- la gestion des permissions RBAC ;
- le diagnostic ;
- l'organisation des ressources ;
- la séparation des workloads ;
- la compréhension de l'architecture.

Dans un environnement réel, cette logique peut être poussée beaucoup plus loin.

On pourrait par exemple avoir :

```text
production
staging
development
monitoring
security
vault
```

ou une organisation basée sur les domaines fonctionnels.

---

# Partie IV — Préparation de l'environnement

## 7. Prérequis matériels

Le laboratoire peut fonctionner sur une petite machine virtuelle.

La configuration minimale recommandée est d'environ :

```text
2 CPU
4 Go RAM
20 Go disque
```

Cependant, pour disposer d'un environnement plus confortable, notamment lorsque plusieurs composants Kubernetes sont installés simultanément, il est préférable de prévoir :

```text
4 CPU
8 Go RAM
20 Go disque
```

Le laboratoire reste volontairement léger.

Nous n'allons pas mettre en place une architecture Vault hautement disponible, plusieurs workers Kubernetes ou une base de données externe dans cette première étape.

L'objectif est pédagogique : comprendre précisément la chaîne de fonctionnement avant de complexifier l'architecture.


1. **K3s → Vault → Kubernetes Auth → Vault Secrets Operator → VaultStaticSecret → Kubernetes Secret → Deployment**

   L'objectif sera de pouvoir faire :

   ```text
   Vault KV v2
      │
      │ Kubernetes Auth
      ▼
   Vault Secrets Operator
      │
      │ synchronisation automatique
      ▼
   Secret Kubernetes "my-secret"
      │
      ▼
   Deployment "my-app"
      │
      ├── USERNAME
      └── PASSWORD
   ```

   Ton principe `VaultStaticSecret` est bien celui qu'il faut utiliser : VSO synchronise un secret Vault vers un `Secret` Kubernetes natif, que le Pod peut ensuite consommer. 

   > **Important :** pour le lab je vais utiliser Vault en **dev mode**. C'est parfait pour apprendre, mais le stockage est en mémoire et les données sont perdues au redémarrage. Ce mode ne doit donc pas être utilisé en production. 1. Architecture du lab

   Nous allons utiliser :

   - **K3s** : cluster Kubernetes mono-nœud
   - **Vault** : namespace `vault`
   - **Vault Secrets Operator** : namespace `vault-secrets-operator`
   - **Application** : namespace `my-ns`
   - Vault KV v2 : mount `kvv2`
   - Vault Kubernetes Auth : mount `demo-auth-mount`
   - Vault role : `demo`
   - Kubernetes ServiceAccount : `default`
   - Vault secret :

   ```text
   kvv2/my-app/config
   ```

   contenant :

   ```text
   username=admin
   password=SuperSecret123!
   ```

   Le secret sera synchronisé vers :

   ```text
   my-ns/my-secret
   ```

   ------

   # 2. Prérequis

   Je pars sur une machine Linux avec environ :

   ```text
   2 CPU
   4 Go RAM minimum
   20 Go disque
   ```

   Pour un lab confortable, je conseille plutôt :

   ```text
   4 CPU
   8 Go RAM
   ```

   K3s fournit directement `kubectl` et son kubeconfig après installation. Une installation mono-nœud est déjà un cluster Kubernetes fonctionnel.

   ------

   # 3. Installation de K3s

   Sur ta VM :

   ```bash
   curl -sfL https://get.k3s.io | sh -
   ```

   Puis :

   ```bash
   sudo kubectl get nodes
   ```

   Tu dois obtenir quelque chose comme :

   ```text
   NAME        STATUS   ROLES                  AGE   VERSION
   k3s-node    Ready    control-plane,master   1m    v1.x.x+k3s
   ```

   Vérifie également :

   ```bash
   sudo kubectl get pods -A
   ```

   Tu dois voir les composants K3s.

   Pour travailler sans `sudo` :

   ```bash
   mkdir -p ~/.kube
   sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
   sudo chown "$USER:$USER" ~/.kube/config
   chmod 600 ~/.kube/config
   ```

   Puis :

   ```bash
   kubectl get nodes
   ```

   ------

   # 4. Installer Helm

   Si Helm n'est pas présent :

   ```bash
   curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
   ```

   Vérifie :

   ```bash
   helm version
   ```

   Ajoute ensuite le repository HashiCorp :

   ```bash
   helm repo add hashicorp https://helm.releases.hashicorp.com
   helm repo update
   ```

   ------

   # 5. Installer Vault

   Nous allons créer son namespace :

   ```bash
   kubectl create namespace vault
   ```

   Puis installer Vault en mode développement :

   ```bash
   helm install vault hashicorp/vault \
     --namespace vault \
     --set server.dev.enabled=true \
     --set server.dev.devRootToken=root
   ```

   HashiCorp documente explicitement `server.dev.enabled=true` pour installer un Vault de développement via le chart Helm. HashiCorp Developer+1

   Vérifie :

   ```bash
   kubectl get pods -n vault
   ```

   Tu dois obtenir :

   ```text
   NAME      READY   STATUS    RESTARTS   AGE
   vault-0   1/1     Running   0          ...
   ```

   Vérifie également le service :

   ```bash
   kubectl get svc -n vault
   ```

   Tu devrais avoir notamment :

   ```text
   vault   ClusterIP   ...   8200/TCP
   ```

   C'est précisément ce qui permettra d'utiliser :

   ```text
   http://vault.vault.svc.cluster.local:8200
   ```

   comme adresse Vault dans `VaultConnection`. HashiCorp utilise également ce type d'adresse pour une installation Vault dans Kubernetes. HashiCorp Developer+1

   ------

   # 6. Vérifier Vault

   On peut entrer dans le Pod :

   ```bash
   kubectl exec -it -n vault vault-0 -- sh
   ```

   Puis :

   ```bash
   export VAULT_ADDR=http://127.0.0.1:8200
   export VAULT_TOKEN=root
   ```

   Vérifie :

   ```bash
   vault status
   ```

   Tu devrais avoir quelque chose comme :

   ```text
   Initialized     true
   Sealed          false
   ```

   Puis :

   ```bash
   exit
   ```

   ------

   # 7. Créer le namespace de l'application

   ```bash
   kubectl create namespace my-ns
   ```

   Vérifie :

   ```bash
   kubectl get ns
   ```

   Tu dois maintenant avoir :

   ```text
   vault
   my-ns
   ```

   ------

   # 8. Installer Vault Secrets Operator

   HashiCorp recommande l'installation de VSO avec Helm. HashiCorp Developer

   Installe-le :

   ```bash
   helm install vault-secrets-operator \
     hashicorp/vault-secrets-operator \
     --namespace vault-secrets-operator \
     --create-namespace
   ```

   Vérifie :

   ```bash
   kubectl get pods -n vault-secrets-operator
   ```

   Tu dois obtenir un Pod du genre :

   ```text
   vault-secrets-operator-controller-manager-xxxxx   2/2   Running
   ```

   Vérifie les CRD :

   ```bash
   kubectl get crd | grep secrets.hashicorp.com
   ```

   Tu devrais voir notamment :

   ```text
   vaultauths.secrets.hashicorp.com
   vaultconnections.secrets.hashicorp.com
   vaultstaticsecrets.secrets.hashicorp.com
   ```

   ------

   # 9. Préparer l'authentification Kubernetes de Vault

   C'est une partie importante du lab.

   Le fonctionnement est :

   ```text
   Pod / VSO
         │
         │ ServiceAccount JWT
         ▼
   Vault Kubernetes Auth
         │
         │ TokenReview
         ▼
   Kubernetes API
   ```

   Vault vérifie ainsi que le JWT du ServiceAccount Kubernetes est valide. C'est précisément le rôle de Kubernetes Auth dans Vault. HashiCorp Developer+1

   Dans notre lab, Vault lui-même tourne dans Kubernetes.

   Vault peut utiliser automatiquement son propre ServiceAccount token comme `token_reviewer_jwt`, ce qui est justement recommandé lorsque Vault tourne dans un Pod Kubernetes. HashiCorp Developer

   ------

   # 10. Donner à Vault le droit de faire TokenReview

   Crée :

   ```yaml
   apiVersion: rbac.authorization.k8s.io/v1
   kind: ClusterRoleBinding
   metadata:
     name: vault-auth-delegator
   roleRef:
     apiGroup: rbac.authorization.k8s.io
     kind: ClusterRole
     name: system:auth-delegator
   subjects:
     - kind: ServiceAccount
       name: vault
       namespace: vault
   ```

   Enregistre-le :

   ```bash
   nano vault-auth-rbac.yaml
   ```

   Puis :

   ```bash
   kubectl apply -f vault-auth-rbac.yaml
   ```

   Vérifie :

   ```bash
   kubectl get clusterrolebinding vault-auth-delegator
   ```

   ------

   # 11. Configurer Kubernetes Auth dans Vault

   Retourne dans Vault :

   ```bash
   kubectl exec -it -n vault vault-0 -- sh
   ```

   Puis :

   ```bash
   export VAULT_ADDR=http://127.0.0.1:8200
   export VAULT_TOKEN=root
   ```

   Active le backend Kubernetes Auth avec le nom que tu utilises dans ton `VaultAuth` :

   ```bash
   vault auth enable -path=demo-auth-mount kubernetes
   ```

   Tu dois obtenir :

   ```text
   Success! Enabled kubernetes auth method at: demo-auth-mount/
   ```

   Maintenant configure-le :

   ```bash
   vault write auth/demo-auth-mount/config \
     kubernetes_host="https://$KUBERNETES_SERVICE_HOST:$KUBERNETES_SERVICE_PORT"
   ```

   C'est une configuration supportée par Vault lorsqu'il tourne dans Kubernetes ; Vault utilise alors automatiquement le token et le CA montés dans son Pod. HashiCorp Developer+1

   Vérifie :

   ```bash
   vault read auth/demo-auth-mount/config
   ```

   ------

   # 12. Activer KV v2

   Toujours dans le Pod Vault :

   ```bash
   vault secrets enable -path=kvv2 kv-v2
   ```

   Vérifie :

   ```bash
   vault secrets list
   ```

   Tu dois voir :

   ```text
   kvv2/    kv    Key-Value Secrets
   ```

   ------

   # 13. Créer notre secret Vault

   Nous allons créer :

   ```text
   kvv2/my-app/config
   ```

   avec :

   ```text
   username=admin
   password=SuperSecret123!
   ```

   Commande :

   ```bash
   vault kv put kvv2/my-app/config \
     username="admin" \
     password="SuperSecret123!"
   ```

   Vérifie :

   ```bash
   vault kv get kvv2/my-app/config
   ```

   Tu devrais voir :

   ```text
   ===== Data =====
   Key         Value
   ---         -----
   password    SuperSecret123!
   username    admin
   ```

   ------

   # 14. Créer la policy Vault

   Maintenant nous devons dire à Vault :

   > le rôle Kubernetes `demo` peut uniquement lire `kvv2/my-app/config`.

   Crée :

   ```bash
   cat > /tmp/my-app-policy.hcl <<'EOF'
   path "kvv2/data/my-app/config" {
     capabilities = ["read"]
   }
   EOF
   ```

   Puis :

   ```bash
   vault policy write my-app-policy /tmp/my-app-policy.hcl
   ```

   Vérifie :

   ```bash
   vault policy read my-app-policy
   ```

   ### Pourquoi `kvv2/data/...` ?

   C'est très important.

   Pour KV v2, le chemin API utilisé par Vault pour lire les données contient :

   ```text
   data/
   ```

   Alors que le chemin logique du secret reste :

   ```text
   my-app/config
   ```

   C'est pourquoi ton `VaultStaticSecret` aura :

   ```yaml
   mount: kvv2
   path: my-app/config
   type: kv-v2
   ```

   et la policy aura :

   ```text
   kvv2/data/my-app/config
   ```

   ------

   # 15. Créer le rôle Kubernetes Vault

   Nous voulons autoriser :

   ```text
   ServiceAccount: default
   Namespace: my-ns
   ```

   à utiliser le rôle :

   ```text
   demo
   ```

   Exécute :

   ```bash
   vault write auth/demo-auth-mount/role/demo \
     bound_service_account_names=default \
     bound_service_account_namespaces=my-ns \
     policies=my-app-policy \
     ttl=1h
   ```

   Vérifie :

   ```bash
   vault read auth/demo-auth-mount/role/demo
   ```

   Tu devrais voir notamment :

   ```text
   bound_service_account_names       [default]
   bound_service_account_namespaces  [my-ns]
   policies                           [my-app-policy]
   ```

   Le fait de limiter simultanément le ServiceAccount et le namespace est essentiel : le rôle Vault ne doit pas être utilisable par n'importe quel Pod du cluster. HashiCorp recommande également de spécifier un ServiceAccount propre à l'application dans les environnements réels. HashiCorp Developer+1

   Pour notre lab, nous conservons `default` afin de rester conforme à ton manifeste.

   ------

   # 16. Sortir de Vault

   ```bash
   exit
   ```

   ------

   # 17. Créer le VaultConnection

   Ton premier fichier était presque correct.

   Je te conseille :

   ```yaml
   apiVersion: secrets.hashicorp.com/v1beta1
   kind: VaultConnection
   metadata:
     name: my-vault-connection
     namespace: my-ns
   spec:
     address: http://vault.vault.svc.cluster.local:8200
   ```

   Enregistre :

   ```bash
   nano vault-connection.yaml
   ```

   Puis :

   ```bash
   kubectl apply -f vault-connection.yaml
   ```

   Vérifie :

   ```bash
   kubectl get vaultconnection -n my-ns
   ```

   Puis :

   ```bash
   kubectl describe vaultconnection my-vault-connection -n my-ns
   ```

   ------

   # 18. Créer le VaultAuth

   Maintenant :

   ```yaml
   apiVersion: secrets.hashicorp.com/v1beta1
   kind: VaultAuth
   metadata:
     name: my-vault-auth
     namespace: my-ns
   spec:
     method: kubernetes
     mount: demo-auth-mount
   
     kubernetes:
       role: demo
       serviceAccount: default
   
     vaultConnectionRef: my-vault-connection
   ```

   Enregistre :

   ```bash
   nano vault-auth.yaml
   ```

   Puis :

   ```bash
   kubectl apply -f vault-auth.yaml
   ```

   Vérifie :

   ```bash
   kubectl get vaultauth -n my-ns
   ```

   Puis :

   ```bash
   kubectl describe vaultauth my-vault-auth -n my-ns
   ```

   Le `VaultAuth` indique à VSO **comment s'authentifier** auprès de Vault, tandis que `VaultConnection` indique **où trouver Vault**. C'est exactement la séparation prévue par les CRD VSO. HashiCorp Developer+1

   ------

   # 19. Créer le VaultStaticSecret

   Voici ton manifeste corrigé :

   ```yaml
   apiVersion: secrets.hashicorp.com/v1beta1
   kind: VaultStaticSecret
   metadata:
     name: vault-static-secret
     namespace: my-ns
   spec:
     vaultAuthRef: my-vault-auth
   
     mount: kvv2
     type: kv-v2
     path: my-app/config
   
     refreshAfter: 10s
   
     destination:
       create: true
       name: my-secret
   ```

   Enregistre :

   ```bash
   nano vault-static-secret.yaml
   ```

   Puis :

   ```bash
   kubectl apply -f vault-static-secret.yaml
   ```

   Vérifie :

   ```bash
   kubectl get vaultstaticsecret -n my-ns
   ```

   Puis :

   ```bash
   kubectl describe vaultstaticsecret vault-static-secret -n my-ns
   ```

   ------

   # 20. Vérifier la synchronisation

   C'est le moment intéressant.

   Fais :

   ```bash
   kubectl get secret -n my-ns
   ```

   Tu devrais obtenir :

   ```text
   NAME        TYPE     DATA   AGE
   my-secret   Opaque   2      ...
   ```

   Regarde son contenu :

   ```bash
   kubectl get secret my-secret -n my-ns -o yaml
   ```

   Tu verras quelque chose comme :

   ```yaml
   apiVersion: v1
   kind: Secret
   metadata:
     name: my-secret
     namespace: my-ns
   type: Opaque
   data:
     password: ...
     username: ...
   ```

   Les valeurs sont encodées en Base64, donc pour vérifier :

   ```bash
   kubectl get secret my-secret \
     -n my-ns \
     -o jsonpath='{.data.username}' | base64 -d
   ```

   Résultat :

   ```text
   admin
   ```

   Puis :

   ```bash
   kubectl get secret my-secret \
     -n my-ns \
     -o jsonpath='{.data.password}' | base64 -d
   ```

   Résultat :

   ```text
   SuperSecret123!
   ```

   ------

   # 21. Déployer ton application

   Ton Deployment peut être utilisé quasiment tel quel.

   Je te propose cette version :

   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: my-app
     namespace: my-ns
   spec:
     replicas: 1
   
     selector:
       matchLabels:
         app: my-app
   
     template:
       metadata:
         labels:
           app: my-app
   
       spec:
         serviceAccountName: default
   
         containers:
           - name: my-app-container
             image: alpine:3.22
   
             env:
               - name: USERNAME
                 valueFrom:
                   secretKeyRef:
                     name: my-secret
                     key: username
   
               - name: PASSWORD
                 valueFrom:
                   secretKeyRef:
                     name: my-secret
                     key: password
   
             command:
               - /bin/sh
               - -c
   
             args:
               - |
                 echo "Application démarrée"
                 echo "USERNAME=$USERNAME"
                 echo "PASSWORD=$PASSWORD"
                 sleep infinity
   ```

   Enregistre :

   ```bash
   nano deployment.yaml
   ```

   Puis :

   ```bash
   kubectl apply -f deployment.yaml
   ```

   Vérifie :

   ```bash
   kubectl get pods -n my-ns
   ```

   Puis :

   ```bash
   kubectl logs -n my-ns deployment/my-app
   ```

   Tu devrais obtenir :

   ```text
   Application démarrée
   USERNAME=admin
   PASSWORD=SuperSecret123!
   ```

   ------

   # 22. Vérifier directement les variables du Pod

   Récupère le nom :

   ```bash
   kubectl get pods -n my-ns
   ```

   Puis :

   ```bash
   kubectl exec -it -n my-ns deploy/my-app -- env | grep -E 'USERNAME|PASSWORD'
   ```

   Résultat :

   ```text
   USERNAME=admin
   PASSWORD=SuperSecret123!
   ```

   Tu as maintenant réalisé :

   ```text
                      VAULT
                        │
                        │
                kvv2/my-app/config
                        │
                        ▼
                 Kubernetes Auth
                        │
                        ▼
                Vault Secrets Operator
                        │
                        ▼
                VaultStaticSecret
                        │
                        ▼
                Kubernetes Secret
                   my-secret
                        │
                        ▼
                   Deployment
                     my-app
                        │
                 ┌──────┴──────┐
                 ▼             ▼
             USERNAME       PASSWORD
   ```

   ------

   # 23. Tester la rotation du secret

   C'est une partie très importante du lab.

   Retourne dans Vault :

   ```bash
   kubectl exec -it -n vault vault-0 -- sh
   ```

   Puis :

   ```bash
   export VAULT_ADDR=http://127.0.0.1:8200
   export VAULT_TOKEN=root
   ```

   Modifie le mot de passe :

   ```bash
   vault kv put kvv2/my-app/config \
     username="admin" \
     password="NewPassword456!"
   ```

   Vérifie :

   ```bash
   vault kv get kvv2/my-app/config
   ```

   Quitte :

   ```bash
   exit
   ```

   ------

   # 24. Observer VSO

   Ton `VaultStaticSecret` possède :

   ```yaml
   refreshAfter: 10s
   ```

   Donc VSO va régulièrement vérifier le secret.

   Attends une dizaine de secondes puis :

   ```bash
   kubectl get secret my-secret \
     -n my-ns \
     -o jsonpath='{.data.password}' | base64 -d
   ```

   Tu dois maintenant obtenir :

   ```text
   NewPassword456!
   ```

   Tu viens donc de démontrer :

   ```text
   Vault secret modifié
          │
          ▼
   VaultStaticSecret
          │
          ▼
   VSO détecte le changement
          │
          ▼
   Kubernetes Secret modifié
   ```

   Le champ `refreshAfter` est justement prévu pour contrôler cette fréquence de rafraîchissement. HashiCorp Developer

   ------

   # 25. Attention : le Deployment ne recharge pas forcément la variable

   C'est un point Kubernetes très important.

   Ton application utilise :

   ```yaml
   env:
     - name: PASSWORD
       valueFrom:
         secretKeyRef:
           name: my-secret
           key: password
   ```

   La modification du `Secret` Kubernetes **ne change pas automatiquement la variable d'environnement déjà chargée dans un conteneur existant**.

   Donc :

   ```text
   Vault
     │
     ▼
   Secret Kubernetes
     │
     ▼
   PASSWORD dans nouveau Pod
   ```

   mais le Pod existant peut continuer à avoir :

   ```text
   PASSWORD=SuperSecret123!
   ```

   Pour voir le nouveau secret dans le Pod, fais :

   ```bash
   kubectl rollout restart deployment my-app -n my-ns
   ```

   Puis :

   ```bash
   kubectl logs -n my-ns deployment/my-app
   ```

   Tu devrais maintenant voir :

   ```text
   Application démarrée
   USERNAME=admin
   PASSWORD=NewPassword456!
   ```

   ------

   # 26. Tester la suppression du secret Kubernetes

   Maintenant, on peut vérifier que VSO est réellement responsable du Secret.

   ```bash
   kubectl delete secret my-secret -n my-ns
   ```

   Vérifie :

   ```bash
   kubectl get secret my-secret -n my-ns
   ```

   Il peut disparaître momentanément.

   Puis :

   ```bash
   kubectl get secret my-secret -n my-ns
   ```

   VSO doit le recréer puisque :

   ```yaml
   destination:
     create: true
   ```

   Cela démontre la logique :

   ```text
                Vault
                  │
                  │ source de vérité
                  ▼
          VaultStaticSecret
                  │
                  ▼
                 VSO
                  │
                  ▼
          Kubernetes Secret
                  │
                  └── reconciliation
   ```

   ------

   # 27. Voir les logs de VSO

   Très utile pour le troubleshooting :

   ```bash
   kubectl logs \
     -n vault-secrets-operator \
     deployment/vault-secrets-operator-controller-manager \
     -c manager \
     --tail=100
   ```

   Tu peux aussi faire :

   ```bash
   kubectl get events -n my-ns --sort-by=.lastTimestamp
   ```

   ------

   # 28. Vérification complète

   À la fin du lab :

   ```bash
   kubectl get pods -A
   ```

   Puis :

   ```bash
   kubectl get vaultconnection -n my-ns
   kubectl get vaultauth -n my-ns
   kubectl get vaultstaticsecret -n my-ns
   kubectl get secret -n my-ns
   kubectl get deployment -n my-ns
   ```

   Tu dois avoir quelque chose ressemblant à :

   ```text
   Vault
   └── vault-0                         Running
   
   VSO
   └── vault-secrets-operator-xxx     Running
   
   my-ns
   ├── VaultConnection                my-vault-connection
   ├── VaultAuth                      my-vault-auth
   ├── VaultStaticSecret              vault-static-secret
   ├── Secret                         my-secret
   └── Deployment                     my-app
   ```

   ------

   # 29. Tous les manifests du lab

   Pour éviter de manipuler plusieurs fichiers, tu peux organiser le lab ainsi :

   ```text
   k3s-vault-lab/
   ├── 01-vault-auth-rbac.yaml
   ├── 02-vault-connection.yaml
   ├── 03-vault-auth.yaml
   ├── 04-vault-static-secret.yaml
   └── 05-deployment.yaml
   ```

   ### `01-vault-auth-rbac.yaml`

   ```yaml
   apiVersion: rbac.authorization.k8s.io/v1
   kind: ClusterRoleBinding
   metadata:
     name: vault-auth-delegator
   roleRef:
     apiGroup: rbac.authorization.k8s.io
     kind: ClusterRole
     name: system:auth-delegator
   subjects:
     - kind: ServiceAccount
       name: vault
       namespace: vault
   ```

   ### `02-vault-connection.yaml`

   ```yaml
   apiVersion: secrets.hashicorp.com/v1beta1
   kind: VaultConnection
   metadata:
     name: my-vault-connection
     namespace: my-ns
   spec:
     address: http://vault.vault.svc.cluster.local:8200
   ```

   ### `03-vault-auth.yaml`

   ```yaml
   apiVersion: secrets.hashicorp.com/v1beta1
   kind: VaultAuth
   metadata:
     name: my-vault-auth
     namespace: my-ns
   spec:
     method: kubernetes
     mount: demo-auth-mount
   
     kubernetes:
       role: demo
       serviceAccount: default
   
     vaultConnectionRef: my-vault-connection
   ```

   ### `04-vault-static-secret.yaml`

   ```yaml
   apiVersion: secrets.hashicorp.com/v1beta1
   kind: VaultStaticSecret
   metadata:
     name: vault-static-secret
     namespace: my-ns
   spec:
     vaultAuthRef: my-vault-auth
   
     mount: kvv2
     type: kv-v2
     path: my-app/config
   
     refreshAfter: 10s
   
     destination:
       create: true
       name: my-secret
   ```

   ### `05-deployment.yaml`

   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: my-app
     namespace: my-ns
   spec:
     replicas: 1
   
     selector:
       matchLabels:
         app: my-app
   
     template:
       metadata:
         labels:
           app: my-app
   
       spec:
         serviceAccountName: default
   
         containers:
           - name: my-app-container
             image: alpine:3.22
   
             env:
               - name: USERNAME
                 valueFrom:
                   secretKeyRef:
                     name: my-secret
                     key: username
   
               - name: PASSWORD
                 valueFrom:
                   secretKeyRef:
                     name: my-secret
                     key: password
   
             command:
               - /bin/sh
               - -c
   
             args:
               - |
                 echo "Application démarrée"
                 echo "USERNAME=$USERNAME"
                 echo "PASSWORD=$PASSWORD"
                 sleep infinity
   ```

   ------

   # 30. Commandes d'installation résumées

   Si tu veux refaire le lab rapidement :

   ```bash
   # K3s
   curl -sfL https://get.k3s.io | sh -
   
   # kubeconfig
   mkdir -p ~/.kube
   sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
   sudo chown "$USER:$USER" ~/.kube/config
   
   # Helm
   curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
   
   # HashiCorp repo
   helm repo add hashicorp https://helm.releases.hashicorp.com
   helm repo update
   
   # namespaces
   kubectl create namespace vault
   kubectl create namespace my-ns
   
   # Vault
   helm install vault hashicorp/vault \
     --namespace vault \
     --set server.dev.enabled=true \
     --set server.dev.devRootToken=root
   
   # VSO
   helm install vault-secrets-operator \
     hashicorp/vault-secrets-operator \
     --namespace vault-secrets-operator \
     --create-namespace
   ```

   Puis :

   ```bash
   kubectl apply -f 01-vault-auth-rbac.yaml
   kubectl apply -f 02-vault-connection.yaml
   kubectl apply -f 03-vault-auth.yaml
   kubectl apply -f 04-vault-static-secret.yaml
   kubectl apply -f 05-deployment.yaml
   ```

   ------

   # 31. Le point essentiel à retenir

   Les trois objets que tu avais fournis ont des rôles différents :

   ### `VaultConnection`

   ```yaml
   kind: VaultConnection
   ```

   répond à :

   > **Où est Vault ?**

   ```text
   http://vault.vault.svc.cluster.local:8200
   ```

   ### `VaultAuth`

   ```yaml
   kind: VaultAuth
   ```

   répond à :

   > **Comment VSO s'authentifie auprès de Vault ?**

   Ici :

   ```text
   Kubernetes Auth
         │
         ├── mount = demo-auth-mount
         ├── role = demo
         └── serviceAccount = default
   ```

   ### `VaultStaticSecret`

   ```yaml
   kind: VaultStaticSecret
   ```

   répond à :

   > **Quel secret Vault dois-je synchroniser vers Kubernetes ?**

   ```text
   Vault mount : kvv2
   Vault path  : my-app/config
          │
          ▼
   Kubernetes Secret
          │
          └── my-secret
   ```

   Puis ton Deployment ne connaît **rien de Vault** :

   ```yaml
   secretKeyRef:
     name: my-secret
   ```

   C'est justement l'un des intérêts de VSO : l'application consomme un Secret Kubernetes natif tandis que VSO s'occupe de la synchronisation avec Vault. HashiCorp Developer

   ## Documentation de référence

   - K3s — Quick Start
   - Vault Helm — installation sur Kubernetes
   - Vault Secrets Operator — installation
   - Vault Secrets Operator — VaultConnection / VaultAuth / VaultStaticSecret
   - Vault Kubernetes Authentication

   **Pour aller plus loin**, le lab intéressant suivant serait de remplacer le `default` ServiceAccount par un **ServiceAccount dédié `my-app`**, ajouter un **NetworkPolicy**, passer Vault du mode `dev` au mode **standalone avec stockage persistant**, puis tester une **rotation de secret sans redémarrage manuel du Deployment**. Ce serait une très bonne étape pour transformer ce lab pédagogique en environnement Kubernetes/Vault beaucoup plus réaliste.

   K![img](https://www.google.com/s2/favicons?domain=https%3A%2F%2Fdocs.k3s.io&sz=128)Sources

   

   

   

2. #### You said:

3. #### ChatGPT said:

   

   Je ne peux pas créer directement le fichier téléchargeable ici car **Canvas n’est pas disponible dans cette session**.

   En revanche, je peux te fournir immédiatement le contenu complet sous forme de fichier `k3s-vault-vso-lab.md` à copier dans ton éditeur, avec **tous les manifests, commandes et étapes du lab**.

   

   

4. #### You said:

5. #### ChatGPT said:

   

   Oui. Et dans ce cas il faut **reprendre le lab précédent en remplaçant complètement Vault Secrets Operator (VSO) par External Secrets Operator (ESO)**.

   La différence fondamentale est que les CRD `VaultConnection`, `VaultAuth` et `VaultStaticSecret` ne sont plus utilisés. Avec ESO, on utilise principalement :

   ```text
   SecretStore
   ExternalSecret
   ```

   ESO dispose d'un provider natif HashiCorp Vault et supporte l'authentification Kubernetes. E!external-secrets.io+1

   ## Architecture du nouveau lab

   On conserve exactement le même scénario :

   ```text
                            K3s
                             │
             ┌───────────────┴────────────────┐
             │                                │
             ▼                                ▼
          Vault                         External Secrets
        namespace vault                Operator
             │                                │
             │ KV v2                         │
             │                                │
             ▼                                │
       kvv2/my-app/config                    │
             │                                │
             │ Kubernetes Auth                │
             │                                │
             └───────────────► SecretStore ◄──┘
                                      │
                                      ▼
                                ExternalSecret
                                      │
                                      ▼
                            Kubernetes Secret
                               my-secret
                                      │
                                      ▼
                                 Deployment
                                   my-app
                                      │
                            ┌─────────┴─────────┐
                            ▼                   ▼
                         USERNAME            PASSWORD
   ```

   Le point important est qu'ESO utilise un `SecretStore` pour configurer le backend Vault et un `ExternalSecret` pour définir le secret Kubernetes à synchroniser. E!external-secrets.io+1

   ------

   # 1. Installation K3s

   ```bash
   curl -sfL https://get.k3s.io | sh -
   ```

   Vérification :

   ```bash
   sudo kubectl get nodes
   ```

   Puis configuration du kubeconfig :

   ```bash
   mkdir -p ~/.kube
   
   sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
   
   sudo chown "$USER:$USER" ~/.kube/config
   
   chmod 600 ~/.kube/config
   ```

   Test :

   ```bash
   kubectl get nodes
   ```

   ------

   # 2. Installer Helm

   ```bash
   curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
   ```

   Puis :

   ```bash
   helm version
   ```

   ------

   # 3. Installer Vault

   Ajouter le repository HashiCorp :

   ```bash
   helm repo add hashicorp https://helm.releases.hashicorp.com
   helm repo update
   ```

   Créer le namespace :

   ```bash
   kubectl create namespace vault
   ```

   Installer Vault en mode développement :

   ```bash
   helm install vault hashicorp/vault \
     --namespace vault \
     --set server.dev.enabled=true \
     --set server.dev.devRootToken=root
   ```

   Vérifier :

   ```bash
   kubectl get pods -n vault
   ```

   Résultat attendu :

   ```text
   NAME      READY   STATUS    RESTARTS   AGE
   vault-0   1/1     Running   0          ...
   ```

   ------

   # 4. Créer le namespace de l'application

   ```bash
   kubectl create namespace my-ns
   ```

   ------

   # 5. Installer External Secrets Operator

   C'est ici que nous remplaçons complètement VSO.

   ESO recommande l'installation via son chart Helm officiel. E!external-secrets.io

   ```bash
   helm repo add external-secrets https://charts.external-secrets.io
   helm repo update
   ```

   Installation :

   ```bash
   helm install external-secrets \
     external-secrets/external-secrets \
     --namespace external-secrets \
     --create-namespace
   ```

   Vérifier :

   ```bash
   kubectl get pods -n external-secrets
   ```

   Tu devrais avoir quelque chose comme :

   ```text
   NAME                                                READY   STATUS
   external-secrets-xxxxxxxxx                          1/1     Running
   external-secrets-cert-controller-xxxxxxxxx          1/1     Running
   external-secrets-webhook-xxxxxxxxx                  1/1     Running
   ```

   Vérifie les CRD :

   ```bash
   kubectl get crd | grep external-secrets
   ```

   Tu dois notamment retrouver :

   ```text
   externalsecrets.external-secrets.io
   secretstores.external-secrets.io
   clustersecretstores.external-secrets.io
   ```

   ------

   # 6. Configurer Vault

   Nous conservons exactement la même configuration Vault que dans ton premier lab.

   Entrer dans Vault :

   ```bash
   kubectl exec -it -n vault vault-0 -- sh
   ```

   Puis :

   ```bash
   export VAULT_ADDR=http://127.0.0.1:8200
   export VAULT_TOKEN=root
   ```

   ------

   # 7. Activer Kubernetes Auth

   On utilise ton nom de mount :

   ```text
   demo-auth-mount
   ```

   Commande :

   ```bash
   vault auth enable -path=demo-auth-mount kubernetes
   ```

   Puis :

   ```bash
   vault write auth/demo-auth-mount/config \
     kubernetes_host="https://$KUBERNETES_SERVICE_HOST:$KUBERNETES_SERVICE_PORT"
   ```

   ------

   # 8. Donner à Vault le droit de faire TokenReview

   Créer ce fichier sur ta machine :

   ```yaml
   apiVersion: rbac.authorization.k8s.io/v1
   kind: ClusterRoleBinding
   metadata:
     name: vault-auth-delegator
   roleRef:
     apiGroup: rbac.authorization.k8s.io
     kind: ClusterRole
     name: system:auth-delegator
   subjects:
     - kind: ServiceAccount
       name: vault
       namespace: vault
   ```

   Enregistre-le :

   ```bash
   nano vault-auth-rbac.yaml
   ```

   Puis :

   ```bash
   kubectl apply -f vault-auth-rbac.yaml
   ```

   C'est également une exigence du provider Vault d'ESO pour l'authentification Kubernetes : le ServiceAccount utilisé doit pouvoir effectuer des `TokenReview`. E!external-secrets.io

   ------

   # 9. Activer KV v2

   Toujours dans Vault :

   ```bash
   vault secrets enable -path=kvv2 kv-v2
   ```

   Puis :

   ```bash
   vault secrets list
   ```

   Tu dois avoir :

   ```text
   kvv2/    kv    Key-Value Secrets
   ```

   ------

   # 10. Créer le secret Vault

   On reprend exactement le même secret :

   ```bash
   vault kv put kvv2/my-app/config \
     username="admin" \
     password="SuperSecret123!"
   ```

   Vérification :

   ```bash
   vault kv get kvv2/my-app/config
   ```

   Résultat :

   ```text
   ===== Data =====
   Key         Value
   ---         -----
   password    SuperSecret123!
   username    admin
   ```

   ------

   # 11. Créer la policy Vault

   Crée :

   ```bash
   cat > /tmp/my-app-policy.hcl <<'EOF'
   path "kvv2/data/my-app/config" {
     capabilities = ["read"]
   }
   EOF
   ```

   Puis :

   ```bash
   vault policy write my-app-policy /tmp/my-app-policy.hcl
   ```

   Vérifie :

   ```bash
   vault policy read my-app-policy
   ```

   ------

   # 12. Créer le rôle Kubernetes Vault

   Avec les versions récentes de Vault/ESO, il est préférable de définir explicitement l'audience du JWT Kubernetes. La documentation ESO signale notamment qu'à partir de Vault 1.21, une audience est nécessaire pour les rôles Kubernetes. E!external-secrets.io

   Nous allons donc créer le rôle avec :

   ```text
   audience = vault
   ```

   Commande :

   ```bash
   vault write auth/demo-auth-mount/role/demo \
     bound_service_account_names=default \
     bound_service_account_namespaces=my-ns \
     policies=my-app-policy \
     audience="vault" \
     ttl=1h
   ```

   Vérifie :

   ```bash
   vault read auth/demo-auth-mount/role/demo
   ```

   ------

   # 13. Quitter Vault

   ```bash
   exit
   ```

   ------

   # 14. Le changement majeur avec ESO

   Avec VSO tu avais :

   ```yaml
   kind: VaultConnection
   ```

   puis :

   ```yaml
   kind: VaultAuth
   ```

   puis :

   ```yaml
   kind: VaultStaticSecret
   ```

   Avec **External Secrets Operator**, on va avoir :

   ```text
   SecretStore
        │
        ▼
   ExternalSecret
        │
        ▼
   Secret Kubernetes
   ```

   Le provider Vault d'ESO configure notamment :

   ```yaml
   server:
   path:
   version:
   auth:
   ```

   et son mode Kubernetes Auth utilise le ServiceAccount pour s'authentifier auprès de Vault. E!external-secrets.io

   ------

   # 15. Créer le SecretStore

   Voici l'équivalent de tes `VaultConnection + VaultAuth`.

   Crée :

   ```yaml
   apiVersion: external-secrets.io/v1
   kind: SecretStore
   metadata:
     name: vault-backend
     namespace: my-ns
   spec:
     provider:
       vault:
         server: "http://vault.vault.svc.cluster.local:8200"
   
         path: "kvv2"
   
         version: "v2"
   
         auth:
           kubernetes:
             mountPath: "demo-auth-mount"
             role: "demo"
   
             serviceAccountRef:
               name: default
               audiences:
                 - vault
   ```

   Enregistre :

   ```bash
   nano secret-store.yaml
   ```

   Puis :

   ```bash
   kubectl apply -f secret-store.yaml
   ```

   Vérifie :

   ```bash
   kubectl get secretstore -n my-ns
   ```

   Puis :

   ```bash
   kubectl describe secretstore vault-backend -n my-ns
   ```

   Tu veux obtenir un état :

   ```text
   Ready: True
   ```

   ### Pourquoi `path: kvv2` ?

   Parce que `kvv2` est le **mount** du moteur KV.

   Nous avons :

   ```text
   Vault
   
   kvv2/
   └── my-app/
       └── config
   ```

   Dans le `SecretStore` :

   ```yaml
   path: kvv2
   version: v2
   ```

   Puis dans l'`ExternalSecret`, nous référencerons :

   ```text
   my-app/config
   ```

   Le provider Vault d'ESO supporte KV v1 et KV v2 et ajoute la logique spécifique au KV v2 lors de la récupération. E!external-secrets.io+1

   ------

   # 16. Créer l'ExternalSecret

   C'est maintenant l'équivalent de ton :

   ```yaml
   kind: VaultStaticSecret
   ```

   Crée :

   ```yaml
   apiVersion: external-secrets.io/v1
   kind: ExternalSecret
   metadata:
     name: vault-static-secret
     namespace: my-ns
   
   spec:
     refreshInterval: 10s
   
     secretStoreRef:
       name: vault-backend
       kind: SecretStore
   
     target:
       name: my-secret
       creationPolicy: Owner
   
     data:
       - secretKey: username
         remoteRef:
           key: my-app/config
           property: username
   
       - secretKey: password
         remoteRef:
           key: my-app/config
           property: password
   ```

   Enregistre :

   ```bash
   nano external-secret.yaml
   ```

   Puis :

   ```bash
   kubectl apply -f external-secret.yaml
   ```

   Vérifie :

   ```bash
   kubectl get externalsecret -n my-ns
   ```

   Puis :

   ```bash
   kubectl describe externalsecret vault-static-secret -n my-ns
   ```

   Tu dois avoir :

   ```text
   Ready: True
   ```

   ------

   # 17. Vérifier le Secret Kubernetes

   ESO devrait maintenant avoir créé :

   ```text
   my-secret
   ```

   Vérifie :

   ```bash
   kubectl get secret -n my-ns
   ```

   Résultat :

   ```text
   NAME        TYPE     DATA   AGE
   my-secret   Opaque   2      ...
   ```

   Puis :

   ```bash
   kubectl get secret my-secret \
     -n my-ns \
     -o jsonpath='{.data.username}' | base64 -d
   ```

   Résultat :

   ```text
   admin
   ```

   Et :

   ```bash
   kubectl get secret my-secret \
     -n my-ns \
     -o jsonpath='{.data.password}' | base64 -d
   ```

   Résultat :

   ```text
   SuperSecret123!
   ```

   ------

   # 18. Deployment

   On reprend ton Deployment quasiment **exactement**.

   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: my-app
     namespace: my-ns
   
   spec:
     replicas: 1
   
     selector:
       matchLabels:
         app: my-app
   
     template:
       metadata:
         labels:
           app: my-app
   
       spec:
         serviceAccountName: default
   
         containers:
           - name: my-app-container
             image: alpine:3.22
   
             env:
               - name: USERNAME
                 valueFrom:
                   secretKeyRef:
                     name: my-secret
                     key: username
   
               - name: PASSWORD
                 valueFrom:
                   secretKeyRef:
                     name: my-secret
                     key: password
   
             command:
               - /bin/sh
               - -c
   
             args:
               - |
                 echo "Application démarrée"
                 echo "USERNAME=$USERNAME"
                 echo "PASSWORD=$PASSWORD"
                 sleep infinity
   ```

   Puis :

   ```bash
   kubectl apply -f deployment.yaml
   ```

   ------

   # 19. Vérifier le Pod

   ```bash
   kubectl get pods -n my-ns
   ```

   Puis :

   ```bash
   kubectl logs -n my-ns deployment/my-app
   ```

   Résultat attendu :

   ```text
   Application démarrée
   USERNAME=admin
   PASSWORD=SuperSecret123!
   ```

   ------

   # 20. Tester la synchronisation

   Maintenant nous allons modifier Vault.

   ```bash
   kubectl exec -it -n vault vault-0 -- sh
   ```

   Puis :

   ```bash
   export VAULT_ADDR=http://127.0.0.1:8200
   export VAULT_TOKEN=root
   ```

   Modifie :

   ```bash
   vault kv put kvv2/my-app/config \
     username="admin" \
     password="NewPassword456!"
   ```

   Quitte :

   ```bash
   exit
   ```

   Attends environ 10 secondes.

   Puis :

   ```bash
   kubectl get secret my-secret \
     -n my-ns \
     -o jsonpath='{.data.password}' | base64 -d
   ```

   Tu dois maintenant obtenir :

   ```text
   NewPassword456!
   ```

   La chaîne complète est donc :

   ```text
   Vault
     │
     │ password=NewPassword456!
     ▼
   KV v2
     │
     ▼
   ExternalSecret
     │
     ▼
   External Secrets Operator
     │
     ▼
   my-secret
     │
     ▼
   Kubernetes
   ```

   ------

   # 21. Tester le Deployment

   Attention au même comportement Kubernetes que dans le lab précédent.

   Le Secret Kubernetes a changé, mais une variable d'environnement déjà injectée dans un Pod existant **ne change pas automatiquement**.

   Donc :

   ```bash
   kubectl exec -it -n my-ns deploy/my-app -- env | grep PASSWORD
   ```

   peut encore afficher :

   ```text
   PASSWORD=SuperSecret123!
   ```

   Redémarre le Deployment :

   ```bash
   kubectl rollout restart deployment my-app -n my-ns
   ```

   Puis :

   ```bash
   kubectl logs -n my-ns deployment/my-app
   ```

   Tu dois obtenir :

   ```text
   Application démarrée
   USERNAME=admin
   PASSWORD=NewPassword456!
   ```

   ------

   # 22. Tester la réconciliation ESO

   Supprime le Secret Kubernetes :

   ```bash
   kubectl delete secret my-secret -n my-ns
   ```

   Puis :

   ```bash
   kubectl get secret my-secret -n my-ns
   ```

   Après la réconciliation ESO :

   ```text
   NAME        TYPE     DATA   AGE
   my-secret   Opaque   2      ...
   ```

   ESO l'a recréé depuis Vault.

   ------

   # 23. Vérifier les événements ESO

   Très utile pour comprendre les erreurs :

   ```bash
   kubectl describe externalsecret \
     vault-static-secret \
     -n my-ns
   ```

   Et :

   ```bash
   kubectl get events \
     -n my-ns \
     --sort-by=.lastTimestamp
   ```

   Les logs du controller :

   ```bash
   kubectl logs \
     -n external-secrets \
     deployment/external-secrets \
     --tail=100
   ```

   ------

   # 24. Comparaison VSO → ESO

   Ton ancien lab :

   | Fonction         | Vault Secrets Operator |
   | ---------------- | ---------------------- |
   | Connexion Vault  | `VaultConnection`      |
   | Authentification | `VaultAuth`            |
   | Synchronisation  | `VaultStaticSecret`    |
   | Operator         | VSO                    |

   

   Le nouveau lab :

   | Fonction         | External Secrets Operator              |
   | ---------------- | -------------------------------------- |
   | Connexion Vault  | `SecretStore`                          |
   | Authentification | `SecretStore.spec.provider.vault.auth` |
   | Synchronisation  | `ExternalSecret`                       |
   | Operator         | ESO                                    |

   

   Donc :

   ```text
   VSO
   │
   ├── VaultConnection
   ├── VaultAuth
   └── VaultStaticSecret
   ```

   devient :

   ```text
   ESO
   │
   ├── SecretStore
   └── ExternalSecret
   ```

   ------

   # 25. Les fichiers finaux

   Je te conseille cette structure :

   ```text
   k3s-vault-eso-lab/
   │
   ├── 01-vault-auth-rbac.yaml
   ├── 02-secret-store.yaml
   ├── 03-external-secret.yaml
   └── 04-deployment.yaml
   ```

   ### `01-vault-auth-rbac.yaml`

   ```yaml
   apiVersion: rbac.authorization.k8s.io/v1
   kind: ClusterRoleBinding
   metadata:
     name: vault-auth-delegator
   roleRef:
     apiGroup: rbac.authorization.k8s.io
     kind: ClusterRole
     name: system:auth-delegator
   subjects:
     - kind: ServiceAccount
       name: vault
       namespace: vault
   ```

   ### `02-secret-store.yaml`

   ```yaml
   apiVersion: external-secrets.io/v1
   kind: SecretStore
   metadata:
     name: vault-backend
     namespace: my-ns
   
   spec:
     provider:
       vault:
         server: "http://vault.vault.svc.cluster.local:8200"
         path: "kvv2"
         version: "v2"
   
         auth:
           kubernetes:
             mountPath: "demo-auth-mount"
             role: "demo"
   
             serviceAccountRef:
               name: default
               audiences:
                 - vault
   ```

   ### `03-external-secret.yaml`

   ```yaml
   apiVersion: external-secrets.io/v1
   kind: ExternalSecret
   metadata:
     name: vault-static-secret
     namespace: my-ns
   
   spec:
     refreshInterval: 10s
   
     secretStoreRef:
       name: vault-backend
       kind: SecretStore
   
     target:
       name: my-secret
       creationPolicy: Owner
   
     data:
       - secretKey: username
         remoteRef:
           key: my-app/config
           property: username
   
       - secretKey: password
         remoteRef:
           key: my-app/config
           property: password
   ```

   ### `04-deployment.yaml`

   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: my-app
     namespace: my-ns
   
   spec:
     replicas: 1
   
     selector:
       matchLabels:
         app: my-app
   
     template:
       metadata:
         labels:
           app: my-app
   
       spec:
         serviceAccountName: default
   
         containers:
           - name: my-app-container
             image: alpine:3.22
   
             env:
               - name: USERNAME
                 valueFrom:
                   secretKeyRef:
                     name: my-secret
                     key: username
   
               - name: PASSWORD
                 valueFrom:
                   secretKeyRef:
                     name: my-secret
                     key: password
   
             command:
               - /bin/sh
               - -c
   
             args:
               - |
                 echo "Application démarrée"
                 echo "USERNAME=$USERNAME"
                 echo "PASSWORD=$PASSWORD"
                 sleep infinity
   ```

   ------

   ## Le lab complet en une image mentale

   ```text
                        ┌──────────────────────┐
                        │        K3s            │
                        │                      │
                        │  ┌────────────────┐  │
                        │  │     Vault      │  │
                        │  │                │  │
                        │  │ Kubernetes Auth│  │
                        │  │       │        │  │
                        │  │     KV v2      │  │
                        │  │       │        │  │
                        │  │ my-app/config  │  │
                        │  └───────┬────────┘  │
                        │          │           │
                        │          │           │
                        │  ┌───────▼────────┐  │
                        │  │ External       │  │
                        │  │ Secrets        │  │
                        │  │ Operator       │  │
                        │  └───────┬────────┘  │
                        │          │           │
                        │          │           │
                        │  ┌───────▼────────┐  │
                        │  │ ExternalSecret │  │
                        │  └───────┬────────┘  │
                        │          │           │
                        │          ▼           │
                        │  ┌────────────────┐  │
                        │  │ Secret         │  │
                        │  │ my-secret      │  │
                        │  └───────┬────────┘  │
                        │          │           │
                        │          ▼           │
                        │  ┌────────────────┐  │
                        │  │ Deployment     │  │
                        │  │ my-app         │  │
                        │  │                │  │
                        │  │ USERNAME       │  │
                        │  │ PASSWORD       │  │
                        │  └────────────────┘  │
                        └──────────────────────┘
   ```

   **Point important :** contrairement au lab VSO précédent, il n'y a ici **aucun `VaultConnection`, `VaultAuth` ou `VaultStaticSecret`**. ESO utilise son `SecretStore` + `ExternalSecret`, et le provider Vault supporte directement Kubernetes Auth et KV v2. E!external-secrets.io+1

   Si ton objectif final est d'avoir un **lab réellement prêt à copier-coller**, je peux aussi te produire la version sous forme d'un **unique `README.md` complet**, avec l'arborescence, tous les fichiers YAML, les commandes `kubectl`/`helm`, les tests de rotation et une section **troubleshooting ESO/Vault**.
