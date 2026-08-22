#!/usr/bin/env python3
"""Doc generator that creates docs/reference/interfaces.md from Python source code AST & Pydantic models."""

import importlib
import inspect
import re
from pathlib import Path
from typing import Any, get_type_hints

from pydantic import BaseModel

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = REPO_ROOT / "docs" / "reference" / "interfaces.md"


def clean_type_str(type_str: str) -> str:
    """Removes lengthy package prefixes for clean markdown display."""
    type_str = re.sub(r"[a-zA-Z0-9_\.]+\.([a-zA-Z0-9_]+)", r"\1", type_str)
    type_str = type_str.replace("typing.", "").replace("<class '", "").replace("'>", "")
    return f"`{type_str}`"


def format_type(type_hint: Any) -> str:
    """Formats a type hint into a readable string."""
    if type_hint is None:
        return "`None`"
    return clean_type_str(str(type_hint))


def render_pydantic_model(cls: type[BaseModel]) -> str:
    """Renders a Pydantic model into Markdown table."""
    lines = [
        f"### `{cls.__name__}` (Pydantic Model)\n",
        f"{inspect.getdoc(cls) or ''}\n",
        "| フィールド | 型 | デフォルト値 | 説明 |",
        "| :--- | :--- | :--- | :--- |",
    ]

    hints = get_type_hints(cls)
    for field_name, field_info in cls.model_fields.items():
        type_str = format_type(hints.get(field_name, field_info.annotation))
        default_val = (
            "*必須*"
            if field_info.is_required()
            else f"`{field_info.default}`"
            if field_info.default is not None
            else "`None`"
        )
        description = (field_info.description or "").replace("\n", " ")
        lines.append(f"| `{field_name}` | {type_str} | {default_val} | {description} |")

    lines.append("")
    return "\n".join(lines)


def render_protocol_or_class(cls: type[Any], label: str = "Class / Protocol") -> str:
    """Renders a Protocol or Class and its methods."""
    doc = inspect.getdoc(cls) or ""
    lines = [
        f"### `{cls.__name__}` ({label})\n",
        f"{doc}\n",
    ]

    methods = [
        (name, func)
        for name, func in inspect.getmembers(cls, predicate=inspect.isfunction)
        if not name.startswith("_")
    ]

    if methods:
        lines.append("#### メソッド一覧\n")
        for name, func in methods:
            sig = str(inspect.signature(func))
            # Clean module prefixes in signature
            sig = re.sub(r"[a-zA-Z0-9_\.]+\.([a-zA-Z0-9_]+)", r"\1", sig)
            method_doc = (inspect.getdoc(func) or "").strip()
            lines.append(f"- **`{name}{sig}`**")
            if method_doc:
                lines.append(f"  - {method_doc}")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    print(f"Generating interface reference docs into: {OUTPUT_FILE}")

    content = [
        "# lumiscrape インターフェース・型仕様書 (Auto-generated)",
        "",
        "> 本ドキュメントはソースコードの型定義および Docstring から自動生成されています。",
        "> 手動で直接編集しないでください。更新方法: `./scripts/generate-docs.sh`",
        "",
        "## 目次",
        "- [1. ドメインスキーマ (core.schemas)](#1-ドメインスキーマ-coreschemas)",
        "- [2. ストレージプロトコル (infrastructure.storage_interface)](#2-ストレージプロトコル-infrastructurestorage_interface)",
        "- [3. データベース連携 (infrastructure.db_client)](#3-データベース連携-infrastructuredb_client)",
        "- [4. システム共通例外 (core.exceptions)](#4-システム共通例外-coreexceptions)",
        "",
        "---",
        "",
        "## 1. ドメインスキーマ (core.schemas)",
        "",
    ]

    # 1. core.schemas
    schemas_mod = importlib.import_module("core.schemas")
    content.append(render_pydantic_model(schemas_mod.EventSchedule))
    content.append(render_pydantic_model(schemas_mod.ScrapeMetadata))

    # 2. infrastructure.storage_interface
    content.append("---")
    content.append("")
    content.append("## 2. ストレージプロトコル (infrastructure.storage_interface)")
    content.append("")
    storage_mod = importlib.import_module("infrastructure.storage_interface")
    content.append(render_protocol_or_class(storage_mod.RawStorageClient, label="Protocol"))
    content.append(render_pydantic_model(storage_mod.StoredObjectMetadata))
    content.append(render_pydantic_model(storage_mod.StoredPayload))

    # 3. infrastructure.db_client
    content.append("---")
    content.append("")
    content.append("## 3. データベース連携 (infrastructure.db_client)")
    content.append("")
    db_mod = importlib.import_module("infrastructure.db_client")
    content.append(render_protocol_or_class(db_mod.PostgresClient, label="Class"))

    # 4. core.exceptions
    content.append("---")
    content.append("")
    content.append("## 4. システム共通例外 (core.exceptions)")
    content.append("")
    exc_mod = importlib.import_module("core.exceptions")
    exceptions = [
        "LumiscrapeError",
        "ParseError",
        "StorageError",
        "DatabaseError",
        "LLMFallbackError",
    ]
    lines = [
        "| 例外クラス名 | 継承元 | 説明 |",
        "| :--- | :--- | :--- |",
    ]
    for exc_name in exceptions:
        if hasattr(exc_mod, exc_name):
            exc_cls = getattr(exc_mod, exc_name)
            base_name = exc_cls.__bases__[0].__name__
            doc = (inspect.getdoc(exc_cls) or "").replace("\n", " ")
            lines.append(f"| `{exc_name}` | `{base_name}` | {doc} |")
    lines.append("")
    content.append("\n".join(lines))

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text("\n".join(content), encoding="utf-8")
    print("Done: docs/reference/interfaces.md generated successfully.")


if __name__ == "__main__":
    main()
