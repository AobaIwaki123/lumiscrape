"""LLM prompt manager for extracting structured JSON using Structured Outputs."""

import json
import os

from pydantic import BaseModel, Field

from core.exceptions import LLMFallbackError
from core.schemas import EventSchedule


class LLMEventExtractionResponse(BaseModel):
    """Schema expected from LLM structured outputs."""

    events: list[EventSchedule] = Field(default_factory=list)
    suggested_css_selector: str | None = Field(
        default=None, description="Suggested updated CSS selector for self-healing"
    )


class LLMPromptManager:
    """Manages Gemini / LLM queries for fallback extraction."""

    def __init__(self, api_key: str | None = None, model_name: str = "gemini-2.5-flash") -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model_name = model_name

    def extract_with_llm(
        self, markdown_content: str, site_id: str, source_url: str
    ) -> LLMEventExtractionResponse:
        """Invokes LLM with structured output schema to extract canonical events."""
        if not self.api_key:
            raise LLMFallbackError("GEMINI_API_KEY environment variable is not configured.")

        system_instruction = (
            "You are an expert data extractor. Extract event schedules from the provided markdown "
            "into the strict JSON schema matching the target EventSchedule format. "
            "Also analyze the DOM/text structure and suggest a stable CSS selector if repeated."
        )

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            prompt = f"Site ID: {site_id}\nSource URL: {source_url}\n\nContent:\n{markdown_content}"

            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=LLMEventExtractionResponse,
                ),
            )

            if isinstance(response.parsed, LLMEventExtractionResponse):
                return response.parsed

            data = json.loads(response.text or "{}")
            return LLMEventExtractionResponse.model_validate(data)
        except Exception as e:
            raise LLMFallbackError(f"LLM fallback extraction failed: {e}") from e
