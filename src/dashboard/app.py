"""FastAPI application for the lumiscrape Kubernetes management dashboard."""

import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from dashboard.k8s_client import KubernetesCrawlerClient
from dashboard.models import SiteConfig
from dashboard.site_service import SiteService

logger = logging.getLogger(__name__)

templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

app = FastAPI(
    title="lumiscrape Dashboard",
    description="Kubernetes & MinIO Native Web Scraping Orchestrator",
    version="1.0.0",
)

site_service = SiteService()
k8s_client = KubernetesCrawlerClient()


@app.get("/healthz")
async def health_check() -> dict[str, str]:
    """Liveness / readiness probe endpoint."""
    return {"status": "ok", "app": "lumiscrape-dashboard"}


@app.get("/", response_class=HTMLResponse)
async def dashboard_index(request: Request) -> Response:
    """Render the main dashboard overview with site list and statistics."""
    sites = site_service.list_sites()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"sites": sites},
    )


@app.get("/sites/new", response_class=HTMLResponse)
async def site_new_form(request: Request) -> Response:
    """Render the new site registration form."""
    return templates.TemplateResponse(
        request=request,
        name="site_new.html",
        context={},
    )


@app.post("/sites/new")
async def create_site(
    site_id: str = Form(...),
    name: str = Form(...),
    url: str = Form(...),
    cron_schedule: str = Form("0 */6 * * *"),
    render_js: bool = Form(False),
) -> RedirectResponse:
    """Create a new site configuration."""
    site = SiteConfig(
        site_id=site_id.strip(),
        name=name.strip(),
        url=url.strip(),
        cron_schedule=cron_schedule.strip() if cron_schedule else None,
        render_js=render_js,
        enabled=True,
    )
    site_service.save_site(site)
    return RedirectResponse(url="/", status_code=303)


@app.get("/jobs", response_class=HTMLResponse)
async def list_jobs_view(request: Request) -> Response:
    """Render the Kubernetes Job execution history and live logs view."""
    jobs = k8s_client.list_jobs(limit=30)
    return templates.TemplateResponse(
        request=request,
        name="jobs.html",
        context={"jobs": jobs},
    )


@app.post("/api/jobs/trigger")
async def trigger_crawl_job(site_id: str = Form(...)) -> RedirectResponse:
    """Trigger a Kubernetes crawling Job for the given site."""
    site = site_service.get_site(site_id)
    if not site:
        raise HTTPException(status_code=404, detail=f"Site {site_id} not found")

    try:
        k8s_client.trigger_job(site_id=site.site_id, url=site.url, render_js=site.render_js)
    except Exception as e:
        logger.error(f"Failed to trigger Job for site {site_id}: {e}")

    return RedirectResponse(url="/jobs", status_code=303)


@app.get("/api/jobs/{job_name}/logs")
async def get_job_logs(job_name: str) -> dict[str, str]:
    """API endpoint to fetch live logs from a crawler Job."""
    logs = k8s_client.get_job_logs(job_name)
    return {"job_name": job_name, "logs": logs}


@app.get("/api/sites")
async def get_sites_api() -> list[dict[str, Any]]:
    """API endpoint to get list of configured sites as JSON."""
    sites = site_service.list_sites()
    return [site.model_dump() for site in sites]
