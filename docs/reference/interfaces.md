# lumiscrape インターフェース・型仕様書 (Auto-generated)

> 本ドキュメントはソースコードの型定義および Docstring から自動生成されています。
> 手動で直接編集しないでください。更新方法: `./scripts/generate-docs.sh`

## 目次
- [1. ドメインスキーマ (core.schemas)](#1-ドメインスキーマ-coreschemas)
- [2. ストレージプロトコル (infrastructure.storage_interface)](#2-ストレージプロトコル-infrastructurestorage_interface)
- [3. クローラー基盤 (scrapers.base_crawler)](#3-クローラー基盤-scrapersbase_crawler)
- [4. データベース連携 (infrastructure.db_client)](#4-データベース連携-infrastructuredb_client)
- [5. システム共通例外 (core.exceptions)](#5-システム共通例外-coreexceptions)

---

## 1. ドメインスキーマ (core.schemas)

### `EventSchedule` (Pydantic Model)

Canonical schema for scraped event schedule data.

| フィールド | 型 | デフォルト値 | 説明 |
| :--- | :--- | :--- | :--- |
| `site_id` | `str` | *必須* | Identifier for the source website |
| `source_url` | `HttpUrl` | *必須* | Original URL of the event |
| `title` | `str` | *必須* | Title of the event |
| `start_at` | `datetime` | *必須* | Event start timestamp (ISO8601) |
| `end_at` | `datetime | None` | `None` | Event end timestamp (ISO8601) |
| `venue` | `str | None` | `None` | Event venue or location |
| `description` | `str | None` | `None` | Event details or description |
| `raw_payload_key` | `str | None` | `None` | MinIO object key for raw HTML/JSON |
| `extracted_via` | `str` | `mechanical` | Extraction method: mechanical or llm_fallback |

### `ScrapeMetadata` (Pydantic Model)

Metadata attached to raw crawled data stored in MinIO.

| フィールド | 型 | デフォルト値 | 説明 |
| :--- | :--- | :--- | :--- |
| `site_id` | `str` | *必須* | Identifier for the source website |
| `url` | `str` | *必須* | Original scraped URL |
| `status_code` | `int` | `200` | HTTP response status code |
| `content_type` | `str` | `text/html` | HTTP Content-Type header |
| `fetched_at` | `datetime` | *必須* | Timestamp when payload was fetched |
| `content_length` | `int` | *必須* | Compressed payload size in bytes |
| `is_gzipped` | `bool` | `True` | Whether the payload is Gzip compressed |

---

## 2. ストレージプロトコル (infrastructure.storage_interface)

### `RawStorageClient` (Protocol)

Protocol defining the In/Out interface for raw scraping data lake.

#### メソッド一覧

- **`delete_object(self, object_key: str) -> bool`**
  - Deletes object from storage.
- **`exists(self, object_key: str) -> bool`**
  - Checks if the specified object key exists in storage.
- **`get_raw_html(self, object_key: str) -> StoredPayload`**
  - Retrieves and decompresses raw HTML and returns payload with metadata.
- **`list_objects(self, site_id: str | None = None, prefix: str | None = None) -> list[StoredObjectMetadata]`**
  - Lists stored objects filtered by site_id and prefix.
- **`save_raw_html(self, site_id: str, url: str, body: bytes | str, status_code: int = 200, content_type: str = 'text/html') -> StoredObjectMetadata`**
  - Compresses and uploads raw HTML to storage lake with attached metadata.

### `StoredObjectMetadata` (Pydantic Model)

Metadata describing a raw scrape object saved in storage.

| フィールド | 型 | デフォルト値 | 説明 |
| :--- | :--- | :--- | :--- |
| `object_key` | `str` | *必須* | S3 object key path |
| `site_id` | `str` | *必須* | Target site identifier |
| `url` | `str` | *必須* | Source URL scraped |
| `status_code` | `int` | `200` | HTTP status code |
| `content_type` | `str` | `text/html` | Content-Type header |
| `fetched_at` | `datetime` | *必須* | Timestamp when payload was fetched |
| `compressed_size` | `int` | *必須* | Size in bytes after Gzip compression |
| `uncompressed_size` | `int` | *必須* | Original payload size in bytes |
| `sha256_checksum` | `str` | *必須* | Hex digest of uncompressed body |
| `is_gzipped` | `bool` | `True` | Whether payload is Gzip compressed |

### `StoredPayload` (Pydantic Model)

Container for retrieved content and its attached metadata.

| フィールド | 型 | デフォルト値 | 説明 |
| :--- | :--- | :--- | :--- |
| `content` | `str` | *必須* | Decompressed UTF-8 content string |
| `metadata` | `StoredObjectMetadata` | *必須* | Object metadata |

---

## 3. クローラー基盤 (scrapers.base_crawler)

### `BaseRawCrawler` (Base Spider Class)

Base spider for collecting raw HTML/JSON directly into MinIO data lake.

Subclasses only need to define `name` and `start_urls`.
All raw payload persistence, Gzip compression, and metadata storage
are handled automatically by the attached downloader middleware.

#### メソッド一覧

- **`parse(self, response: Response, **_kwargs: Any) -> Generator[ScrapeMetadata, None, None]`**
  - Default parse handler that yields the raw object metadata saved to MinIO.
- **`start_requests(self) -> Generator[Request, None, None]`**
  - Generates initial requests with optional JS rendering flag in meta.

---

## 4. データベース連携 (infrastructure.db_client)

### `PostgresClient` (Class)

Handles persistence of canonical data models into PostgreSQL.

#### メソッド一覧

- **`init_tables(self) -> None`**
  - Creates table schemas if they do not exist.
- **`upsert_events(self, events: Sequence[EventSchedule]) -> int`**
  - Upserts canonical event records into PostgreSQL.

---

## 5. システム共通例外 (core.exceptions)

| 例外クラス名 | 継承元 | 説明 |
| :--- | :--- | :--- |
| `LumiscrapeError` | `Exception` | Base exception for all lumiscrape errors. |
| `ParseError` | `LumiscrapeError` | Raised when mechanical parsing fails or required fields are missing. |
| `StorageError` | `LumiscrapeError` | Raised when object storage (MinIO) operations fail. |
| `DatabaseError` | `LumiscrapeError` | Raised when database operations fail. |
| `LLMFallbackError` | `LumiscrapeError` | Raised when autonomous LLM fallback fails. |
