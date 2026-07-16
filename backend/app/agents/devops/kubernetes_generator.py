"""Kubernetes manifest generator for application deployment."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any

import yaml

from app.core.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class K8sResourceType(enum.Enum):
    """Supported Kubernetes resource types for manifest generation."""

    DEPLOYMENT = "Deployment"
    SERVICE = "Service"
    INGRESS = "Ingress"
    SECRET = "Secret"
    CONFIGMAP = "ConfigMap"
    PVC = "PersistentVolumeClaim"
    HPA = "HorizontalPodAutoscaler"
    NETWORK_POLICY = "NetworkPolicy"


class ServiceType(enum.Enum):
    """Kubernetes service types."""

    CLUSTER_IP = "ClusterIP"
    NODE_PORT = "NodePort"
    LOAD_BALANCER = "LoadBalancer"


class IngressClass(enum.Enum):
    """Common ingress controller classes."""

    NGINX = "nginx"
    TRAEFIK = "traefik"
    HAPROXY = "haproxy"


class VolumeAccessMode(enum.Enum):
    """PersistentVolumeClaim access modes."""

    READ_WRITE_ONCE = "ReadWriteOnce"
    READ_ONLY_MANY = "ReadOnlyMany"
    READ_WRITE_MANY = "ReadWriteMany"


# ---------------------------------------------------------------------------
# Dataclasses – configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ResourceRequirements:
    """CPU and memory resource requirements for a container."""

    cpu_request: str = "100m"
    cpu_limit: str = "500m"
    memory_request: str = "128Mi"
    memory_limit: str = "512Mi"


@dataclass(frozen=True)
class HealthProbe:
    """Configuration for liveness, readiness, or startup probes."""

    path: str = "/health"
    port: int = 8000
    initial_delay_seconds: int = 15
    period_seconds: int = 20
    timeout_seconds: int = 5
    failure_threshold: int = 3
    success_threshold: int = 1


@dataclass(frozen=True)
class SecurityContext:
    """Container security context configuration."""

    run_as_non_root: bool = True
    run_as_user: int = 1000
    run_as_group: int = 1000
    fs_group: int = 1000
    read_only_root_filesystem: bool = True
    allow_privilege_escalation: bool = False
    capabilities_drop: list[str] = field(default_factory=lambda: ["ALL"])


@dataclass(frozen=True)
class HPAConfig:
    """HorizontalPodAutoscaler configuration."""

    min_replicas: int = 2
    max_replicas: int = 10
    cpu_target_percentage: int = 70
    memory_target_percentage: int = 80


@dataclass(frozen=True)
class NetworkPolicyConfig:
    """Network policy configuration for ingress/egress rules."""

    allow_ingress_from: list[str] = field(default_factory=lambda: ["kube-system"])
    allow_egress_to: list[str] = field(default_factory=list)
    deny_all_default: bool = True


@dataclass
class K8sResource:
    """A single Kubernetes resource manifest."""

    resource_type: K8sResourceType
    name: str
    namespace: str
    content: str
    labels: dict[str, str] = field(default_factory=dict)


@dataclass
class K8sManifestResult:
    """Result of Kubernetes manifest generation."""

    resources: list[K8sResource]
    namespace: str
    total_resources: int
    notes: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Default values
# ---------------------------------------------------------------------------

_DEFAULT_NAMESPACE = "default"
_APP_LABEL = "app.kubernetes.io/name"
_APP_VERSION_LABEL = "app.kubernetes.io/version"
_APP_MANAGED_BY_LABEL = "app.kubernetes.io/managed-by"
_APP_COMPONENT_LABEL = "app.kubernetes.io/component"


# ---------------------------------------------------------------------------
# KubernetesGenerator
# ---------------------------------------------------------------------------


class KubernetesGenerator:
    """Generates production-ready Kubernetes manifests for application deployment."""

    def __init__(self) -> None:
        self._resource_defaults = ResourceRequirements()
        self._security_defaults = SecurityContext()
        self._hpa_defaults = HPAConfig()
        self._health_defaults = HealthProbe()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate(
        self,
        analysis: dict[str, Any],
        resources: list[K8sResourceType] | None = None,
    ) -> K8sManifestResult:
        """Generate Kubernetes manifests based on project analysis.

        Args:
            analysis: Project analysis dictionary containing detected components,
                      project type, ports, environment variables, etc.
            resources: Optional list of specific resource types to generate.
                      If None, generates all applicable resources.

        Returns:
            A ``K8sManifestResult`` containing all generated manifests.
        """
        logger.info("Generating Kubernetes manifests")
        namespace = analysis.get("namespace", _DEFAULT_NAMESPACE)
        app_name = analysis.get("app_name", "app")
        app_version = analysis.get("app_version", "1.0.0")

        labels = self._build_common_labels(app_name, app_version, namespace)

        if resources is None:
            resources = [
                K8sResourceType.DEPLOYMENT,
                K8sResourceType.SERVICE,
                K8sResourceType.INGRESS,
                K8sResourceType.SECRET,
                K8sResourceType.CONFIGMAP,
                K8sResourceType.PVC,
                K8sResourceType.HPA,
                K8sResourceType.NETWORK_POLICY,
            ]

        generated: list[K8sResource] = []
        notes: list[str] = []

        config = {
            "app_name": app_name,
            "app_version": app_version,
            "namespace": namespace,
            "labels": labels,
            "analysis": analysis,
        }

        for resource_type in resources:
            try:
                resource = await self._generate_resource(resource_type, config)
                if resource is not None:
                    generated.append(resource)
            except Exception as exc:
                logger.warning(
                    "Failed to generate %s: %s",
                    resource_type.value,
                    exc,
                )
                notes.append(f"Skipped {resource_type.value}: {exc}")

        result = K8sManifestResult(
            resources=generated,
            namespace=namespace,
            total_resources=len(generated),
            notes=notes,
        )

        logger.info(
            "Kubernetes manifests generated",
            total_resources=result.total_resources,
            namespace=namespace,
        )
        return result

    async def generate_deployment(self, config: dict[str, Any]) -> K8sResource:
        """Generate a Deployment manifest."""
        app_name = config["app_name"]
        namespace = config["namespace"]
        labels = config["labels"]
        analysis = config["analysis"]

        port = analysis.get("port", 8000)
        image = analysis.get("image", f"{app_name}:latest")
        replicas = analysis.get("replicas", 2)
        env_vars = analysis.get("env_vars", {})

        security = self._security_defaults
        resources = self._resource_defaults
        health = self._health_defaults

        container = {
            "name": app_name,
            "image": image,
            "ports": [{"containerPort": port, "protocol": "TCP"}],
            "resources": {
                "requests": {
                    "cpu": resources.cpu_request,
                    "memory": resources.memory_request,
                },
                "limits": {
                    "cpu": resources.cpu_limit,
                    "memory": resources.memory_limit,
                },
            },
            "securityContext": {
                "runAsNonRoot": security.run_as_non_root,
                "runAsUser": security.run_as_user,
                "runAsGroup": security.run_as_group,
                "readOnlyRootFilesystem": security.read_only_root_filesystem,
                "allowPrivilegeEscalation": security.allow_privilege_escalation,
                "capabilities": {"drop": security.capabilities_drop},
            },
            "livenessProbe": self._build_http_probe(health, "liveness"),
            "readinessProbe": self._build_http_probe(health, "readiness"),
            "startupProbe": self._build_http_probe(health, "startup"),
            "volumeMounts": self._build_volume_mounts(analysis),
        }

        if env_vars:
            container["env"] = [
                {"name": k, "value": str(v)} for k, v in env_vars.items()
            ]

        pod_spec: dict[str, Any] = {
            "containers": [container],
            "securityContext": {
                "fsGroup": security.fs_group,
            },
        }

        if analysis.get("volumes"):
            pod_spec["volumes"] = self._build_volumes(analysis)

        deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": app_name,
                "namespace": namespace,
                "labels": labels,
            },
            "spec": {
                "replicas": replicas,
                "selector": {
                    "matchLabels": {app_name: app_name},
                },
                "template": {
                    "metadata": {
                        "labels": {
                            **labels,
                            app_name: app_name,
                        },
                    },
                    "spec": pod_spec,
                },
                "strategy": {
                    "type": "RollingUpdate",
                    "rollingUpdate": {
                        "maxSurge": "25%",
                        "maxUnavailable": "0",
                    },
                },
            },
        }

        content = yaml.dump(deployment, default_flow_style=False, sort_keys=False)
        return K8sResource(
            resource_type=K8sResourceType.DEPLOYMENT,
            name=app_name,
            namespace=namespace,
            content=content,
            labels=labels,
        )

    async def generate_service(self, config: dict[str, Any]) -> K8sResource:
        """Generate a Service manifest."""
        app_name = config["app_name"]
        namespace = config["namespace"]
        labels = config["labels"]
        analysis = config["analysis"]

        port = analysis.get("port", 8000)
        service_type = ServiceType(
            analysis.get("service_type", ServiceType.CLUSTER_IP.value)
        )

        service = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": app_name,
                "namespace": namespace,
                "labels": labels,
            },
            "spec": {
                "type": service_type.value,
                "selector": {app_name: app_name},
                "ports": [
                    {
                        "port": port,
                        "targetPort": port,
                        "protocol": "TCP",
                        "name": "http",
                    }
                ],
            },
        }

        content = yaml.dump(service, default_flow_style=False, sort_keys=False)
        return K8sResource(
            resource_type=K8sResourceType.SERVICE,
            name=app_name,
            namespace=namespace,
            content=content,
            labels=labels,
        )

    async def generate_ingress(self, config: dict[str, Any]) -> K8sResource:
        """Generate an Ingress manifest with TLS support."""
        app_name = config["app_name"]
        namespace = config["namespace"]
        labels = config["labels"]
        analysis = config["analysis"]

        host = analysis.get("host", f"{app_name}.example.com")
        ingress_class = IngressClass(
            analysis.get("ingress_class", IngressClass.NGINX.value)
        )
        tls_secret_name = analysis.get("tls_secret_name", f"{app_name}-tls")
        path_type = analysis.get("path_type", "Prefix")
        port = analysis.get("port", 8000)

        ingress = {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "Ingress",
            "metadata": {
                "name": app_name,
                "namespace": namespace,
                "labels": labels,
                "annotations": {
                    "nginx.ingress.kubernetes.io/ssl-redirect": "true",
                    "nginx.ingress.kubernetes.io/proxy-body-size": "10m",
                    "nginx.ingress.kubernetes.io/proxy-read-timeout": "60",
                    "nginx.ingress.kubernetes.io/proxy-send-timeout": "60",
                },
            },
            "spec": {
                "ingressClassName": ingress_class.value,
                "tls": [
                    {
                        "hosts": [host],
                        "secretName": tls_secret_name,
                    }
                ],
                "rules": [
                    {
                        "host": host,
                        "http": {
                            "paths": [
                                {
                                    "path": "/",
                                    "pathType": path_type,
                                    "backend": {
                                        "service": {
                                            "name": app_name,
                                            "port": {"number": port},
                                        },
                                    },
                                }
                            ],
                        },
                    }
                ],
            },
        }

        content = yaml.dump(ingress, default_flow_style=False, sort_keys=False)
        return K8sResource(
            resource_type=K8sResourceType.INGRESS,
            name=app_name,
            namespace=namespace,
            content=content,
            labels=labels,
        )

    async def generate_secrets(self, config: dict[str, Any]) -> K8sResource:
        """Generate a Secret manifest for sensitive configuration."""
        app_name = config["app_name"]
        namespace = config["namespace"]
        labels = config["labels"]
        analysis = config["analysis"]

        secret_data = analysis.get("secrets", {})
        secret_type = analysis.get("secret_type", "Opaque")

        if not secret_data:
            secret_data = {
                "DATABASE_URL": "CHANGEME",
                "SECRET_KEY": "CHANGEME",
            }
            logger.info(
                "No secrets provided in analysis – using placeholder values"
            )

        secret = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": f"{app_name}-secret",
                "namespace": namespace,
                "labels": labels,
            },
            "type": secret_type,
            "stringData": secret_data,
        }

        content = yaml.dump(secret, default_flow_style=False, sort_keys=False)
        return K8sResource(
            resource_type=K8sResourceType.SECRET,
            name=f"{app_name}-secret",
            namespace=namespace,
            content=content,
            labels=labels,
        )

    async def generate_configmap(self, config: dict[str, Any]) -> K8sResource:
        """Generate a ConfigMap manifest for non-sensitive configuration."""
        app_name = config["app_name"]
        namespace = config["namespace"]
        labels = config["labels"]
        analysis = config["analysis"]

        config_data = analysis.get("config", {})
        if not config_data:
            config_data = {
                "APP_ENV": "production",
                "LOG_LEVEL": "info",
                "WORKERS": "4",
            }

        configmap = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": f"{app_name}-config",
                "namespace": namespace,
                "labels": labels,
            },
            "data": {k: str(v) for k, v in config_data.items()},
        }

        content = yaml.dump(configmap, default_flow_style=False, sort_keys=False)
        return K8sResource(
            resource_type=K8sResourceType.CONFIGMAP,
            name=f"{app_name}-config",
            namespace=namespace,
            content=content,
            labels=labels,
        )

    async def generate_pvc(self, config: dict[str, Any]) -> K8sResource:
        """Generate a PersistentVolumeClaim manifest."""
        app_name = config["app_name"]
        namespace = config["namespace"]
        labels = config["labels"]
        analysis = config["analysis"]

        storage_size = analysis.get("storage_size", "10Gi")
        storage_class = analysis.get("storage_class", "standard")
        access_mode = VolumeAccessMode(
            analysis.get("access_mode", VolumeAccessMode.READ_WRITE_ONCE.value)
        )

        pvc = {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {
                "name": f"{app_name}-data",
                "namespace": namespace,
                "labels": labels,
            },
            "spec": {
                "accessModes": [access_mode.value],
                "storageClassName": storage_class,
                "resources": {
                    "requests": {
                        "storage": storage_size,
                    },
                },
            },
        }

        content = yaml.dump(pvc, default_flow_style=False, sort_keys=False)
        return K8sResource(
            resource_type=K8sResourceType.PVC,
            name=f"{app_name}-data",
            namespace=namespace,
            content=content,
            labels=labels,
        )

    async def generate_hpa(self, config: dict[str, Any]) -> K8sResource:
        """Generate a HorizontalPodAutoscaler manifest."""
        app_name = config["app_name"]
        namespace = config["namespace"]
        labels = config["labels"]
        analysis = config["analysis"]

        hpa_config = HPAConfig(
            min_replicas=analysis.get("min_replicas", self._hpa_defaults.min_replicas),
            max_replicas=analysis.get("max_replicas", self._hpa_defaults.max_replicas),
            cpu_target_percentage=analysis.get(
                "cpu_target", self._hpa_defaults.cpu_target_percentage
            ),
            memory_target_percentage=analysis.get(
                "memory_target", self._hpa_defaults.memory_target_percentage
            ),
        )

        hpa = {
            "apiVersion": "autoscaling/v2",
            "kind": "HorizontalPodAutoscaler",
            "metadata": {
                "name": f"{app_name}-hpa",
                "namespace": namespace,
                "labels": labels,
            },
            "spec": {
                "scaleTargetRef": {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "name": app_name,
                },
                "minReplicas": hpa_config.min_replicas,
                "maxReplicas": hpa_config.max_replicas,
                "metrics": [
                    {
                        "type": "Resource",
                        "resource": {
                            "name": "cpu",
                            "target": {
                                "type": "Utilization",
                                "averageUtilization": hpa_config.cpu_target_percentage,
                            },
                        },
                    },
                    {
                        "type": "Resource",
                        "resource": {
                            "name": "memory",
                            "target": {
                                "type": "Utilization",
                                "averageUtilization": hpa_config.memory_target_percentage,
                            },
                        },
                    },
                ],
                "behavior": {
                    "scaleDown": {
                        "stabilizationWindowSeconds": 300,
                        "policies": [
                            {
                                "type": "Percent",
                                "value": 10,
                                "periodSeconds": 60,
                            }
                        ],
                    },
                    "scaleUp": {
                        "stabilizationWindowSeconds": 60,
                        "policies": [
                            {
                                "type": "Percent",
                                "value": 100,
                                "periodSeconds": 15,
                            }
                        ],
                    },
                },
            },
        }

        content = yaml.dump(hpa, default_flow_style=False, sort_keys=False)
        return K8sResource(
            resource_type=K8sResourceType.HPA,
            name=f"{app_name}-hpa",
            namespace=namespace,
            content=content,
            labels=labels,
        )

    async def generate_network_policy(self, config: dict[str, Any]) -> K8sResource:
        """Generate a NetworkPolicy manifest."""
        app_name = config["app_name"]
        namespace = config["namespace"]
        labels = config["labels"]
        analysis = config["analysis"]

        policy_config = NetworkPolicyConfig(
            allow_ingress_from=analysis.get(
                "ingress_namespaces",
                self._get_default_network_policy_config().allow_ingress_from,
            ),
            deny_all_default=analysis.get("deny_all_default", True),
        )

        ingress_rules: list[dict[str, Any]] = []
        if policy_config.allow_ingress_from:
            for ns in policy_config.allow_ingress_from:
                ingress_rules.append(
                    {
                        "from": [
                            {"namespaceSelector": {"matchLabels": {"kubernetes.io/metadata.name": ns}}}
                        ],
                        "ports": [
                            {"protocol": "TCP", "port": analysis.get("port", 8000)}
                        ],
                    }
                )

        egress_rules: list[dict[str, Any]] = []
        if policy_config.allow_egress_to:
            for ns in policy_config.allow_egress_to:
                egress_rules.append(
                    {
                        "to": [
                            {"namespaceSelector": {"matchLabels": {"kubernetes.io/metadata.name": ns}}}
                        ],
                    }
                )

        network_policy: dict[str, Any] = {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "NetworkPolicy",
            "metadata": {
                "name": f"{app_name}-network-policy",
                "namespace": namespace,
                "labels": labels,
            },
            "spec": {
                "podSelector": {
                    "matchLabels": {app_name: app_name},
                },
                "policyTypes": ["Ingress", "Egress"],
            },
        }

        if ingress_rules:
            network_policy["spec"]["ingress"] = ingress_rules
        else:
            network_policy["spec"]["ingress"] = []

        if egress_rules:
            network_policy["spec"]["egress"] = egress_rules
        else:
            network_policy["spec"]["egress"] = [
                {"to": [{"namespaceSelector": {}}]}
            ]

        content = yaml.dump(network_policy, default_flow_style=False, sort_keys=False)
        return K8sResource(
            resource_type=K8sResourceType.NETWORK_POLICY,
            name=f"{app_name}-network-policy",
            namespace=namespace,
            content=content,
            labels=labels,
        )

    # ------------------------------------------------------------------
    # Private helpers – resource generation dispatcher
    # ------------------------------------------------------------------

    async def _generate_resource(
        self,
        resource_type: K8sResourceType,
        config: dict[str, Any],
    ) -> K8sResource | None:
        """Dispatch to the appropriate generator based on resource type."""
        generators = {
            K8sResourceType.DEPLOYMENT: self.generate_deployment,
            K8sResourceType.SERVICE: self.generate_service,
            K8sResourceType.INGRESS: self.generate_ingress,
            K8sResourceType.SECRET: self.generate_secrets,
            K8sResourceType.CONFIGMAP: self.generate_configmap,
            K8sResourceType.PVC: self.generate_pvc,
            K8sResourceType.HPA: self.generate_hpa,
            K8sResourceType.NETWORK_POLICY: self.generate_network_policy,
        }

        generator = generators.get(resource_type)
        if generator is None:
            logger.warning("No generator for resource type: %s", resource_type.value)
            return None

        return await generator(config)

    # ------------------------------------------------------------------
    # Private helpers – labels and probe building
    # ------------------------------------------------------------------

    @staticmethod
    def _build_common_labels(
        app_name: str,
        app_version: str,
        namespace: str,
    ) -> dict[str, str]:
        """Build standard Kubernetes labels for all resources."""
        return {
            _APP_LABEL: app_name,
            _APP_VERSION_LABEL: app_version,
            _APP_MANAGED_BY_LABEL: "forge-ai",
            _APP_COMPONENT_LABEL: namespace,
        }

    def _build_http_probe(
        self,
        health: HealthProbe,
        probe_type: str,
    ) -> dict[str, Any]:
        """Build an HTTP-based probe configuration."""
        probe: dict[str, Any] = {
            "httpGet": {
                "path": health.path,
                "port": health.port,
            },
        }

        if probe_type == "startup":
            probe["initialDelaySeconds"] = 5
            probe["periodSeconds"] = 10
            probe["failureThreshold"] = 30
        elif probe_type == "liveness":
            probe["initialDelaySeconds"] = health.initial_delay_seconds
            probe["periodSeconds"] = health.period_seconds
            probe["timeoutSeconds"] = health.timeout_seconds
            probe["failureThreshold"] = health.failure_threshold
        else:
            probe["initialDelaySeconds"] = health.initial_delay_seconds
            probe["periodSeconds"] = health.period_seconds
            probe["timeoutSeconds"] = health.timeout_seconds
            probe["successThreshold"] = health.success_threshold
            probe["failureThreshold"] = health.failure_threshold

        return probe

    # ------------------------------------------------------------------
    # Private helpers – volume configuration
    # ------------------------------------------------------------------

    def _build_volume_mounts(self, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Build volume mount specifications from analysis."""
        mounts: list[dict[str, Any]] = []
        volumes = analysis.get("volumes", [])

        for vol in volumes:
            if isinstance(vol, dict):
                mount_path = vol.get("mount_path", "/data")
                vol_name = vol.get("name", "data")
            else:
                mount_path = str(vol)
                vol_name = "data"

            mounts.append(
                {
                    "name": vol_name,
                    "mountPath": mount_path,
                    "readOnly": False,
                }
            )

        if not mounts:
            mounts.append(
                {
                    "name": "tmp",
                    "mountPath": "/tmp",
                }
            )

        return mounts

    def _build_volumes(self, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Build volume specifications from analysis."""
        volumes: list[dict[str, Any]] = []
        raw_volumes = analysis.get("volumes", [])

        for vol in raw_volumes:
            if isinstance(vol, dict):
                vol_name = vol.get("name", "data")
                pvc_name = vol.get("pvc_name")
                if pvc_name:
                    volumes.append(
                        {
                            "name": vol_name,
                            "persistentVolumeClaim": {
                                "claimName": pvc_name,
                            },
                        }
                    )
                else:
                    volumes.append(
                        {
                            "name": vol_name,
                            "emptyDir": {},
                        }
                    )
            else:
                volumes.append(
                    {
                        "name": "data",
                        "emptyDir": {},
                    }
                )

        volumes.append(
            {
                "name": "tmp",
                "emptyDir": {},
            }
        )

        return volumes

    # ------------------------------------------------------------------
    # Private helpers – network policy config
    # ------------------------------------------------------------------

    @staticmethod
    def _get_default_network_policy_config() -> NetworkPolicyConfig:
        """Return default network policy configuration."""
        return NetworkPolicyConfig(
            allow_ingress_from=["kube-system", "ingress-nginx"],
            deny_all_default=True,
        )
