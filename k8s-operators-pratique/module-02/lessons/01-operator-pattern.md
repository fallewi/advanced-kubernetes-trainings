# Leçon 2.1 : Le modèle Operator

**Navigation :** [Vue d'ensemble du module](../README.md) | [Leçon suivante : Les fondamentaux de Kubebuilder →](02-kubebuilder-fundamentals.md)

# Introduction

Dans le **Module 1**, nous avons étudié les mécanismes fondamentaux qui font fonctionner Kubernetes :

- l'architecture du plan de contrôle ;
- le rôle du serveur API ;
- les contrôleurs Kubernetes ;
- le modèle de réconciliation (*Reconciliation Loop*) ;
- les **Custom Resources** ;
- les **Custom Resource Definitions (CRD)**.

Ces différents concepts constituent les briques élémentaires sur lesquelles repose l'ensemble de l'écosystème Kubernetes.

Cependant, il manque encore une pièce essentielle : **l'intelligence métier**.

En effet, Kubernetes sait parfaitement gérer des ressources génériques telles que les Pods, les Deployments ou les StatefulSets, mais il ne possède aucune connaissance spécifique concernant une base PostgreSQL, un cluster Kafka, un serveur Redis ou encore un système de sauvegarde.

Par exemple, Kubernetes ne sait pas :

- comment initialiser une base PostgreSQL ;
- comment promouvoir un réplica en serveur principal après une panne ;
- comment effectuer une sauvegarde cohérente ;
- comment restaurer automatiquement une base de données ;
- comment mettre à niveau une application complexe sans interruption de service.

Toutes ces opérations nécessitent une expertise propre au domaine concerné.

C'est précisément cette expertise qu'apportent les **Operators**.

Un Operator est bien plus qu'un simple contrôleur Kubernetes.

Il s'agit d'un logiciel capable de transformer des procédures d'exploitation traditionnellement réalisées par des administrateurs système en un ensemble de règles automatisées exécutées en permanence dans le cluster.

En d'autres termes, un Operator permet de transformer le savoir-faire humain en logiciel.

Cette approche constitue aujourd'hui l'un des piliers de Kubernetes et explique pourquoi la majorité des plateformes cloud natives modernes reposent sur des Operators.



# Théorie : le modèle Operator

Un **Operator** est un modèle d'architecture permettant de déployer, d'exploiter et d'administrer des applications Kubernetes de manière entièrement déclarative.

Il repose principalement sur trois composants :

- une ou plusieurs **Custom Resource Definitions (CRD)** ;
- un **contrôleur Kubernetes** ;
- une logique métier propre à l'application administrée.

L'Operator observe en permanence les ressources personnalisées créées par les utilisateurs.

À chaque modification, il compare :

- **l'état souhaité** décrit dans le champ `spec` ;
- **l'état réel** observé dans le cluster.

S'il détecte une différence entre ces deux états, il agit automatiquement afin de rétablir la situation.

Autrement dit, un Operator applique exactement le même modèle de réconciliation que les contrôleurs natifs de Kubernetes.

La différence réside dans le fait qu'il possède une connaissance approfondie d'un domaine particulier.

Par exemple :

- un Operator PostgreSQL connaît les mécanismes de réplication ;
- un Operator Kafka sait créer des brokers et répartir les partitions ;
- un Operator Elasticsearch maîtrise les notions de nœuds maîtres, de nœuds de données et de rééquilibrage du cluster.

Cette connaissance spécifique est appelée **connaissance opérationnelle** (*Operational Knowledge*).



# La philosophie des Operators

Les Operators ne sont pas seulement des programmes.

Ils incarnent une nouvelle manière d'administrer les applications.

Au lieu de rédiger des procédures d'exploitation décrivant les étapes à suivre, on développe un logiciel capable d'exécuter ces procédures automatiquement.

L'objectif est de remplacer des opérations manuelles répétitives par une automatisation fiable et reproductible.

Cette philosophie repose sur plusieurs principes fondamentaux.



## La connaissance opérationnelle devient du code

Traditionnellement, le fonctionnement d'une application complexe est documenté dans des guides d'exploitation.

On y retrouve par exemple :

- les étapes d'installation ;
- les procédures de mise à jour ;
- les sauvegardes ;
- les restaurations ;
- les procédures de reprise après incident ;
- les opérations de maintenance.

Ces documents peuvent rapidement devenir obsolètes.

Ils dépendent également fortement des compétences des administrateurs.

Les Operators adoptent une approche radicalement différente.

Toute cette connaissance est directement intégrée dans le code du contrôleur.

Ainsi :

- les procédures sont toujours exécutées de la même manière ;
- les erreurs humaines sont fortement réduites ;
- les opérations deviennent reproductibles ;
- les meilleures pratiques sont systématiquement appliquées.

On parle alors de **Knowledge as Code** ou **Operational Knowledge as Code**.

Cette approche est comparable au principe de l'**Infrastructure as Code**, mais appliquée aux opérations d'exploitation.



## Une automatisation en libre-service

L'un des grands objectifs des Operators est de simplifier le travail des utilisateurs.

Au lieu d'effectuer eux-mêmes toutes les opérations techniques, ils décrivent simplement le résultat souhaité.

Par exemple :

```yaml
apiVersion: database.company.com/v1
kind: PostgreSQL
metadata:
  name: production-db
spec:
  version: "16"
  replicas: 3
  storage: 500Gi
```

Ce manifeste ne décrit pas les Pods, les Services ou les volumes à créer.

Il exprime uniquement l'objectif.

L'Operator prend ensuite le relais.

Il décide automatiquement :

- quels StatefulSets créer ;
- quels Services déployer ;
- quels PersistentVolumeClaims générer ;
- comment configurer la réplication ;
- comment initialiser la base de données.

L'utilisateur se concentre sur le **quoi**.

L'Operator se charge du **comment**.

Cette séparation est l'un des fondements du modèle déclaratif de Kubernetes.



## Une intégration native à Kubernetes

Contrairement à certains outils externes d'automatisation, un Operator ne contourne jamais Kubernetes.

Au contraire, il utilise exactement les mêmes mécanismes que les composants natifs.

Il s'appuie notamment sur :

- le serveur API ;
- les CRD ;
- les mécanismes `Watch` ;
- les événements Kubernetes ;
- RBAC ;
- les contrôleurs ;
- les boucles de réconciliation.

Pour l'utilisateur, un Operator se comporte donc comme une fonctionnalité native de Kubernetes.

Les ressources qu'il introduit peuvent être manipulées avec :

```bash
kubectl get

kubectl describe

kubectl edit

kubectl delete
```

sans nécessiter d'outil spécifique.

Cette parfaite intégration explique pourquoi les Operators s'insèrent naturellement dans les plateformes GitOps, les solutions d'observabilité ou encore les outils de sauvegarde.



# Pourquoi les Operators sont-ils si importants ?

Les applications modernes sont devenues extrêmement complexes.

Prenons l'exemple d'une base PostgreSQL haute disponibilité.

Son administration implique notamment :

- l'installation des serveurs ;
- la configuration de la réplication ;
- la gestion des certificats ;
- les sauvegardes automatiques ;
- la restauration ;
- les mises à niveau ;
- la surveillance de la santé du cluster ;
- le remplacement automatique des nœuds défaillants.

Sans Operator, toutes ces tâches devraient être réalisées manuellement.

Avec un Operator, elles sont automatisées.

Les avantages sont nombreux.

## Automatisation

Les tâches répétitives sont exécutées automatiquement.

L'administrateur n'intervient plus que pour définir les objectifs.



## Cohérence

Chaque déploiement suit exactement les mêmes règles.

Les risques liés aux erreurs humaines sont fortement réduits.



## Capitalisation de l'expertise

Les bonnes pratiques ne sont plus uniquement connues par quelques experts.

Elles sont intégrées directement dans le logiciel.

Chaque nouveau déploiement bénéficie automatiquement de cette expertise.



## Gestion complète du cycle de vie

Contrairement à un simple outil de déploiement, un Operator accompagne l'application durant toute sa vie.

Il peut gérer :

- l'installation ;
- la configuration ;
- les mises à jour ;
- les sauvegardes ;
- les restaurations ;
- la montée en charge ;
- la reprise après incident ;
- la suppression propre des ressources.

On parle alors de **gestion du cycle de vie** (*Lifecycle Management*).



# Les niveaux de maturité des Operators

Tous les Operators n'offrent pas les mêmes fonctionnalités.

La communauté Kubernetes a défini un **Operator Capability Model**, qui classe les Operators selon leur niveau de sophistication.

De manière simplifiée :

| Niveau | Capacités principales |
|--||
| **Niveau 1** | Installation automatisée de l'application. |
| **Niveau 2** | Gestion des mises à jour et de la configuration. |
| **Niveau 3** | Gestion complète du cycle de vie (installation, sauvegardes, restauration, montée en charge, maintenance). |
| **Niveau 4** | Automatisation avancée basée sur l'observation de l'état du système. |
| **Niveau 5** | Auto-réparation (*Self-Healing*), optimisation continue et exploitation largement autonome. |

La majorité des Operators utilisés en production visent au minimum le **niveau 3**, qui offre une gestion complète de l'application tout au long de son cycle de vie.

> ## À retenir
>
> Un **Operator** est un contrôleur Kubernetes spécialisé qui combine des **Custom Resource Definitions (CRD)** avec une logique métier avancée afin d'automatiser l'administration d'une application. Il transforme les procédures d'exploitation traditionnellement réalisées par des administrateurs en code exécutable, capable d'observer en permanence le cluster, de détecter les écarts entre l'état souhaité et l'état réel, puis d'effectuer automatiquement les actions nécessaires pour maintenir le système conforme aux attentes de l'utilisateur.
>
