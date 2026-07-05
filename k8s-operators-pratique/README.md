# Création d'Opérateurs Kubernetes avec Kubebuilder

> Une formation complète, pratique et entièrement gratuite pour apprendre à concevoir des opérateurs Kubernetes prêts pour la production à l'aide de **Kubebuilder**.

# Présentation de la formation

Cette formation a été conçue pour vous apprendre à développer des **opérateurs Kubernetes** depuis leurs fondations jusqu'à leur mise en production.

Au fil des chapitres, vous découvrirez les mécanismes internes de Kubernetes, comprendrez le fonctionnement du **Control Plane**, explorerez le **Controller Pattern**, puis apprendrez à utiliser **Kubebuilder** afin de créer vos propres opérateurs capables d'automatiser le cycle de vie d'applications complexes.

Contrairement à une simple présentation théorique, cette formation adopte une approche résolument pratique : chaque notion est illustrée par des démonstrations, des laboratoires et des exemples directement exploitables dans un environnement professionnel.

L'objectif est de vous permettre d'acquérir les compétences nécessaires pour développer des opérateurs robustes, évolutifs et conformes aux bonnes pratiques utilisées dans les environnements Kubernetes modernes.

# Informations générales

| Élément | Description |
|-|-|
| **Durée estimée** | 8 semaines (40 à 50 heures de travail) |
| **Niveau** | Intermédiaire à avancé |
| **Prérequis** | Bonnes connaissances de Kubernetes, bases du langage Go, compréhension de la conteneurisation |
| **Licence** | Formation libre et open source distribuée sous licence MIT |



# Organisation de la formation

La formation est organisée en **huit modules progressifs**.

Chaque module développe les connaissances acquises dans le précédent afin de construire progressivement une compréhension approfondie du développement d'opérateurs Kubernetes.



# Module 1 — Exploration approfondie de l'architecture Kubernetes

Ce premier module pose les fondations indispensables à toute la formation.

Vous étudierez le fonctionnement interne de Kubernetes afin de comprendre comment les opérateurs s'intègrent naturellement dans son architecture.

### Contenu

- Les composants du Control Plane
- Les mécanismes internes de l'API Kubernetes (API Machinery)
- Le Controller Pattern
- Les ressources personnalisées (Custom Resources)



# Module 2 — Introduction aux opérateurs Kubernetes

Après avoir compris l'architecture du cluster, vous découvrirez le concept d'**Operator Pattern**, véritable pierre angulaire de l'automatisation Kubernetes.

Vous apprendrez également à utiliser Kubebuilder pour générer rapidement une structure de projet professionnelle.

### Contenu

- Le modèle Operator Pattern
- Les fondamentaux de Kubebuilder
- Préparation de l'environnement de développement
- Création du premier opérateur



# Module 3 — Développement de contrôleurs personnalisés

Ce module est consacré au cœur du développement d'un opérateur.

Vous apprendrez à concevoir des contrôleurs capables d'observer l'état du cluster puis de prendre automatiquement les décisions nécessaires afin de maintenir l'état souhaité.

### Contenu

- Controller Runtime
- Conception d'une API Kubernetes
- Implémentation de la logique de réconciliation
- Manipulation des ressources avec client-go



# Module 4 — Techniques avancées de réconciliation

Une fois les bases maîtrisées, ce module introduit les mécanismes avancés utilisés dans les opérateurs de production.

Vous apprendrez notamment à gérer les statuts, les conditions, les finalizers ainsi que différentes stratégies d'observation des ressources.

### Contenu

- Gestion des Conditions et du Status
- Finalizers et nettoyage des ressources
- Watching et Indexing
- Modèles avancés de réconciliation



# Module 5 — Webhooks et contrôle d'admission

Les Webhooks permettent de contrôler les objets Kubernetes avant leur création ou leur modification.

Ce module explique leur fonctionnement et leur intégration avec Kubebuilder.

### Contenu

- Contrôle d'admission Kubernetes
- Webhooks de validation
- Webhooks de mutation
- Déploiement des Webhooks



# Module 6 — Tests et débogage

Le développement d'un opérateur ne s'arrête pas à l'écriture du code.

Ce module présente les méthodes permettant de garantir la qualité des développements grâce aux tests automatisés ainsi qu'aux outils de diagnostic.

### Contenu

- Fondamentaux des tests
- Tests unitaires avec EnvTest
- Tests d'intégration
- Débogage et observabilité



# Module 7 — Préparation à la production

Avant de déployer un opérateur dans un environnement réel, plusieurs aspects doivent être maîtrisés : sécurité, disponibilité, performances et distribution.

Ce module présente les meilleures pratiques utilisées dans les projets professionnels.

### Contenu

- Packaging et distribution
- RBAC et sécurité
- Haute disponibilité
- Performances et montée en charge



# Module 8 — Concepts avancés et cas d'utilisation réels

Le dernier module explore des architectures utilisées dans les grandes plateformes Kubernetes.

Vous découvrirez notamment les problématiques liées au multi-tenant, aux applications Stateful ainsi qu'à la composition d'opérateurs.



## Prérequis techniques

Avant de commencer cette formation, assurez-vous de disposer des outils suivants :

- Go 1.24 ou version supérieure
- kubectl & kubernetes
- Docker ou Podman
- Kubebuilder 4.7 ou version supérieure




# Méthode pédagogique

Cette formation repose sur une progression pédagogique inspirée des meilleures formations techniques professionnelles.

Chaque notion est introduite progressivement afin de construire une compréhension durable des concepts.

Les principaux axes pédagogiques sont les suivants :

- **Une approche fortement pratique** : chaque chapitre est accompagné d'exercices concrets.
- **Une forte dimension visuelle** : de nombreux diagrammes Mermaid illustrent les architectures, les échanges entre composants et les flux internes de Kubernetes.
- **Une montée progressive en complexité** : les premiers exemples sont volontairement simples avant d'évoluer vers des opérateurs complets destinés à la production.
- **Des cas d'usage réalistes** : les projets développés sont directement inspirés d'environnements professionnels.



# Ressources complémentaires

Pour approfondir certains sujets, les ressources suivantes sont recommandées :

- Documentation officielle de Kubebuilder
- Documentation officielle de l'API Kubernetes
- Documentation officielle de l'Operator Pattern
- Code complet de l'opérateur Hello World réalisé avec Kubebuilder
- Code complet d'un opérateur PostgreSQL développé tout au long de cette formation
