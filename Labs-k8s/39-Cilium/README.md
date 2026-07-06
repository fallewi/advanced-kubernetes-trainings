# CILIUM NETWORK POLICIES AND SERVICE MESH

# Cilium Network Policies: L3/L4/L7 Filtering - 

## Introduction

In the dynamic world of Kubernetes, securing inter-pod communication is paramount. While Kubernetes’ native `NetworkPolicy` resources offer foundational L3/L4 filtering, they often fall short in complex, microservices-driven architectures. This is where [Cilium](https://cilium.io/), an eBPF-powered CNI (Container Network Interface) plugin, steps in, revolutionizing network security with its unparalleled capabilities. Cilium extends network policy enforcement far beyond traditional IP and port rules, enabling deep packet inspection and L7 (application layer) filtering.

Imagine a scenario where you need to restrict access to a specific API endpoint based on HTTP path or method, or ensure that only authenticated Kafka clients can publish messages to a particular topic. Standard Kubernetes Network Policies can’t achieve this level of granularity. Cilium, leveraging the power of [eBPF](https://ebpf.io/), allows you to define policies that understand application protocols like HTTP, Kafka, gRPC, and more. This deep dive will guide you through the intricacies of crafting robust L3/L4/L7 Cilium Network Policies, empowering you to build a truly secure and observable Kubernetes environment. For a broader understanding of network security.

### TL;DR: Cilium Network Policies Deep Dive

Cilium Network Policies extend Kubernetes’ native L3/L4 policies with advanced L7 filtering using eBPF, enabling fine-grained control over application traffic (HTTP, Kafka, gRPC). This guide covers installation, L3/L4 policy creation (namespace, pod, CIDR, entity selectors), and sophisticated L7 policies. Key commands include installing Cilium via Helm, applying `CiliumNetworkPolicy` YAMLs, and using `cilium status` and `cilium monitor` for verification. Remember to explicitly allow traffic, as Cilium operates on a deny-all model by default once policies are in place.

**Key Commands:**

```bash

# Install Cilium
helm repo add cilium https://helm.cilium.io/
helm install cilium cilium/cilium --version 1.15.5 \
  --namespace kube-system \
  --set ipam.mode=cluster-pool \
  --set ipv4.enabled=true \
  --set tunnel=vxlan \
  --set enableIPv4BIGTCP=true \
  --set autoDirectNodeRoutes=true \
  --set kubeProxyReplacement=strict \
  --set bpf.masquerade=true \
  --set l7Proxy=true \
  --set policyEnforcementMode=always

# Check Cilium status
cilium status --wait

# Apply a Cilium Network Policy
kubectl apply -f your-cilium-policy.yaml

# Monitor network activity with policy decisions
cilium monitor --type policy --verbose

# Debug policy enforcement
cilium policy get

# Clean up Cilium
helm uninstall cilium --namespace kube-system
kubectl delete namespace test-app
```

## Prerequisites

Before we dive into the fascinating world of Cilium Network Policies, ensure you have the following:

- **Kubernetes Cluster:** A running Kubernetes cluster (v1.20+ recommended). You can use Minikube, Kind, or a cloud-managed cluster (EKS, GKE, AKS).
- **`kubectl`:** Configured to interact with your cluster. Refer to the [official Kubernetes documentation](https://kubernetes.io/docs/tasks/tools/install-kubectl/) for installation.
- **`helm`:** Version 3.x for installing Cilium. See the [Helm installation guide](https://helm.sh/docs/intro/install/).
- **`cilium-cli`:** The Cilium CLI tool for interacting with your Cilium installation. Install it via `brew install cilium-cli` (macOS) or follow the [official Cilium documentation](https://docs.cilium.io/en/stable/gettingstarted/k8s-install-default/#install-the-cilium-cli).
- **Basic Kubernetes Knowledge:** Familiarity with Pods, Deployments, Services, and Namespaces.
- **Basic Networking Concepts:** Understanding of IP addresses, ports, and network protocols.

## Step-by-Step Guide

### Step 1: Install Cilium on Your Kubernetes Cluster

First, we need to install Cilium as our CNI plugin. We’ll use Helm for a straightforward installation. It’s crucial to enable `l7Proxy=true` and set `policyEnforcementMode=always` to fully leverage Cilium’s advanced policy capabilities, especially for L7 filtering. The `kubeProxyReplacement=strict` setting is also important for performance and security, as it allows Cilium to handle service load balancing using eBPF.

```bash

# Add the Cilium Helm repository
helm repo add cilium https://helm.cilium.io/

# Update your Helm repositories
helm repo update

# Install Cilium with L7 proxy and policy enforcement enabled
helm install cilium cilium/cilium --version 1.15.5 \
  --namespace kube-system \
  --set ipam.mode=cluster-pool \
  --set ipv4.enabled=true \
  --set tunnel=vxlan \
  --set enableIPv4BIGTCP=true \
  --set autoDirectNodeRoutes=true \
  --set kubeProxyReplacement=strict \
  --set bpf.masquerade=true \
  --set l7Proxy=true \
  --set policyEnforcementMode=always \
  --set hubble.enabled=true \
  --set hubble.ui.enabled=true \
  --set hubble.relay.enabled=true \
  --wait

# Verify Cilium installation status
cilium status --wait
```

#### Explanation

The Helm command installs Cilium into the `kube-system` namespace. We’re setting several important flags:

- `ipam.mode=cluster-pool`: Uses a cluster-wide IPAM (IP Address Management) for pod IPs.
- `tunnel=vxlan`: Configures VXLAN tunneling for inter-node pod communication. Other options like Geneve or native routing are available depending on your environment. For enhanced security, you might explore [Cilium WireGuard Encryption](https://kubezilla.io/cilium-wireguard-encryption).
- `kubeProxyReplacement=strict`: Replaces `kube-proxy` functionality with eBPF, improving performance and reducing overhead.
- `l7Proxy=true`: Enables the Envoy proxy within Cilium, essential for L7 policy enforcement.
- `policyEnforcementMode=always`: Ensures that all network traffic is subject to policy enforcement. By default, Cilium operates in a “deny-all” mode once a `CiliumNetworkPolicy` is applied to a pod, meaning you must explicitly permit traffic.
- `hubble.enabled=true`, `hubble.ui.enabled=true`, `hubble.relay.enabled=true`: Enables Hubble, Cilium’s observability layer, which is invaluable for visualizing and debugging network flows and policy decisions. For more on eBPF observability, check out [eBPF Observability: Building Custom Metrics with Hubble](https://kubezilla.io/ebpf-observability-hubble).

#### Verify

Wait for all Cilium components to be ready. The `cilium status --wait` command will block until Cilium reports a healthy state.

```bash

cilium status --wait
```

```bash

Cluster: default
DaemonSet: cilium            Desired: 1, Ready: 1/1, Available: 1/1
Deployment: cilium-operator   Desired: 1, Ready: 1/1, Available: 1/1
Deployment: hubble-relay      Desired: 1, Ready: 1/1, Available: 1/1
Deployment: hubble-ui         Desired: 1, Ready: 1/1, Available: 1/1
Containers:  cilium         Running: 1
             cilium-operator Running: 1
             hubble-relay   Running: 1
             hubble-ui      Running: 1
Cluster Pods:  2/2 managed by Cilium
Image versions: cilium/cilium:v1.15.5 cilium/operator-generic:v1.15.5 cilium/hubble-relay:v1.15.5 cilium/hubble-ui:v0.13.0
All components are healthy!
```

### Step 2: Deploy Sample Applications

To demonstrate network policies, we’ll deploy a simple application consisting of a `client`, an `app` (backend), and a `database`. These will reside in a dedicated namespace.

```yaml

# traffic-test-app.yaml
---
apiVersion: v1
kind: Namespace
metadata:
  name: test-app
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: client
  namespace: test-app
  labels:
    app: client
spec:
  replicas: 1
  selector:
    matchLabels:
      app: client
  template:
    metadata:
      labels:
        app: client
    spec:
      containers:
      - name: client
        image: curlimages/curl:8.7.1
        command: ["sleep", "3600"]
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
  namespace: test-app
  labels:
    app: app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: app
  template:
    metadata:
      labels:
        app: app
    spec:
      containers:
      - name: app
        image: kennethreitz/httpbin
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: app-service
  namespace: test-app
spec:
  selector:
    app: app
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: database
  namespace: test-app
  labels:
    app: database
spec:
  replicas: 1
  selector:
    matchLabels:
      app: database
  template:
    metadata:
      labels:
        app: database
    spec:
      containers:
      - name: database
        image: postgres:16
        env:
        - name: POSTGRES_DB
          value: mydatabase
        - name: POSTGRES_USER
          value: user
        - name: POSTGRES_PASSWORD
          value: password
        ports:
        - containerPort: 5432
---
apiVersion: v1
kind: Service
metadata:
  name: database-service
  namespace: test-app
spec:
  selector:
    app: database
  ports:
    - protocol: TCP
      port: 5432
      targetPort: 5432
```

#### Explanation

This YAML defines:

- A `test-app` namespace to isolate our application.
- A `client` deployment using `curlimages/curl`, which we’ll use to initiate requests.
- An `app` deployment using `kennethreitz/httpbin`, a simple HTTP request and response service, exposed via `app-service`.
- A `database` deployment using `postgres`, exposed via `database-service`.

By default, with no Cilium policies applied (yet), all these pods can communicate freely within the `test-app` namespace.

#### Verify

Apply the resources and ensure all pods are running. Then, test connectivity between `client` and `app`.

```bash

kubectl apply -f traffic-test-app.yaml

# Wait for pods to be ready
kubectl wait --for=condition=ready pod -l app=client -n test-app --timeout=300s
kubectl wait --for=condition=ready pod -l app=app -n test-app --timeout=300s
kubectl wait --for=condition=ready pod -l app=database -n test-app --timeout=300s

# Get the client pod name
CLIENT_POD=$(kubectl get pod -l app=client -n test-app -o jsonpath='{.items[0].metadata.name}')

# Test connectivity to app-service
kubectl exec -ti "$CLIENT_POD" -n test-app -- curl -sv http://app-service.test-app/status/200
```

```bash

# Expected output (truncated for brevity), showing a successful HTTP 200 response:
*   Trying 10.X.Y.Z:80...
* Connected to app-service.test-app (10.X.Y.Z) port 80 (#0)
> GET /status/200 HTTP/1.1
> Host: app-service.test-app
> User-Agent: curl/8.7.1
> Accept: */*
>
< HTTP/1.1 200 OK
< Server: gunicorn/20.0.4
< Date: Thu, 01 Jan 1970 00:00:00 GMT
< Connection: close
< Content-Length: 0
<
* Closing connection 0
```

### Step 3: Implement Basic L3/L4 Cilium Network Policies

Now, let's start with basic L3/L4 policies. Remember that once a `CiliumNetworkPolicy` targets a pod, all ingress and egress traffic to/from that pod is denied by default, unless explicitly allowed by a policy. This "default deny" posture is a cornerstone of robust security.

```yaml

# cilium-l3-l4-policy.yaml
---
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: allow-client-to-app
  namespace: test-app
spec:
  endpointSelector:
    matchLabels:
      app: app # This policy applies to pods with label app: app
  ingress: # Define ingress rules for 'app' pods
  - fromEndpoints:
    - matchLabels:
        app: client # Allow ingress from pods with label app: client
    toPorts:
    - ports:
      - port: "80"
        protocol: TCP # Allow TCP traffic on port 80

---
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: allow-app-to-database
  namespace: test-app
spec:
  endpointSelector:
    matchLabels:
      app: app # This policy applies to pods with label app: app
  egress: # Define egress rules for 'app' pods
  - toEndpoints:
    - matchLabels:
        app: database # Allow egress to pods with label app: database
    toPorts:
    - ports:
      - port: "5432"
        protocol: TCP # Allow TCP traffic on port 5432

---
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: allow-all-egress-from-client # Client needs to talk to app, and potentially external services
  namespace: test-app
spec:
  endpointSelector:
    matchLabels:
      app: client
  egress:
  - {} # Allows all egress traffic. In a real scenario, you'd restrict this further.

---
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: allow-dns-from-all-pods
  namespace: test-app
spec:
  endpointSelector: {} # Applies to all pods in the namespace
  egress:
  - toPorts:
    - ports:
      - port: "53"
        protocol: UDP
      - port: "53"
        protocol: TCP
    toEntities:
    - "kube-dns" # Allow egress to Kubernetes DNS service
  - toFQDNs: # Alternative for external DNS servers
    - matchName: "8.8.8.8" # Example: Google DNS
    - matchName: "8.8.4.4"
    toPorts:
    - ports:
      - port: "53"
        protocol: UDP
      - port: "53"
        protocol: TCP
```

#### Explanation

We've defined four `CiliumNetworkPolicy` resources:

- `allow-client-to-app`: This policy targets pods with `app: app`. It explicitly allows ingress traffic on TCP port 80 from pods labeled `app: client` within the same namespace.
- `allow-app-to-database`: This policy targets pods with `app: app`. It explicitly allows egress traffic on TCP port 5432 to pods labeled `app: database`.
- `allow-all-egress-from-client`: This policy targets pods with `app: client`. The `egress: - {}` rule is a wildcard that allows all egress traffic. This is often used as a temporary measure or for pods that truly need broad outbound access (e.g., an external HTTP client), but ideally, you'd narrow this scope in production.
- `allow-dns-from-all-pods`: This crucial policy allows all pods in the namespace to perform DNS lookups. Without it, pods might fail to resolve service names or external hostnames. It uses `toEntities: ["kube-dns"]` to target the Kubernetes DNS service, which is a built-in Cilium selector for common Kubernetes components. We also included `toFQDNs` for external DNS servers, demonstrating another powerful Cilium feature.

Notice the use of `endpointSelector` to define which pods a policy applies to, and `fromEndpoints`/`toEndpoints` to define the source/destination of allowed traffic based on labels. Cilium also supports `fromCIDR`/`toCIDR` for IP range filtering, and `fromEntities`/`toEntities` for predefined entities like `host`, `world`, `init`, `kube-apiserver`, etc.

#### Verify

Apply the policies and re-test connectivity. The `client` should still be able to reach `app-service`, and the `app` pod should be able to reach the `database-service` (though we didn't add a database client to the app, the policy is in place).

```bash

kubectl apply -f cilium-l3-l4-policy.yaml

# Get the client pod name again (it might have restarted)
CLIENT_POD=$(kubectl get pod -l app=client -n test-app -o jsonpath='{.items[0].metadata.name}')

# Test connectivity from client to app-service (should succeed)
kubectl exec -ti "$CLIENT_POD" -n test-app -- curl -sv http://app-service.test-app/status/200

# Test connectivity from client to database-service (should fail, as no policy allows it)
kubectl exec -ti "$CLIENT_POD" -n test-app -- curl -sv http://database-service.test-app:5432
```

```bash

# Expected output for client to app-service (success - truncated):
< HTTP/1.1 200 OK
...

# Expected output for client to database-service (failure - truncated):
*   Trying 10.X.Y.Z:5432...
* TCP_NODELAY set
* connect to 10.X.Y.Z port 5432 failed: Connection refused
* Failed to connect to database-service.test-app port 5432 after 0 ms: Connection refused
* Closing connection 0
curl: (7) Failed to connect to database-service.test-app port 5432 after 0 ms: Connection refused
command terminated with exit code 7
```

The failure to connect to the database from the client confirms our policies are working: the `client` pod has no explicit policy allowing it to connect to the `database` pod on port 5432, so the connection is denied by Cilium.

### Step 4: Implement Advanced L7 Cilium Network Policies (HTTP)

Now for the real power of Cilium: L7 filtering. We'll restrict the `client` pod's access to the `app-service` to specific HTTP paths and methods.

```yaml

# cilium-l7-http-policy.yaml
---
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: restrict-app-http-access
  namespace: test-app
spec:
  endpointSelector:
    matchLabels:
      app: app # This policy applies to pods with label app: app
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: client # Allow ingress from pods with label app: client
    toPorts:
    - ports:
      - port: "80"
        protocol: TCP
      rules:
        http: # Define HTTP rules
        - method: "GET"
          path: "/status/200" # Allow only GET requests to /status/200
        - method: "POST"
          path: "/post" # Allow only POST requests to /post
        - method: "GET"
          path: "/get" # Allow only GET requests to /get
```

#### Explanation

This `CiliumNetworkPolicy`:

- Targets `app: app` pods.
- Allows ingress from `app: client` pods on TCP port 80.
- Crucially, it adds a `rules.http` section. This tells Cilium's Envoy proxy to inspect the HTTP traffic.
- It explicitly permits only `GET /status/200`, `POST /post`, and `GET /get` requests. Any other HTTP request to the `app-service` will be denied, even if it's on port 80 from the `client` pod.

This level of control is invaluable for microservices, allowing you to enforce API contracts directly at the network layer. For more advanced traffic management, you might explore the [Kubernetes Gateway API](https://kubezilla.io/kubernetes-gateway-api-guide), which Cilium also supports.

#### Verify

Apply the L7 policy and test various HTTP requests from the `client` pod.

```bash

# Apply the L7 policy
kubectl apply -f cilium-l7-http-policy.yaml

# Get the client pod name
CLIENT_POD=$(kubectl get pod -l app=client -n test-app -o jsonpath='{.items[0].metadata.name}')

echo "--- Testing allowed GET /status/200 ---"
kubectl exec -ti "$CLIENT_POD" -n test-app -- curl -sv http://app-service.test-app/status/200

echo "--- Testing allowed GET /get ---"
kubectl exec -ti "$CLIENT_POD" -n test-app -- curl -sv http://app-service.test-app/get

echo "--- Testing allowed POST /post ---"
kubectl exec -ti "$CLIENT_POD" -n test-app -- curl -sv -X POST -d "data=test" http://app-service.test-app/post

echo "--- Testing denied GET /anything-else ---"
kubectl exec -ti "$CLIENT_POD" -n test-app -- curl -sv http://app-service.test-app/anything-else

echo "--- Testing denied GET /status/404 ---"
kubectl exec -ti "$CLIENT_POD" -n test-app -- curl -sv http://app-service.test-app/status/404
```

```bash

# Expected output:

# --- Testing allowed GET /status/200 --- (Success - truncated)
< HTTP/1.1 200 OK
...

# --- Testing allowed GET /get --- (Success - truncated)
< HTTP/1.1 200 OK
...

# --- Testing allowed POST /post --- (Success - truncated)
< HTTP/1.1 200 OK
...

# --- Testing denied GET /anything-else --- (Failure - truncated)
*   Trying 10.X.Y.Z:80...
* Connected to app-service.test-app (10.X.Y.Z) port 80 (#0)
> GET /anything-else HTTP/1.1
> Host: app-service.test-app
> User-Agent: curl/8.7.1
> Accept: */*
>
* Recv failure: Connection reset by peer
* Closing connection 0
curl: (56) Recv failure: Connection reset by peer
command terminated with exit code 56

# --- Testing denied GET /status/404 --- (Failure - truncated)
*   Trying 10.X.Y.Z:80...
* Connected to app-service.test-app (10.X.Y.Z) port 80 (#0)
> GET /status/404 HTTP/1.1
> Host: app-service.test-app
> User-Agent: curl/8.7.1
> Accept: */*
>
* Recv failure: Connection reset by peer
* Closing connection 0
curl: (56) Recv failure: Connection reset by peer
command terminated with exit code 56
```

The successful requests confirm the allowed paths, while the "Connection reset by peer" errors for denied paths demonstrate that Cilium's L7 policy is actively blocking unauthorized HTTP traffic. This is a significant security enhancement over traditional L3/L4 firewalls.

### Step 5: Using Cilium Network Policies for External Access (CIDR/FQDN)

Cilium policies can also control access to external services or specific IP ranges using `toCIDR` and `toFQDNs`. Let's create a policy that allows the `app` pod to make HTTP requests to a specific external domain, for instance, `liora.io`.

```yaml

# cilium-external-access-policy.yaml
---
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: allow-app-to-example-com
  namespace: test-app
spec:
  endpointSelector:
    matchLabels:
      app: app # This policy applies to pods with label app: app
  egress:
  - toFQDNs:
    - matchName: "liora.io" # Allow egress to liora.io
    toPorts:
    - ports:
      - port: "80"
        protocol: TCP
      - port: "443"
        protocol: TCP
    rules:
      http: # Optionally, apply L7 rules even for external traffic if it's HTTP/HTTPS
      - method: "GET"
        path: "/"
```

#### Explanation

This policy allows `app` pods to make HTTP/HTTPS requests to `liora.io`. The `toFQDNs` section uses DNS resolution to identify the target IPs. This is highly dynamic and secure, as you don't need to hardcode IP addresses that might change. The optional `rules.http` section demonstrates that L7 policies can also be applied to external HTTP traffic.

For scenarios requiring access to specific IP blocks, you would use `toCIDR`:

```yaml

# Example: Allow app to a specific external CIDR block
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: allow-app-to-external-cidr
  namespace: test-app
spec:
  endpointSelector:
    matchLabels:
      app: app
  egress:
  - toCIDR:
    - "203.0.113.0/24" # Example CIDR block
    toPorts:
    - ports:
      - port: "8080"
        protocol: TCP
```

#### Verify

Apply the FQDN policy and test connectivity from the `app` pod to `liora.io`. Note: We'll use the `client` pod to simulate the `app` pod's behavior for testing convenience, as the `app` pod itself doesn't have `curl`.

```bash

# Apply the FQDN policy
kubectl apply -f cilium-external-access-policy.yaml

# Get the client pod name
CLIENT_POD=$(kubectl get pod -l app=client -n test-app -o jsonpath='{.items[0].metadata.name}')

echo "--- Testing allowed egress to liora.io from client (simulating app) ---"
kubectl exec -ti "$CLIENT_POD" -n test-app -- curl -sv http://liora.io

echo "--- Testing denied egress to non-allowed external domain (e.g., google.com) ---"
kubectl exec -ti "$CLIENT_POD" -n test-app -- curl -sv http://google.com
```

```bash

# Expected output for liora.io (Success - truncated):
*   Trying 93.184.216.34:80...
* Connected to liora.io (93.184.216.34) port 80 (#0)
> GET / HTTP/1.1
> Host: liora.io
> User-Agent: curl/8.7.1
> Accept: */*
>
< HTTP/1.1 200 OK
...

# Expected output for google.com (Failure - truncated):
*   Trying 142.250.190.132:80...
* TCP_NODELAY set
* connect to 142.250.190.132 port 80 failed: Connection refused
* Failed to connect to google.com port 80 after 0 ms: Connection refused
* Closing connection 0
curl: (7) Failed to connect to google.com port 80 after 0 ms: Connection refused
command terminated with exit code 7
```

The successful connection to `liora.io` and the failure to `google.com` (which was not explicitly allowed by a `toFQDNs` rule) confirms that Cilium's FQDN-based policies are working as expected.

### Step 6: Monitoring and Debugging Cilium Policies with Hubble

Hubble, Cilium's observability platform, is incredibly useful for understanding how policies are enforced and for debugging connectivity issues. Since we enabled Hubble during installation, we can now use it.

```bash

# Port-forward Hubble UI
kubectl port-forward -n kube-system svc/hubble-ui 8080:80

# In a new terminal, open Hubble UI in your browser:
# http://localhost:8080

# Monitor live network flows and policy decisions
cilium monitor --type policy --verbose
```

#### Explanation

`cilium monitor --type policy --verbose` provides a real-time stream of network events and policy decisions. You'll see entries like `Policy denied (L7)` or `Policy allowed (L3)`, along with detailed information about the source, destination, and specific policy rule that was matched. This is indispensable for validating your policies and troubleshooting unexpected behavior.

#### Verify

While `cilium monitor` is running, re-run some of the allowed and denied curl commands from previous steps. Observe the output in the monitor window:

- Allowed requests should show `Policy allowed` entries, possibly with L7 details.
- Denied requests should clearly show `Policy denied (L7)` or `Policy denied (L3)`.

## Production Considerations

- **Default Deny:** Always design your policies with a "default deny" mindset. Once a `CiliumNetworkPolicy` applies to an endpoint, all traffic is denied unless explicitly permitted. This is a strong security posture.
- **Granularity vs. Complexity:** While L7 policies offer extreme granularity, balance this with the complexity of managing too many fine-grained rules. Group related services and their communication patterns

