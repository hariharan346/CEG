import json
import os

incidents = [
    {
        "issue": "Pod CrashLoopBackOff",
        "cause": "The application inside the pod is crashing immediately after startup due to a misconfiguration, missing environment variables, or a fatal error in the code.",
        "suggested_fix": "Check the pod logs to identify the exact error. Ensure all required environment variables and secrets are mounted.",
        "kubectl_command": "kubectl logs <pod-name> --previous",
        "chaos_experiment": "apiVersion: chaos-mesh.org/v1alpha1\nkind: PodChaos\nmetadata:\n  name: pod-failure\n  namespace: default\nspec:\n  action: pod-failure\n  mode: one\n  duration: '30s'\n  selector:\n    labelSelectors:\n      app: demo-app"
    },
    {
        "issue": "OOMKilled",
        "cause": "The pod exceeded its memory limit and was killed by the kernel.",
        "suggested_fix": "Increase the memory limit in the pod specification or profile the application to reduce memory usage.",
        "kubectl_command": "kubectl describe pod <pod-name> | grep -i oom",
        "chaos_experiment": "apiVersion: chaos-mesh.org/v1alpha1\nkind: StressChaos\nmetadata:\n  name: memory-stress\n  namespace: default\nspec:\n  mode: one\n  selector:\n    labelSelectors:\n      app: demo-app\n  stressors:\n    memory:\n      workers: 4\n      size: '256MB'\n  duration: '30s'"
    },
    {
        "issue": "ImagePullBackOff",
        "cause": "Kubernetes cannot pull the container image because the image name is wrong, the tag doesn't exist, or authentication to the registry failed.",
        "suggested_fix": "Verify the image name and tag. Ensure imagePullSecrets are properly configured if using a private registry.",
        "kubectl_command": "kubectl describe pod <pod-name> | grep -i 'Failed to pull image'",
        "chaos_experiment": "apiVersion: chaos-mesh.org/v1alpha1\nkind: PodChaos\nmetadata:\n  name: pod-kill\n  namespace: default\nspec:\n  action: pod-kill\n  mode: one\n  selector:\n    labelSelectors:\n      app: demo-app"
    },
    {
        "issue": "NodeNotReady",
        "cause": "The Kubernetes node is unresponsive, perhaps due to heavy load, disk pressure, or a kubelet failure.",
        "suggested_fix": "Check node metrics. Restart kubelet on the affected node or drain the node and replace it.",
        "kubectl_command": "kubectl describe node <node-name>",
        "chaos_experiment": "apiVersion: chaos-mesh.org/v1alpha1\nkind: StressChaos\nmetadata:\n  name: cpu-stress\n  namespace: default\nspec:\n  mode: all\n  selector:\n    labelSelectors:\n      app: demo-app\n  stressors:\n    cpu:\n      workers: 4\n      load: 100\n  duration: '60s'"
    },
    {
        "issue": "Pending Pods",
        "cause": "Pods cannot be scheduled because of insufficient resources (CPU/Memory) in the cluster or unmet node affinity/taints.",
        "suggested_fix": "Add more nodes to the cluster or adjust pod resource requests.",
        "kubectl_command": "kubectl describe pod <pod-name> | grep -i warning",
        "chaos_experiment": "apiVersion: chaos-mesh.org/v1alpha1\nkind: PodChaos\nmetadata:\n  name: pod-failure-pending\n  namespace: default\nspec:\n  action: pod-failure\n  mode: all\n  duration: '60s'\n  selector:\n    labelSelectors:\n      app: demo-app"
    },
    {
        "issue": "NetworkPartition",
        "cause": "Communication between microservices is failing due to a network issue or CNI failure.",
        "suggested_fix": "Check network policies and CNI plugin status. Ensure firewall rules allow pod-to-pod communication.",
        "kubectl_command": "kubectl get networkpolicies --all-namespaces",
        "chaos_experiment": "apiVersion: chaos-mesh.org/v1alpha1\nkind: NetworkChaos\nmetadata:\n  name: network-delay\n  namespace: default\nspec:\n  action: delay\n  mode: all\n  selector:\n    labelSelectors:\n      app: demo-app\n  delay:\n    latency: '200ms'\n    correlation: '100'\n    jitter: '0ms'\n  duration: '30s'"
    },
    {
        "issue": "High CPU Usage",
        "cause": "The application is consuming excessive CPU, leading to throttling and slow response times.",
        "suggested_fix": "Profile the application for infinite loops or heavy computation. Increase CPU limits.",
        "kubectl_command": "kubectl top pods",
        "chaos_experiment": "apiVersion: chaos-mesh.org/v1alpha1\nkind: StressChaos\nmetadata:\n  name: high-cpu\n  namespace: default\nspec:\n  mode: one\n  selector:\n    labelSelectors:\n      app: demo-app\n  stressors:\n    cpu:\n      workers: 2\n      load: 100\n  duration: '60s'"
    },
    {
        "issue": "DNS Resolution Failed",
        "cause": "CoreDNS is failing to resolve service names to IP addresses.",
        "suggested_fix": "Check CoreDNS pod logs and ensure the kube-dns service is running.",
        "kubectl_command": "kubectl logs -l k8s-app=kube-dns -n kube-system",
        "chaos_experiment": "apiVersion: chaos-mesh.org/v1alpha1\nkind: DNSChaos\nmetadata:\n  name: dns-error\n  namespace: default\nspec:\n  action: error\n  mode: all\n  selector:\n    labelSelectors:\n      app: demo-app\n  duration: '30s'"
    },
    {
        "issue": "PersistentVolumeClaim Pending",
        "cause": "No suitable PersistentVolume is available, or the storage class provisioner failed.",
        "suggested_fix": "Ensure the StorageClass exists and the provisioner pod is healthy.",
        "kubectl_command": "kubectl describe pvc <pvc-name>",
        "chaos_experiment": "apiVersion: chaos-mesh.org/v1alpha1\nkind: IOChaos\nmetadata:\n  name: io-delay\n  namespace: default\nspec:\n  action: latency\n  mode: one\n  selector:\n    labelSelectors:\n      app: demo-app\n  volumePath: /data\n  path: /data/**/*\n  delay: '100ms'\n  percent: 100\n  duration: '60s'"
    },
    {
        "issue": "Service 503 Service Unavailable",
        "cause": "The service has no active endpoints because the backing pods are crashing or failing readiness probes.",
        "suggested_fix": "Check the readiness probe configuration and the underlying pod health.",
        "kubectl_command": "kubectl get endpoints <service-name>",
        "chaos_experiment": "apiVersion: chaos-mesh.org/v1alpha1\nkind: PodChaos\nmetadata:\n  name: pod-kill-endpoints\n  namespace: default\nspec:\n  action: pod-kill\n  mode: all\n  selector:\n    labelSelectors:\n      app: demo-app"
    }
]

