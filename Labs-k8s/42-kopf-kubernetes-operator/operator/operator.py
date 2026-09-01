import kopf
from kubernetes import client, config
from kubernetes.client.rest import ApiException

# ---------------------------------------------------------
# Configuration du client Kubernetes
# ---------------------------------------------------------
try:
    config.load_incluster_config()
except config.ConfigException:
    config.load_kube_config()

core_api = client.CoreV1Api()

# ---------------------------------------------------------
# Fonctions d'aide (Helpers) pour la réconciliation
# ---------------------------------------------------------

def validate_crd_spec(spec):
    """Vérifie la présence des champs obligatoires requis par la demande."""
    if "storageClass" not in spec or not spec["storageClass"]:
        raise kopf.PermanentError("Le champ 'storageClass' est obligatoire dans la CRD.")
    if "size" not in spec or not spec["size"]:
        raise kopf.PermanentError("Le champ 'size' est obligatoire dans la CRD.")

def reconcile_storage(spec, name, namespace, uid, logger):
    """ Boucle centrale de réconciliation : crée/vérifie le PV et le PVC """
    validate_crd_spec(spec)

    storage_class = spec["storageClass"]
    size = spec["size"]
    access_modes = spec.get("accessModes", ["ReadWriteOnce"])

    pv_name = f"{namespace}-{name}-pv"
    pvc_name = f"{name}-pvc"

    # --- ÉTAPE 1 : GESTION DU PERSISTENT VOLUME (PV) ---
    pv_exists = False
    try:
        pv = core_api.read_persistent_volume(name=pv_name)
        pv_exists = True
        logger.info(f"Le PV {pv_name} existe déjà. Statut actuel : {pv.status.phase if pv.status else 'Unknown'}")
    except ApiException as e:
        if e.status != 404:
            raise e

    if not pv_exists:
        logger.info(f"Le PV {pv_name} est manquant. Création en cours (Size: {size}, SC: {storage_class})...")
        # Construction du PV statique lié explicitement au PVC futur
        pv_manifest = client.V1PersistentVolume(
            metadata=client.V1ObjectMeta(
                name=pv_name,
                labels={
                    "app.kubernetes.io/managed-by": "evc-operator",
                    "storage.example.com/evc": name,
                },
                # Note : Pas d'owner reference namespace sur un objet global comme le PV, 
                # Kopf ou le PVC s'occuperont de la purge via finalizers si nécessaire.
            ),
            spec=client.V1PersistentVolumeSpec(
                capacity={"storage": size},
                access_modes=access_modes,
                storage_class_name=storage_class,
                # Lien bidirectionnel (Static Binding)
                claim_ref=client.V1ObjectReference(
                    name=pvc_name,
                    namespace=namespace
                ),
                # Type de stockage sous-jacent (adaptable selon votre infra, ex: hostPath pour test)
                host_path=client.V1HostPathVolumeSource(path=f"/mnt/data/{pv_name}")
            )
        )
        try:
            core_api.create_persistent_volume(body=pv_manifest)
            logger.info(f"PV {pv_name} créé avec succès.")
        except ApiException as e:
            if e.status != 409:
                raise e

    # --- ÉTAPE 2 : GESTION DU PERSISTENT VOLUME CLAIM (PVC) ---
    pvc_exists = False
    try:
        pvc = core_api.read_namespaced_persistent_volume_claim(name=pvc_name, namespace=namespace)
        pvc_exists = True
        logger.info(f"Le PVC {pvc_name} existe déjà. Statut actuel : {pvc.status.phase if pvc.status else 'Unknown'}")
    except ApiException as e:
        if e.status != 404:
            raise e

    if not pvc_exists:
        logger.info(f"Le PVC {pvc_name} est manquant. Création en cours...")
        pvc_manifest = client.V1PersistentVolumeClaim(
            metadata=client.V1ObjectMeta(
                name=pvc_name,
                namespace=namespace,
                labels={
                    "app.kubernetes.io/managed-by": "evc-operator",
                    "storage.example.com/evc": name,
                },
                owner_references=[
                    client.V1OwnerReference(
                        api_version="storage.example.com/v1",
                        kind="EphemeralVolumeClaim",
                        name=name,
                        uid=uid,
                        controller=True,
                        block_owner_deletion=True,
                    )
                ],
            ),
            spec=client.V1PersistentVolumeClaimSpec(
                access_modes=access_modes,
                storage_class_name=storage_class,
                volume_name=pv_name, # Force la liaison stricte avec notre PV créé ci-dessus
                resources=client.V1ResourceRequirements(
                    requests={"storage": size}
                ),
            ),
        )
        try:
            core_api.create_namespaced_persistent_volume_claim(namespace=namespace, body=pvc_manifest)
            logger.info(f"PVC {pvc_name} créé avec succès.")
        except ApiException as e:
            if e.status != 409:
                raise e

    # --- ÉTAPE 3 : VÉRIFICATION DU COUPLAGE (BOUND) ---
    try:
        updated_pvc = core_api.read_namespaced_persistent_volume_claim(name=pvc_name, namespace=namespace)
        phase = updated_pvc.status.phase if updated_pvc.status else "Unknown"
        return {"phase": phase, "pvName": pv_name, "pvcName": pvc_name}
    except ApiException:
        return {"phase": "Reconciling", "pvcName": pvc_name}


