"""Crawl4AI runner to convert noisy HTML into clean Markdown."""

from core.exceptions import LLMFallbackError


class Crawl4AICleaner:
    """Uses Crawl4AI pipeline to sanitize raw HTML into token-efficient Markdown."""

    async def clean_html_to_markdown(self, raw_html: str, url: str) -> str:
        """Sanitizes raw HTML and produces clean markdown text."""
        try:
            from crawl4ai import AsyncWebCrawler
            from crawl4ai.extraction_strategy import NoExtractionStrategy

            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(
                    url=url,
                    html=raw_html,
                    extraction_strategy=NoExtractionStrategy(),
                    bypass_cache=True,
                )
                if result.success and result.markdown:
                    return str(result.markdown)
                return raw_html[:5000]
        except ImportError:
            # Fallback when crawl4ai optional dependency is not loaded in lightweight test
            return raw_html[:5000]
        except Exception as e:
            raise LLMFallbackError(f"Crawl4AI cleaning failed: {e}") from e
