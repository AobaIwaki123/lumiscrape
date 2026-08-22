"""Site configuration and MinIO data synchronization service."""

import logging
from pathlib import Path

import yaml

from dashboard.models import SiteConfig
from infrastructure.minio_client import MinIOStorageClient

logger = logging.getLogger(__name__)


class SiteService:
    """Manages site definitions and correlates with MinIO storage statistics."""

    def __init__(
        self, config_dir: str = "configs/sites", storage_client: MinIOStorageClient | None = None
    ):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.storage_client = storage_client or MinIOStorageClient()
        self._ensure_default_sites()

    def _ensure_default_sites(self) -> None:
        """Create sample site configuration if none exist."""
        equal_love_path = self.config_dir / "equal_love.yml"
        if not equal_love_path.exists():
            default_config = {
                "site_id": "equal_love",
                "name": "=LOVE (イコールラブ) 公式スケジュール",
                "url": "https://equal-love.jp/schedule/",
                "cron_schedule": "0 */6 * * *",
                "render_js": False,
                "enabled": True,
            }
            with open(equal_love_path, "w", encoding="utf-8") as f:
                yaml.dump(default_config, f, allow_unicode=True)

    def list_sites(self) -> list[SiteConfig]:
        """List all configured sites with real-time MinIO object counts."""
        sites: list[SiteConfig] = []
        for yaml_file in sorted(self.config_dir.glob("*.yml")):
            try:
                with open(yaml_file, encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}

                site_id = data.get("site_id", yaml_file.stem)
                minio_count = 0
                last_fetched = None

                try:
                    objects = self.storage_client.list_objects(site_id=site_id)
                    minio_count = len(objects)
                    if objects:
                        last_fetched = max(obj.fetched_at for obj in objects)
                except Exception as e:
                    logger.debug(f"MinIO stats fetch failed for site {site_id}: {e}")

                site = SiteConfig(
                    site_id=site_id,
                    name=data.get("name", site_id),
                    url=data.get("url", ""),
                    cron_schedule=data.get("cron_schedule", "0 */6 * * *"),
                    render_js=data.get("render_js", False),
                    enabled=data.get("enabled", True),
                    minio_object_count=minio_count,
                    last_fetched_at=last_fetched,
                )
                sites.append(site)
            except Exception as e:
                logger.error(f"Error reading site config {yaml_file}: {e}")

        return sites

    def save_site(self, site: SiteConfig) -> None:
        """Save or update a site configuration file."""
        file_path = self.config_dir / f"{site.site_id}.yml"
        data = {
            "site_id": site.site_id,
            "name": site.name,
            "url": site.url,
            "cron_schedule": site.cron_schedule,
            "render_js": site.render_js,
            "enabled": site.enabled,
        }
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True)
        logger.info(f"Saved site configuration for: {site.site_id}")

    def get_site(self, site_id: str) -> SiteConfig | None:
        """Retrieve a specific site configuration."""
        file_path = self.config_dir / f"{site_id}.yml"
        if not file_path.exists():
            return None
        with open(file_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return SiteConfig(
            site_id=data.get("site_id", site_id),
            name=data.get("name", site_id),
            url=data.get("url", ""),
            cron_schedule=data.get("cron_schedule", "0 */6 * * *"),
            render_js=data.get("render_js", False),
            enabled=data.get("enabled", True),
        )