# ---------------------------------------------------------
# Handlers de l'Opérateur (Cycle de vie de la CRD)
# ---------------------------------------------------------

@kopf.on.create("storage.example.com", "v1", "ephemeralvolumeclaims")
@kopf.on.resume("storage.example.com", "v1", "ephemeralvolumeclaims")
@kopf.on.update("storage.example.com", "v1", "ephemeralvolumeclaims")
def reconcile_evc(spec, name, namespace, body, logger, **kwargs):
    """
    Déclenché à la création, mise à jour ou redémarrage de l'opérateur.
    Assure l'état désiré du PV et du PVC.
    """
    logger.info(f"Reconciliation demandée pour la CRD EVC: {name}")
    uid = body["metadata"]["uid"]
    status_metrics = reconcile_storage(spec, name, namespace, uid, logger)
    return status_metrics


@kopf.on.delete("storage.example.com", "v1", "ephemeralvolumeclaims")
def delete_evc(name, namespace, logger, **kwargs):
    """
    Gère le nettoyage. Le PVC est supprimé via l'OwnerReference Kubernetes automatiquement.
    Le PV (ressource globale) doit être nettoyé manuellement ici.
    """
    pv_name = f"{namespace}-{name}-pv"
    logger.info(f"Suppression de la CRD EVC {name}. Nettoyage manuel du PV {pv_name} associé.")
    
    try:
        core_api.delete_persistent_volume(name=pv_name)
        logger.info(f"PV {pv_name} marqué pour suppression.")
    except ApiException as e:
        if e.status != 404:
            logger.error(f"Erreur lors du nettoyage du PV {pv_name} : {e}")


# ---------------------------------------------------------
# Surveillance active (Boucle continue de réparation)
# ---------------------------------------------------------

@kopf.timer("storage.example.com", "v1", "ephemeralvolumeclaims", interval=10.0)
def continuous_reconciliation_timer(spec, name, namespace, body, logger, **kwargs):
    """
    S'exécute toutes les 10 secondes pour chaque instance de CRD présente.
    Si un administrateur supprime le PV ou le PVC manuellement, cette fonction 
    va détecter l'absence et forcer instantanément leur reconstruction.
    """
    uid = body["metadata"]["uid"]
    pv_name = f"{namespace}-{name}-pv"
    pvc_name = f"{name}-pvc"
    
    reconcile_needed = False
    
    # Check PVC
    try:
        core_api.read_namespaced_persistent_volume_claim(name=pvc_name, namespace=namespace)
    except ApiException as e:
        if e.status == 404:
            logger.warning(f"[ALERTE] Le PVC {pvc_name} a été supprimé manuellement ! Réparation requise.")
            reconcile_needed = True

    # Check PV
    try:
        core_api.read_persistent_volume(name=pv_name)
    except ApiException as e:
        if e.status == 404:
            logger.warning(f"[ALERTE] Le PV {pv_name} a été supprimé manuellement ! Réparation requise.")
            reconcile_needed = True

    if reconcile_needed:
        status_metrics = reconcile_storage(spec, name, namespace, uid, logger)
        return status_metrics
