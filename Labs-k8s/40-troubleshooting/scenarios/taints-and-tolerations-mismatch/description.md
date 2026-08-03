## Taints and Tolerations Mismatch

### Description:
Pods fail to be scheduled on nodes due to mismatches in taints and tolerations, or because of node selectors that reference labels no node has. In this scenario, the pod uses a `nodeSelector` with a label (`non-existent-taint-label: "true"`) that does not exist on any node in the cluster, causing the pod to remain in a `Pending` state indefinitely.

Taints and tolerations work together to ensure pods are not scheduled onto inappropriate nodes. A taint on a node repels pods unless those pods have a matching toleration. Similarly, `nodeSelector` constrains pods to only run on nodes with specific labels.

### Causes:
- A node is tainted but the pod does not have the appropriate tolerations.
- A `nodeSelector` references a label that no node in the cluster has.
- Incorrect `tolerations` configuration in the pod spec (wrong key, value, or effect).

### Fix:
1. Remove or correct the `nodeSelector` so it matches labels that exist on cluster nodes.
2. Ensure the node taints are correctly defined using `kubectl describe node`.
3. Add the corresponding tolerations in the pod spec to match node taints.
4. Verify the pod's toleration values match the taint values on the node.
5. Use `kubectl get nodes --show-labels` to check available node labels.
6. Review the pod scheduling logs with `kubectl describe pod` to identify scheduling failures.
