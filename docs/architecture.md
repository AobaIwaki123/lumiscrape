# lumiscrape システムアーキテクチャ

本ドキュメントでは、`lumiscrape` の全体アーキテクチャ、データフロー、コンポーネント構成を解説します。

---

## 1. 全体アーキテクチャ図

```mermaid
flowchart TD
    subgraph "Admin & Control Layer"
        User["User / Developer"]
        WebUI["Go + HTMX Web UI (pkg/web)"]
        StateDB[("Site Registry / State DB")]
        User -->|"Register URL / Trigger"| WebUI
        WebUI -->|"CRUD Site Rules"| StateDB
    end

    subgraph "Collection & Ingestion Layer (Runtime)"
        Scheduler["Scheduler (pkg/scheduler)"]
        Fetcher["HTTP Client / Fetcher"]
        MinIO[("MinIO S3 Data Lake (Raw HTML/JSON)")]
        StateDB -->|"Read Targets & Schedule"| Scheduler
        Scheduler -->|"Dispatch HTTP GET"| Fetcher
        Fetcher -->|"Target Websites"| WebTarget["Target Web Pages"]
        Fetcher -->|"Gzip Stream Upload"| MinIO
        Fetcher -->|"Update Status"| StateDB
    end

    subgraph "Parser & Normalization Layer (Runtime)"
        RuleConfig["YAML Selector Configs"]
        ParserEngine["Colly Engine (pkg/parser)"]
        TargetDB[("Normalized Storage / DB")]
        MinIO -->|"Trigger / Read Raw Data"| ParserEngine
        RuleConfig -->|"Read Selectors"| ParserEngine
        ParserEngine -->|"Store Structured JSON"| TargetDB
    end

    subgraph "LLM-Assisted Rule Tuning Pipeline (Offline / Fallback)"
        Trafilatura["Trafilatura Clean Pipeline"]
        LLMEngine["LLM / Gemini API (tools/rule-generator)"]
        SlackAlert["Slack Alert / Notification"]
        
        ParserEngine -->|"On Rule Failure"| SlackAlert
        MinIO -->|"Fetch Raw HTML"| Trafilatura
        Trafilatura -->|"Clean Markdown/DOM"| LLMEngine
        LLMEngine -->|"Generate New Selectors"| RuleConfig
    end
```

---

## 2. データフロー

1. **URL 登録とスケジュール管理**:
   - ユーザーは Go + HTMX の管理画面から対象 URL と Cron スケジュールを登録します。
2. **収集 (Extract & Load)**:
   - スケジューラーが定期的に HTTP GET を実行し、取得した HTML を gzip 圧縮して MinIO に即時保存します。
   - 収集レイヤーはパースを行わないため、高速かつ安定して動作します。
3. **機械的変換 (Transform)**:
   - パーサーエンジン（Colly）が YAML 設定ファイルに定義されたセレクタ（CSS/XPath）に従い、MinIO 内の HTML を構造化データ（JSON）に変換します。
4. **LLM アシスト（チューニング＆フォールバック）**:
   - 新規サイトのルール作成時や、サイト側の構造変更（セレクタ破損）検知時に、Trafilatura でノイズを除去したテキストを LLM に渡し、新しいセレクタ定義を自動生成・提案します。
