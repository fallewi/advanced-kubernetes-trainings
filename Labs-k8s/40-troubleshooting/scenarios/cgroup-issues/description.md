## CGroup Issues

### Description:
CGroup (control group) issues occur when a container exceeds the resource limits enforced by the Linux kernel's cgroup mechanism. When a container tries to use more memory than its cgroup limit allows, the kernel's OOM killer terminates the process, resulting in an OOMKilled status in Kubernetes.

### Causes:
- Memory limits set too low for the application's actual usage.
- Application memory leaks causing usage to exceed limits.
- Misconfigured cgroup settings in the container runtime.

### How to Reproduce:
The `issue.yaml` creates a pod using `polinux/stress` that attempts to allocate 100MB of memory but has a cgroup memory limit of only 50Mi. The kernel OOM killer terminates the process, causing the pod to enter OOMKilled/CrashLoopBackOff status.

### Fix:
1. Review the pod's resource limits and ensure they match the application's actual memory requirements.
2. Check pod status for OOMKilled events: `kubectl describe pod <pod-name>`.
3. Increase the memory limit to accommodate the application's needs.
4. The `fix.yaml` sets a memory limit of 256Mi with a workload that only uses 50MB, allowing the pod to run successfully.
