# Kubernetes Troubleshooting Scenarios

Welcome to the **Kubernetes Troubleshooting Scenarios Simulator**! This repository contains **35 real-world Kubernetes issues** that you can simulate, analyze, and resolve. Whether you're a beginner or an experienced Kubernetes professional, this project will help you gain hands-on troubleshooting experience in Kubernetes environments.

## Why This Repository?

- **35 real-world scenarios**: Each scenario is designed to reflect actual Kubernetes issues you may encounter in production environments.
- **Step-by-step troubleshooting**: Follow clear instructions for simulating issues, investigating problems, and applying solutions.
- **Hands-on practice**: Learn by doing! Build your troubleshooting skills in a real Kubernetes environment.
- **Docker integration**: Learn how to build and run Docker containers for each scenario as needed.

---

## Features

- **35 Kubernetes troubleshooting scenarios** covering networking, storage, security, probes, scheduling, resources, and more.
- **No custom Docker images needed** — all scenarios use standard public images (`busybox`, `nginx:alpine`, `polinux/stress`).
- **Observable failures** — 30 scenarios produce clear failure states (Pending, CrashLoopBackOff, OOMKilled, Error) visible via `kubectl get pods`.
- **Interactive scenario runner** (`manage-scenarios.sh`) to simulate, investigate, and fix issues step by step.
- **Practical solutions** and explanations to help you understand the root causes of issues.

---

## Getting Started

### Prerequisites

1. **Kubernetes Cluster**:
   - Ensure you have access to a Kubernetes cluster. You can use Minikube, Docker Desktop, or a cloud-managed service like AWS EKS, GKE, or AKS.

