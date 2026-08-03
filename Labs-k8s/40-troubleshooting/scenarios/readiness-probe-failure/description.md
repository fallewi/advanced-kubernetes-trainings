## Readiness Probe Failure

### Description:
The pod is marked as not ready because the readiness probe fails, preventing the pod from receiving traffic. In this scenario, the readiness probe is configured to check a non-existent path (`/nonexistent`) on the nginx container. Since that path returns a 404 error, the probe always fails and the pod stays in a "not ready" state.

### Causes:
- Incorrectly configured readiness probe path that does not exist on the application.
- The application inside the pod is not responding as expected on the probed endpoint.
- Wrong port specified in the readiness probe configuration.

### Fix:
1. Check the readiness probe configuration and adjust the `path` to match an actual endpoint served by the application (e.g., `/` for nginx).
2. Verify the application inside the pod is running and able to handle requests on the specified path and port.
3. Test the pod's health by manually sending requests to the probe's endpoint using `kubectl exec`.
4. Increase the `initialDelaySeconds` and `timeoutSeconds` if the application takes longer to start.
