"""Unit tests for the Kubernetes management dashboard."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from dashboard.app import app
from dashboard.k8s_client import KubernetesCrawlerClient
from dashboard.models import SiteConfig
from dashboard.site_service import SiteService


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def temp_site_service(tmp_path: Path) -> SiteService:
    mock_storage = MagicMock()
    mock_storage.list_objects.return_value = []
    return SiteService(config_dir=str(tmp_path), storage_client=mock_storage)


def test_site_service_crud(temp_site_service: SiteService) -> None:
    # 1. Default sites creation
    sites = temp_site_service.list_sites()
    assert len(sites) >= 1
    assert any(s.site_id == "equal_love" for s in sites)

    # 2. Save new site
    new_site = SiteConfig(
        site_id="site_test",
        name="Test Site",
        url="https://example.com",
        cron_schedule="0 0 * * *",
        render_js=True,
    )
    temp_site_service.save_site(new_site)

    # 3. Retrieve site
    retrieved = temp_site_service.get_site("site_test")
    assert retrieved is not None
    assert retrieved.name == "Test Site"
    assert retrieved.render_js is True


def test_k8s_client_trigger_and_list() -> None:
    with (
        patch("dashboard.k8s_client.client.BatchV1Api") as mock_batch,
        patch("dashboard.k8s_client.client.CoreV1Api") as mock_core,
        patch("dashboard.k8s_client.config.load_kube_config"),
    ):
        k8s = KubernetesCrawlerClient(namespace="minio")

        # Test trigger_job
        job_name = k8s.trigger_job(site_id="equal_love", url="https://equal-love.jp")
        assert job_name.startswith("crawl-equal-love-")
        assert k8s.batch_v1.create_namespaced_job.called

        # Test list_jobs
        mock_job = MagicMock()
        mock_job.metadata.name = "crawl-equal-love-12345"
        mock_job.metadata.labels = {"site": "equal_love"}
        mock_job.metadata.creation_timestamp = 1000
        mock_job.status.active = 1
        mock_job.status.succeeded = 0
        mock_job.status.failed = 0
        mock_job.status.start_time = None
        mock_job.status.completion_time = None

        mock_batch.return_value.list_namespaced_job.return_value.items = [mock_job]
        jobs = k8s.list_jobs()
        assert len(jobs) == 1
        assert jobs[0].status == "Running"
        assert jobs[0].site_id == "equal_love"

        # Test get_job_logs
        mock_pod = MagicMock()
        mock_pod.metadata.name = "crawl-equal-love-pod"
        mock_core.return_value.list_namespaced_pod.return_value.items = [mock_pod]
        mock_core.return_value.read_namespaced_pod_log.return_value = "Scrapy crawler started..."

        logs = k8s.get_job_logs("crawl-equal-love-12345")
        assert "Scrapy crawler started..." in logs


def test_fastapi_endpoints(client: TestClient) -> None:
    # 1. Health check
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    # 2. Main dashboard HTML
    res = client.get("/")
    assert res.status_code == 200
    assert "lumiscrape" in res.text
    assert "収集対象サイト一覧" in res.text

    # 3. New site form HTML
    res = client.get("/sites/new")
    assert res.status_code == 200
    assert "新規クローラーサイト登録" in res.text

    # 4. Create site POST
    res = client.post(
        "/sites/new",
        data={
            "site_id": "test_band",
            "name": "Test Band Schedule",
            "url": "https://testband.com/live",
            "cron_schedule": "0 12 * * *",
        },
        follow_redirects=False,
    )
    assert res.status_code == 303

    # 5. JSON API list
    res = client.get("/api/sites")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert any(d["site_id"] == "test_band" for d in data)

    # 6. Jobs page HTML
    res = client.get("/jobs")
    assert res.status_code == 200
    assert "Kubernetes ジョブ実行履歴" in res.text
