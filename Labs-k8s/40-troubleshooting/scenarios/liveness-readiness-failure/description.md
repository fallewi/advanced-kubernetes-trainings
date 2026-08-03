## Liveness/Readiness Probe Failure

### Description:
Both the liveness and readiness probes fail because they check a non-existent path (`/nonexistent`) on the nginx container. The liveness probe failure causes Kubernetes to restart the container repeatedly (CrashLoopBackOff), while the readiness probe failure prevents the pod from receiving traffic.

### Causes:
- Misconfigured probe paths that do not match any valid application endpoint.
- Both probes returning non-200 HTTP status codes (404 Not Found).

### Fix:
1. Update both liveness and readiness probe paths to valid endpoints (e.g., `/` for nginx).
2. Verify the application responds with a 200 status on the configured probe paths.
3. Adjust probe timing parameters (`initialDelaySeconds`, `periodSeconds`, `failureThreshold`) as needed.
4. Use `kubectl describe pod <pod-name>` to check probe failure events and `kubectl logs` for application logs.
