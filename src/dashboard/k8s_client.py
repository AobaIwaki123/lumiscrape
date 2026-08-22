"""Kubernetes Job and Pod execution client for crawler orchestration."""

import logging
import os
import time

from kubernetes import client, config
from kubernetes.client.exceptions import ApiException

from dashboard.models import JobExecutionRecord

logger = logging.getLogger(__name__)


class KubernetesCrawlerClient:
    """Manages Kubernetes crawler Jobs and retrieves live execution logs."""

    def __init__(
        self, namespace: str = "minio", image: str = "ghcr.io/aobaiwaki123/lumiscrape:latest"
    ):
        self.namespace = os.getenv("JOB_NAMESPACE", namespace)
        self.image = os.getenv("CRAWLER_IMAGE", image)
        self._init_k8s_client()

    def _init_k8s_client(self) -> None:
        """Initialize Kubernetes configuration (In-cluster or kubeconfig)."""
        try:
            config.load_incluster_config()
            logger.info("Loaded in-cluster Kubernetes configuration")
        except Exception:
            try:
                config.load_kube_config()
                logger.info("Loaded local kube-config configuration")
            except Exception as e:
                logger.warning(f"Could not load Kubernetes configuration: {e}")

        self.batch_v1 = client.BatchV1Api()
        self.core_v1 = client.CoreV1Api()

    def trigger_job(self, site_id: str, url: str | None = None, render_js: bool = False) -> str:
        """Trigger a new Scrapy crawling Job on Kubernetes."""
        timestamp = int(time.time())
        job_name = f"crawl-{site_id.replace('_', '-')}-{timestamp}"

        env_vars = [
            client.V1EnvVar(name="SITE_ID", value=site_id),
            client.V1EnvVar(
                name="MINIO_ENDPOINT",
                value=os.getenv("MINIO_ENDPOINT", "minio.minio.svc.cluster.local:9000"),
            ),
            client.V1EnvVar(
                name="MINIO_ACCESS_KEY", value=os.getenv("MINIO_ACCESS_KEY", "minioadmin")
            ),
            client.V1EnvVar(
                name="MINIO_SECRET_KEY", value=os.getenv("MINIO_SECRET_KEY", "minioadmin")
            ),
            client.V1EnvVar(
                name="MINIO_BUCKET_NAME", value=os.getenv("MINIO_BUCKET_NAME", "lumiscrape-raw")
            ),
            client.V1EnvVar(name="MINIO_SECURE", value=os.getenv("MINIO_SECURE", "false")),
        ]
        if url:
            env_vars.append(client.V1EnvVar(name="START_URL", value=url))
        if render_js:
            env_vars.append(client.V1EnvVar(name="RENDER_JS", value="true"))

        container = client.V1Container(
            name="crawler",
            image=self.image,
            image_pull_policy="Always",
            command=["scrapy", "crawl", site_id],
            env=env_vars,
            resources=client.V1ResourceRequirements(
                requests={"cpu": "100m", "memory": "256Mi"},
                limits={"cpu": "1000m", "memory": "1024Mi"},
            ),
        )

        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(
                labels={"app": "lumiscrape-crawler", "site": site_id, "job-name": job_name}
            ),
            spec=client.V1PodSpec(
                restart_policy="Never",
                containers=[container],
            ),
        )

        job_spec = client.V1JobSpec(
            template=template,
            backoff_limit=1,
            ttl_seconds_after_finished=86400,  # 24 hours
        )

        job = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(name=job_name, namespace=self.namespace),
            spec=job_spec,
        )

        try:
            self.batch_v1.create_namespaced_job(namespace=self.namespace, body=job)
            logger.info(f"Successfully triggered Kubernetes Job: {job_name}")
            return job_name
        except ApiException as e:
            logger.error(f"Failed to create Kubernetes Job {job_name}: {e}")
            raise

    def list_jobs(self, limit: int = 20) -> list[JobExecutionRecord]:
        """List recently executed crawler Jobs with their current status."""
        try:
            jobs_resp = self.batch_v1.list_namespaced_job(
                namespace=self.namespace,
                label_selector="app=lumiscrape-crawler",
            )
        except Exception as e:
            logger.warning(f"Failed to list Jobs from Kubernetes: {e}")
            return []

        records: list[JobExecutionRecord] = []
        for job in sorted(
            jobs_resp.items, key=lambda j: j.metadata.creation_timestamp or 0, reverse=True
        )[:limit]:
            status = "Pending"
            if job.status.active:
                status = "Running"
            elif job.status.succeeded:
                status = "Completed"
            elif job.status.failed:
                status = "Failed"

            site_id = (job.metadata.labels or {}).get("site", "unknown")
            started_at = job.status.start_time
            completed_at = job.status.completion_time
            duration = None
            if started_at and completed_at:
                duration = int((completed_at - started_at).total_seconds())

            records.append(
                JobExecutionRecord(
                    job_name=job.metadata.name,
                    site_id=site_id,
                    status=status,
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_seconds=duration,
                )
            )

        return records

    def get_job_logs(self, job_name: str) -> str:
        """Fetch stdout/stderr execution logs from the Pod belonging to a Job."""
        try:
            pods_resp = self.core_v1.list_namespaced_pod(
                namespace=self.namespace,
                label_selector=f"job-name={job_name}",
            )
            if not pods_resp.items:
                return f"No Pod found for Job {job_name} yet."

            pod_name = pods_resp.items[0].metadata.name
            logs = self.core_v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=self.namespace,
                tail_lines=300,
            )
            return str(logs)
        except Exception as e:
            logger.warning(f"Failed to read logs for Job {job_name}: {e}")
            return f"Error retrieving logs: {e}"
