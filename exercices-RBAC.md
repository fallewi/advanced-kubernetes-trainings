# Exercice RBAC – Gestion des applications dans un environnement d'entreprise

## Contexte

L'entreprise **TechCorp** dispose d'un cluster Kubernetes utilisé par plusieurs équipes.

L'équipe **Application Delivery** est responsable du déploiement et de la maintenance des applications dans le namespace **production**.

Pour des raisons de sécurité, les membres de cette équipe ne doivent disposer que des droits strictement nécessaires à leurs activités quotidiennes.

Un nouvel utilisateur, **jdupont**, rejoint l'équipe et doit recevoir les permissions adaptées.

---

## Besoin métier

L'utilisateur **jdupont** doit pouvoir :

### Sur les Pods

- Consulter les Pods
- Créer des Pods
- Modifier des Pods existants
- Consulter les logs des Pods

### Sur les Deployments

- Consulter les Deployments
- Créer des Deployments
- Modifier des Deployments

### Sur les StatefulSets

- Consulter les StatefulSets
- Créer des StatefulSets
- Modifier des StatefulSets

### Sur les CronJobs

- Consulter les CronJobs
- Créer des CronJobs
- Modifier des CronJobs

---

## Contraintes de sécurité

L'utilisateur **ne doit pas pouvoir** :

- Supprimer des ressources
- Consulter les Secrets
- Créer ou modifier des Roles
- Créer ou modifier des RoleBindings
- Créer ou modifier des ClusterRoles
- Créer ou modifier des ClusterRoleBindings
- Accéder aux ressources d'autres namespaces

---

# Travaux demandés

## Partie 1 : Analyse des besoins

À partir des exigences ci-dessus :

1. Identifier les API Groups concernés.
2. Identifier les ressources Kubernetes concernées.
3. Identifier les verbes RBAC nécessaires.
4. Déterminer si un `Role` ou un `ClusterRole` est le plus adapté.
5. Justifier votre choix.

---

## Partie 2 : Création des objets RBAC

Créer les objets Kubernetes nécessaires afin que :

- Les permissions soient limitées au namespace `production`.
- L'utilisateur `jdupont` dispose uniquement des droits décrits dans le besoin métier.
- Les contraintes de sécurité soient respectées.

Vous devrez produire :

- Le manifeste du rôle RBAC.
- Le manifeste permettant d'associer ce rôle à l'utilisateur.

---

## Partie 3 : Vérification des permissions

Écrire les commandes permettant de vérifier que l'utilisateur possède les droits nécessaires.

### Vérifications à effectuer

#### Pods

- Lire les Pods
- Créer un Pod
- Modifier un Pod
- Consulter les logs d'un Pod

#### Deployments

- Lire les Deployments
- Créer un Deployment
- Modifier un Deployment

#### StatefulSets

- Lire les StatefulSets
- Créer un StatefulSet
- Modifier un StatefulSet

#### CronJobs

- Lire les CronJobs
- Créer un CronJob
- Modifier un CronJob

---

## Partie 4 : Vérification des restrictions

Écrire les commandes permettant de vérifier que les actions suivantes sont interdites.

### Administration RBAC

- Créer un Role
- Modifier un Role
- Créer un RoleBinding
- Modifier un RoleBinding

### Secrets

- Lire un Secret
- Lister les Secrets

### Suppression

- Supprimer un Pod
- Supprimer un Deployment
- Supprimer un StatefulSet
- Supprimer un CronJob

---

## Partie 5 : Validation opérationnelle

Décrire les étapes permettant de :

1. Se connecter en tant que `jdupont`.
2. Déployer une application de test.
3. Modifier cette application.
4. Consulter les logs associés.
5. Vérifier qu'il est impossible d'accéder à un Secret.
6. Vérifier qu'il est impossible de supprimer le Deployment.
7. Vérifier qu'il est impossible de créer un nouvel objet RBAC.

---

# Livrables attendus

Le candidat devra fournir :

- Un manifeste YAML du rôle RBAC.
- Un manifeste YAML d'association du rôle à l'utilisateur.
- Les commandes de validation des permissions.
- Les commandes de validation des restrictions.
- Une courte justification du modèle RBAC retenu.

---

# Questions de réflexion

1. Pourquoi est-il dangereux d'attribuer le rôle `cluster-admin` à tous les utilisateurs ?
2. Quelle différence existe-t-il entre un `Role` et un `ClusterRole` ?
3. Quelle différence existe-t-il entre les verbes `update` et `patch` ?
4. Pourquoi l'accès aux logs doit-il être explicitement autorisé dans RBAC ?
5. Quel principe de sécurité est appliqué lorsqu'on n'accorde que les permissions strictement nécessaires à un utilisateur ?
6. Quels risques pourraient apparaître si un développeur obtenait un accès en lecture aux Secrets du namespace `production` ?
7. Dans quel cas serait-il pertinent d'utiliser un `ClusterRole` pour cette équipe ?
