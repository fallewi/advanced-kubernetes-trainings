import kopf
from kubernetes import client, config
from kubernetes.client.rest import ApiException


# ---------------------------------------------------------
# Kubernetes client
# ---------------------------------------------------------

config.load_incluster_config()

core_api = client.CoreV1Api()


# ---------------------------------------------------------
# CREATE
# ---------------------------------------------------------

@kopf.on.create(
    "storage.example.com",
    "v1",
    "ephemeralvolumeclaims",
)
def create_pvc(spec, name, namespace, body, logger, **kwargs):

    storage_class = spec["storageClass"]
    size = spec["size"]

    access_modes = spec.get(
        "accessModes",
        ["ReadWriteOnce"]
    )

    pvc_name = f"{name}-pvc"

    logger.info(
        f"Creating PVC {pvc_name} "
        f"(size={size}, storageClass={storage_class})"
    )

    pvc = client.V1PersistentVolumeClaim(
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
                    uid=body["metadata"]["uid"],
                    controller=True,
                    block_owner_deletion=True,
                )
            ],
        ),

        spec=client.V1PersistentVolumeClaimSpec(
            access_modes=access_modes,

            storage_class_name=storage_class,

            resources=client.V1ResourceRequirements(
                requests={
                    "storage": size
                }
            ),
        ),
    )

    try:

        core_api.create_namespaced_persistent_volume_claim(
            namespace=namespace,
            body=pvc,
        )

        logger.info(
            f"PVC {pvc_name} successfully created"
        )

    except ApiException as e:

        if e.status == 409:

            logger.info(
                f"PVC {pvc_name} already exists"
            )

        else:
            raise


    return {
        "phase": "Creating",
        "pvcName": pvc_name,
    }


# ---------------------------------------------------------
# UPDATE
# ---------------------------------------------------------

@kopf.on.update(
    "storage.example.com",
    "v1",
    "ephemeralvolumeclaims",
)
def update_evc(spec, name, namespace, body, logger, **kwargs):

    storage_class = spec["storageClass"]
    size = spec["size"]

    pvc_name = f"{name}-pvc"

    logger.info(
        f"EVC {name} updated"
    )

    try:

        pvc = core_api.read_namespaced_persistent_volume_claim(
            name=pvc_name,
            namespace=namespace,
        )

        logger.info(
            f"PVC {pvc_name} exists"
        )

        logger.info(
            f"Current PVC storage class: "
            f"{pvc.spec.storage_class_name}"
        )

        logger.info(
            f"Requested storage class: "
            f"{storage_class}"
        )

        logger.info(
            f"Requested size: {size}"
        )

    except ApiException as e:

        if e.status == 404:

            logger.warning(
                f"PVC {pvc_name} does not exist"
            )

        else:
            raise


# ---------------------------------------------------------
# DELETE
# ---------------------------------------------------------

@kopf.on.delete(
    "storage.example.com",
    "v1",
    "ephemeralvolumeclaims",
)
def delete_evc(name, namespace, logger, **kwargs):

    pvc_name = f"{name}-pvc"

    logger.info(
        f"Deleting EVC {name}"
    )

    logger.info(
        f"PVC {pvc_name} will be garbage collected"
    )


# ---------------------------------------------------------
# PVC events
# ---------------------------------------------------------

@kopf.timer(
    "storage.example.com",
    "v1",
    "ephemeralvolumeclaims",
    interval=10,
)
def check_pvc(spec, name, namespace, logger, **kwargs):

    pvc_name = f"{name}-pvc"

    try:

        pvc = core_api.read_namespaced_persistent_volume_claim(
            name=pvc_name,
            namespace=namespace,
        )

        phase = pvc.status.phase

        logger.info(
            f"EVC={name} PVC={pvc_name} phase={phase}"
        )

    except ApiException as e:

        if e.status == 404:

            logger.warning(
                f"PVC {pvc_name} not found"
            )

        else:
            raise
