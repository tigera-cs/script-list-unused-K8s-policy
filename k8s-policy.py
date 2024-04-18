#!/usr/bin/env python3
from kubernetes import client, config

def list_unmatched_network_policies():
    # Load the kubeconfig file
    config.load_kube_config()

    # Create API clients
    v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()
    batch_v1 = client.BatchV1Api()
    networking_v1 = client.NetworkingV1Api()

    print("Analyzing Kubernetes network policies...")

    # Open a file to write the unmatched policies
    with open('kubernetes-unused-policies.txt', 'w') as file:
        # Print the header in the file
        file.write(f"NAMESPACE     NAME OF POLICY          ENDPOINTS-ATTACHED    RESOURCES-IN-THE-NAMESPACE\n")

        # List all network policies
        network_policies = networking_v1.list_network_policy_for_all_namespaces()

        for np in network_policies.items:
            namespace = np.metadata.namespace
            policy_name = np.metadata.name
            selector = ','.join([f'{k}={v}' for k, v in np.spec.pod_selector.match_labels.items()]) if np.spec.pod_selector.match_labels else None

            pods = v1.list_namespaced_pod(namespace, label_selector=selector) if selector else v1.list_namespaced_pod(namespace)
            endpoints_attached = len(pods.items)

            # Check for any resource in the namespace
            deployments = apps_v1.list_namespaced_deployment(namespace)
            daemonsets = apps_v1.list_namespaced_daemon_set(namespace)
            statefulsets = apps_v1.list_namespaced_stateful_set(namespace)
            jobs = batch_v1.list_namespaced_job(namespace)
            replica_sets = apps_v1.list_namespaced_replica_set(namespace)

            total_resources = sum([
                len(deployments.items),
                len(daemonsets.items),
                len(statefulsets.items),
                len(jobs.items),
                len(replica_sets.items)
            ])

            # Check for existence of any resources in the namespace
            if total_resources == 0 and endpoints_attached == 0:
                file.write(f"{namespace: <13} {policy_name: <25} {endpoints_attached: <20} {total_resources}\n")

    print("\nThe output has been written to kubernetes-unused-policies.txt. Please review it before any clean-up action.")

if __name__ == "__main__":
    list_unmatched_network_policies()