2. **Install kubectl**:
   - `kubectl` is the Kubernetes command-line tool that you'll use to interact with your cluster.
   - Download and install it from the [official Kubernetes site](https://kubernetes.io/docs/tasks/tools/install-kubectl/).
   - To verify installation:
     ```bash
     kubectl version --client
     ```

3. **Install Docker**:
   - Install Docker to build images locally or on your preferred CI/CD pipeline.
   - Download Docker from the [official Docker site](https://www.docker.com/products/docker-desktop).

4. **Clone the Repository**:
   - Clone the repository to your local machine:
     ```bash
     git clone https://github.com/vellankikoti/troubleshoot-kubernetes-like-a-pro.git
     cd troubleshoot-kubernetes-like-a-pro
     ```

---

## Running the Scenarios

### Step 1: Make the Script Executable

In the root directory of the repository, you will find a script to help manage the scenarios:
```bash
chmod +x manage-scenarios.sh
```

### Step 2: Run the Script

Start the scenario management script:
```bash
./manage-scenarios.sh
```

### Step 3: Choose a Scenario

The script will display a list of 35 scenarios. Each scenario corresponds to a real-world issue in Kubernetes. Enter the scenario number to simulate and resolve the issue.

For example, enter `1` to simulate the "Affinity Rules Violation."

### Step 4: Simulate the Issue

The script will apply the `issue.yaml` file to simulate the problem in your Kubernetes cluster. You can inspect the issue with:
```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

### Step 5: Apply the Fix

After analyzing the issue, the script will guide you to apply the corresponding `fix.yaml` file to resolve the issue:
```bash
kubectl apply -f fix.yaml
```

Verify that the issue is resolved by checking the pod's status:
```bash
kubectl get pods
```

---

## Folder Structure

```
troubleshoot-kubernetes-like-a-pro/
├── scenarios/
│   ├── affinity-rules-violation/
│   │   ├── description.md    # Explains the issue, causes, and fix
│   │   ├── issue.yaml        # Creates the broken state
│   │   └── fix.yaml          # Resolves the issue
│   ├── crashloopbackoff/
│   ├── dns-resolution-failure/
│   └── ... (35 scenarios)
├── docs/
│   ├── pod-lifecycle.md
│   └── troubleshooting-guide.md
├── scripts/
│   └── manage-scenarios.sh
├── manage-scenarios.sh       # Interactive scenario runner
└── README.md
```

- **scenarios/**: Contains 35 scenario folders, each with `issue.yaml`, `fix.yaml`, and `description.md`.
- **docs/**: Supplementary guides on pod lifecycle and troubleshooting.
- **scripts/**: Contains the scenario management script.

---

## Available Scenarios

The repository includes the following 35 Kubernetes troubleshooting scenarios:

| # | Scenario | Failure Type | Observable State |
|---|----------|-------------|-----------------|
| 1 | **Affinity Rules Violation** | Scheduling | Pod Pending |
| 2 | **CGroup Issues** | Resource / OOM | OOMKilled / CrashLoopBackOff |
| 3 | **Cluster Autoscaler Issues** | Scheduling | Pods Pending (100 replicas) |
| 4 | **Container Runtime (CRI) Errors** | Runtime | RuntimeClass not found |
| 5 | **Crash Due to Insufficient Disk Space** | Storage | Pod Evicted |
| 6 | **CrashLoopBackOff** | Application | CrashLoopBackOff |
| 7 | **Disk IO Errors** | Storage | Container Error |
| 8 | **DNS Resolution Failure** | Networking | DNS timeout (pod runs but DNS fails) |
| 9 | **Failed Resource Limits** | Resource / OOM | OOMKilled / CrashLoopBackOff |
| 10 | **File Permissions on Mounted Volumes** | Storage / Security | Read-only filesystem error |
| 11 | **Firewall Restriction** | Networking | Egress blocked by NetworkPolicy |
| 12 | **Image Pull Backoff** | Image | ImagePullBackOff |
| 13 | **Image Pull Error** | Image | ErrImagePull |
| 14 | **Ingress Configuration Issue** | Networking | Misconfigured Ingress |
| 15 | **Insufficient Resources** | Scheduling | Pod Pending |
| 16 | **Liveness Probe Failure** | Probes | CrashLoopBackOff (probe fails) |
| 17 | **Liveness & Readiness Failure** | Probes | CrashLoopBackOff + Not Ready |
| 18 | **LoadBalancer Service Misconfiguration** | Networking | Service targets wrong selector |
| 19 | **Network Connectivity Issues** | Networking | Egress blocked by NetworkPolicy |
| 20 | **Node Affinity Issue** | Scheduling | Pod Pending |
| 21 | **OOM Killed** | Resource / OOM | OOMKilled / CrashLoopBackOff |
| 22 | **Outdated Kubernetes Version** | Best Practice | Running (educational) |
| 23 | **Persistent Volume Claim Issues** | Storage | Pod Pending (PVC unbound) |
| 24 | **PID Namespace Collision** | Security | Running with hostPID (security risk) |
| 25 | **Pod Disruption Budget Violations** | Availability | PDB blocks disruption |
| 26 | **Port Binding Issues** | Networking | Port conflict |
| 27 | **Readiness Probe Failure** | Probes | Running but Not Ready (0/1) |
| 28 | **Resource Requests & Limits Mismatch** | Resource | API rejection (limit < request) |
| 29 | **Security Context Issues** | Best Practice | Running as root (educational) |
| 30 | **SELinux/AppArmor Policy Violation** | Best Practice | Running (educational) |
| 31 | **Service Account Permissions Issue** | RBAC | Pod creation fails (SA not found) |
| 32 | **Service Port Mismatch** | Networking | Service port mismatch |
| 33 | **Taints and Tolerations Mismatch** | Scheduling | Pod Pending |
| 34 | **Volume Mount Issue** | Storage | API rejection (volume not defined) |
| 35 | **Wrong Container Command** | Application | RunContainerError |

### Scenario Categories

- **Hard Failures (30 scenarios):** These produce a clear, observable failure state (Pending, CrashLoopBackOff, OOMKilled, Error, etc.) that you can diagnose with `kubectl get pods`, `kubectl describe`, and `kubectl logs`.

- **Best Practice / Educational (3 scenarios):** Scenarios #22 (Outdated K8s Version), #29 (Security Context), and #30 (SELinux/AppArmor) are configuration best-practice demos. Both the issue and fix pods will show as Running — the learning is in understanding the security implications of the configuration difference.

- **CNI-Dependent (2 scenarios):** Scenarios #11 (Firewall Restriction) and #19 (Network Connectivity) use Kubernetes NetworkPolicy to simulate blocked traffic. These require a CNI plugin that supports NetworkPolicy enforcement (e.g., **Calico**, **Cilium**, **Weave Net**). They will not demonstrate the issue on clusters using basic flannel or Docker Desktop’s default CNI.

---

## Troubleshooting Tips

- Always check the logs and describe the pod to identify the issue:
  ```bash
  kubectl logs <pod-name>
  kubectl describe pod <pod-name>
  ```

- If a fix doesn’t resolve the issue, verify cluster configurations and try reapplying the scenario.

- For NetworkPolicy scenarios (#11, #19), ensure your cluster has a CNI that supports NetworkPolicy (e.g., Calico, Cilium).

---

## Contributing

Contributions are welcome! Feel free to:
- **Add new scenarios**: If you have an interesting or challenging Kubernetes issue, contribute by adding it to this repo.
- **Improve existing scenarios**: Fix bugs, improve documentation, or suggest enhancements.

To contribute, please submit a pull request with your changes.

---

## License

This project is licensed under the MIT License.

---

## Special Thanks

This project is maintained by [Koti](https://www.linkedin.com/in/vellankikoti/). Thank you for exploring the Kubernetes Troubleshooting Scenarios Simulator!

---

### 🚀 Enjoy learning Kubernetes troubleshooting!
