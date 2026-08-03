## Failed Resource Limits

### Description:
A pod is terminated (OOMKilled) because its workload exceeds the configured memory limits. Kubernetes enforces resource limits via cgroups, and exceeding them causes the kernel to kill the process.

### How to Reproduce:
The `issue.yaml` creates a pod running `polinux/stress` that tries to allocate 64MB of memory but has a limit of only 32Mi. The process is OOMKilled, causing CrashLoopBackOff.

### Causes:
- Memory limits set too low for the application's requirements.
- Application has a memory leak or unexpected memory consumption pattern.
- Resource limits not tested under realistic workloads.

### Fix:
1. Check pod events for OOMKilled: `kubectl describe pod <pod-name>`.
2. Monitor actual memory usage: `kubectl top pod <pod-name>`.
3. Set memory limits based on observed usage with appropriate headroom.
4. The `fix.yaml` sets a memory limit of 256Mi with a workload that only uses 50MB, running successfully.
