## File Permissions on Mounted Volumes

### Description:
A pod fails because it cannot write to the filesystem. When `readOnlyRootFilesystem` is set to `true` in the security context, all writes to the root filesystem are denied. This is a security best practice, but applications that need to write temporary files will fail unless writable volumes are mounted.

### How to Reproduce:
The `issue.yaml` creates a pod with `readOnlyRootFilesystem: true` that tries to write to `/tmp/test.txt`. The write fails because the entire root filesystem is read-only, causing the container to exit with an error.

### Causes:
- `readOnlyRootFilesystem: true` set without providing writable volume mounts for directories the application needs to write to.
- Application writes to paths that are not backed by mounted volumes.

### Fix:
1. Identify which directories the application needs to write to (e.g., `/tmp`, `/var/log`).
2. Mount an `emptyDir` volume at those paths to provide a writable layer.
3. The `fix.yaml` keeps `readOnlyRootFilesystem: true` but adds an `emptyDir` volume mounted at `/tmp`, allowing the application to write temporary files securely.
