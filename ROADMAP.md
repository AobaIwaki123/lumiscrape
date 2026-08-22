# lumiscrape 開発ロードマップ (ROADMAP.md)

本ドキュメントは、汎用 Web スクレイピング＆データ統合基盤 `lumiscrape` の開発計画および実装フェーズを定義します。

---

## 開発コンセプト

1. **軽量・堅牢な Kubernetes ネイティブ運用 (K8s Native & No Bloatware)**:
   - 巨大で過剰な外部ミドルウェア（Kafka/MySQL/MongoDB等）を排除し、Kubernetes の Job/CronJob と MinIO S3 データレイクを直接活用する軽量な管理ダッシュボードを採用。
2. **Raw 取り込みとパースの完全分離 (Separation of Ingestion & Extraction)**:
   - **Raw 取り込み (Ingestion)**: サイトごとの個別 Spider 実装を最小化し、URL・設定値の宣言のみで動作する共通基底 Spider (`BaseRawCrawler`) で MinIO へ Gzip 保存。
   - **データ抽出 (Extraction)**: MinIO に蓄積された Raw HTML からドメインモデル (`EventSchedule`) への構造化は、サイトごとに静的に戦略（機械的ルール vs LLM）を決定して適用。
3. **Clean Architecture による責務の分離**:
   - ドメイン層 (`src/core/`)、インフラ層 (`src/infrastructure/`)、アプリケーション層 (`src/scrapers/`, `src/dashboard/`) を分離し、長期的な保守性と拡張性を担保。

---

## フェーズ一覧

### フェーズ 1: データレイクとインフラ基盤の確立【完了】
Kubernetes 上にデータレイクと実行基盤を構築し、Raw データの蓄積およびドキュメント自動生成基盤を確立。

- [x] **MinIO データレイクデプロイと 7日間 ILM 設定 (`k8s/minio/`, `k8s/argocd/`)**
  - Rook-Ceph (`ceph-rbd` 20Gi) バックエンドの MinIO サーバー構築
  - 7日間保持後に自動物理削除する ILM (Lifecycle) ルール適用 Job
  - ArgoCD による GitOps 自動同期管理
- [x] **Raw データ保存用 In/Out インターフェース実装 (`src/infrastructure/storage_interface.py`, `minio_client.py`)**
  - `RawStorageClient` Protocol (In/Out 抽象契約)
  - Gzip 圧縮ストリーム保存・自動解凍取得・AWS SigV4 整合メタデータ管理
  - Scrapy ミドルウェア (`MinIORawStorageMiddleware`) 連携
- [x] **インターフェース仕様書の自動生成 & CI ドリフト検証 (`tools/generate_docs.py`, `docs/reference/interfaces.md`)**
  - ソースコード AST & Pydantic 反射による仕様書 1 箇所集約生成
  - `verify-all.sh` および CI での乖離（ドリフト）防止チェック

---

### フェーズ 2: Raw 取り込み基盤と K8s 管理ダッシュボードの確立
サイト固有コードを最小化し、Kubernetes 上でのクローラー実行・URL 登録・状態可視化ダッシュボードを整備。

- [x] **1. 共通 Raw 取り込み基盤 BaseRawCrawler & サンプル Spider の実装 (`src/scrapers/base_crawler.py`)**
  - 5 行の定義のみで動作する共通基底 Spider および `=LOVE` サンプル Spider 実装
- [ ] **2. 軽量 K8s 管理ダッシュボードの実装 (`src/dashboard/`)**
  - **URL / サイト登録フォーム**: シード URL、巡回頻度（Cron）、サイト識別子の登録
  - **一覧 & 監視画面**: 登録サイト一覧、MinIO 保存件数・最新取得状況の可視化
  - **K8s Job コントローラー**: ブラウザからの「今すぐ実行」および K8s Job の起動・Pod ログ取得
- [ ] **3. 管理ダッシュボードの Kubernetes デプロイ (`k8s/dashboard/`, `k8s/argocd/`)**
  - FastAPI ダッシュボードの Deployment / Service / Ingress (`lumiscrape.aooba.net`)
  - K8s RBAC（Job / Pod 実行権限）の付与
  - ArgoCD Application 登録
- [ ] **4. Browserless 動的レンダリングプロキシ連携 (`k8s/browserless/`)**
  - SPA や JavaScript 動的生成サイト向けのヘッドレスブラウザ連携

---

### フェーズ 3: サイト別パース戦略（静的ルール vs LLM）と自律修復基盤
MinIO に蓄積された Raw HTML から正規化ドメインモデル (`EventSchedule`) への抽出処理を実装。

- [ ] **1. 静的ルール・パーサーエンジン (`src/parsers/mechanical/`)**
  - 安定したサイト向けの XPath / CSS セレクタ定義駆動による機械的抽出エンジン
- [ ] **2. LLM パーサーエンジン (`src/infrastructure/llm_fallback/`)**
  - 複雑・動的サイト向けの Crawl4AI ノイズ除去 ＋ Gemini API Structured Outputs による構造化抽出
  - 呼び出し回数リミッター（ガードレール）
- [ ] **3. PostgreSQL マスター DB 連携 (`src/infrastructure/db_client.py`)**
  - `event_schedules` テーブルのスキーマ管理と Upsert ロジック
- [ ] **4. セレクタ自動修復 CLI ツール (`tools/rule_generator/`)**
  - 静的ルール破損時の通知と、最新 Raw HTML からセレクタ修正案を自動生成・提示する支援ツール

---

### フェーズ 4: 運用監視・アラートと実サイト展開
複数サイトへのスケールアウトと運用監視を確立。

- [ ] **Slack アラート通知連携**
  - クロール失敗・パースエラー・LLM フォールバック発動時の自動通知
- [ ] **10+ サイトへの汎用クローラー適用 & パース検証**
  - 実運用サイトの登録とデータ抽出パイプラインの結合テスト
