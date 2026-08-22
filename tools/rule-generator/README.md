# tools/rule-generator

LLM-assisted scraping rule generation pipeline.

## Overview
This tool extracts clean content from raw HTML using Trafilatura, queries an LLM (Gemini API) with structured output schema, and automatically generates CSS/XPath selector rules in YAML format for use in `lumiscrape`.
