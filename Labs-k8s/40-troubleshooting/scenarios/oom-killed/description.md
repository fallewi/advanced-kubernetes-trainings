## OOM Killed

### Description:
The pod is terminated due to the Out of Memory (OOM) killer because the `polinux/stress` container attempts to allocate more memory than its limit allows.

### Causes:
- The container's memory limit (50Mi) is lower than the memory the stress tool tries to allocate (100M).
- Memory leaks or excessive resource usage in the application.

### Fix:
1. Increase the memory resource limits to accommodate the workload's actual memory needs.
2. Reduce the memory consumption of the workload (e.g., lower `--vm-bytes` for stress).
3. Monitor the pod's memory usage to identify spikes or memory leaks.
4. Use `kubectl describe pod <pod-name>` to confirm the OOMKilled reason.