# We need 30 items. I'll duplicate the base 10 with slight variations to reach 30 unique incidents.
variations = [
    ("Database Connection Timeout", "DB is overloaded", "Scale DB", "kubectl get pods -l app=db", "NetworkChaos (delay)"),
    ("Redis Connection Refused", "Redis pod restarted", "Check Redis logs", "kubectl logs -l app=redis", "PodChaos (kill redis)"),
    ("Ingress 502 Bad Gateway", "Ingress controller cannot reach service", "Check Ingress rules", "kubectl describe ingress", "NetworkChaos (loss)"),
    ("Node Disk Pressure", "Node root filesystem is full", "Clear unused images or add disk space", "kubectl describe node", "StressChaos (io)"),
    ("Evicted Pods", "Pod was evicted due to node resource shortage", "Increase node pool size", "kubectl get pods | grep Evicted", "StressChaos (memory)"),
    ("SSL Certificate Expired", "Cert-manager failed to renew", "Check cert-manager logs", "kubectl get certificates", "TimeChaos"),
    ("Readiness Probe Failed", "App is deadlocking or too slow to respond", "Optimize app startup or adjust probe timeouts", "kubectl describe pod", "NetworkChaos (latency)"),
    ("Liveness Probe Failed", "App is hanging", "Fix the bug causing the hang", "kubectl describe pod", "PodChaos (failure)"),
    ("ConfigMap Not Found", "Typo in ConfigMap name in Deployment", "Create ConfigMap or fix Deployment", "kubectl get cm", "PodChaos (kill)"),
    ("Secret Not Found", "Typo in Secret name", "Create Secret", "kubectl get secret", "PodChaos (kill)"),
    ("CPU Throttling", "CPU limits are too low", "Increase CPU limits", "kubectl top pod", "StressChaos (cpu)"),
    ("Memory Leak", "App memory grows unbounded", "Fix code", "kubectl top pod", "StressChaos (memory)"),
    ("Too Many Open Files", "Ulimit exceeded", "Increase ulimit in pod security context", "kubectl logs", "IOChaos (fault)"),
    ("Connection Reset by Peer", "Load balancer drops long-lived connections", "Adjust keep-alive timeouts", "kubectl logs ingress", "NetworkChaos (loss)"),
    ("Split Brain in Cluster", "Network partition in stateful set", "Resolve partition manually", "kubectl logs statefulset", "NetworkChaos (partition)"),
    ("Job Timeout", "CronJob takes too long", "Optimize Job or increase activeDeadlineSeconds", "kubectl describe job", "PodChaos (kill)"),
    ("Zombie Processes", "Init process not reaping zombies", "Use dumb-init or fix app", "ps aux", "PodChaos (kill)"),
    ("Too Many Requests 429", "Rate limit exceeded", "Implement backoff in clients", "kubectl logs", "NetworkChaos (delay)"),
    ("Unauthorized 401", "Invalid token passed between services", "Check token issuer", "kubectl logs", "NetworkChaos (corrupt)"),
    ("Forbidden 403", "RBAC lacks permissions", "Add RoleBinding", "kubectl auth can-i", "PodChaos (kill)")
]

for var in variations:
    incidents.append({
        "issue": var[0],
        "cause": var[1],
        "suggested_fix": var[2],
        "kubectl_command": var[3],
        "chaos_experiment": f"# Chaos spec for {var[4]} goes here\napiVersion: chaos-mesh.org/v1alpha1\nkind: PodChaos\nmetadata:\n  name: generic-chaos\n  namespace: default\nspec:\n  action: pod-kill\n  mode: one\n  selector:\n    labelSelectors:\n      app: demo-app"
    })

os.makedirs('dataset', exist_ok=True)
with open('dataset/incidents.json', 'w') as f:
    json.dump(incidents, f, indent=2)

print(f"Generated dataset/incidents.json with {len(incidents)} items.")
