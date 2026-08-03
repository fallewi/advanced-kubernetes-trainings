## Liveness Probe Failure

### Description:
The liveness probe fails because it checks a non-existent path (`/nonexistent`) on the nginx container. After the failure threshold is reached, Kubernetes kills and restarts the container, leading to a CrashLoopBackOff state.

### Causes:
- Incorrect probe path that returns a 404 status code.
- Misconfigured probe endpoint that does not match any route served by the application.

### Fix:
1. Update the liveness probe path to a valid endpoint (e.g., `/` for nginx).
2. Verify the application responds with a 200 status on the configured probe path.
3. Adjust `initialDelaySeconds`, `periodSeconds`, and `failureThreshold` as needed.
4. Use `kubectl describe pod <pod-name>` to check probe failure events.
