## Firewall Restriction

### Description:
Pods cannot communicate with external services due to Kubernetes NetworkPolicy rules blocking egress traffic, simulating firewall restrictions.

### How to Reproduce:
The `issue.yaml` creates a pod with label `app: firewall-test` and a NetworkPolicy that denies all egress traffic for pods with that label. The pod's `wget` command to google.com times out because outbound traffic is blocked.

### Causes:
- NetworkPolicy rules blocking egress traffic.
- Missing egress rules in NetworkPolicy configurations.
- Firewall or security group rules on the underlying infrastructure.

### Fix:
1. Check NetworkPolicies affecting the pod: `kubectl get networkpolicies`.
2. Review the egress rules: `kubectl describe networkpolicy <name>`.
3. Either remove the restrictive NetworkPolicy or add appropriate egress rules.
4. The `fix.yaml` deploys the same pod without the NetworkPolicy, allowing normal egress traffic.
