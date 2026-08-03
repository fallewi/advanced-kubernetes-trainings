## DNS Resolution Failure

### Description:
Pods cannot resolve DNS queries, leading to failures in communication with services within the cluster or external endpoints.

### How to Reproduce:
The `issue.yaml` creates a pod with `dnsPolicy: None` and a bogus nameserver (192.0.2.1 - RFC 5737 TEST-NET address). The `nslookup` command fails because no valid DNS server is reachable. The pod stays running (via `|| sleep 3600`) so you can inspect the failure.

### Causes:
- DNS policy set to `None` without valid nameservers configured.
- CoreDNS or kube-dns service is down or misconfigured.
- Network policies blocking DNS traffic on port 53.

### Fix:
1. Use the default `dnsPolicy: ClusterFirst` to leverage the cluster's DNS service.
2. Verify CoreDNS is running: `kubectl get pods -n kube-system -l k8s-app=kube-dns`.
3. Test DNS resolution inside a pod: `kubectl exec <pod> -- nslookup kubernetes.default.svc.cluster.local`.
4. The `fix.yaml` uses the default ClusterFirst DNS policy, allowing proper DNS resolution.
