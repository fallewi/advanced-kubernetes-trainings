## Network Connectivity Issues

### Description:
A NetworkPolicy blocks all egress traffic from the pod, preventing it from reaching external services. The pod runs but cannot communicate outside the cluster.

### Causes:
- A NetworkPolicy with empty egress rules denies all outbound traffic for matching pods.
- Misconfigured network policies blocking legitimate traffic.

### Fix:
1. Identify and remove or modify the restrictive NetworkPolicy using `kubectl get networkpolicy`.
2. If egress restrictions are needed, add specific egress rules to allow required traffic.
3. Deploy the pod without the restrictive NetworkPolicy to restore connectivity.
4. Test connectivity using `kubectl exec` to run `wget` or `ping` commands from the pod.
