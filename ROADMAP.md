# lumiscrape 開発ロードマップ (ROADMAP.md)

本ドキュメントは、汎用 Web スクレイピング＆データ統合基盤 `lumiscrape` の開発計画および実装フェーズを定義します。

---

## 開発コンセプト

1. **OSS エコシステムの最大活用**: Estela、Scrapy、Browserless、MinIO などの強力な OSS を組み合わせ、自作コード（車輪の再発明）を最小化。
2. **Clean Architecture による責務の分離**: ドメイン（型）、インフラ（外部連携）、アプリケーション（クローラー）を明確に分離し、長期的な保守性と拡張性を担保。
3. **機械処理の高速性と LLM の柔軟性の両立**: 通常時は Scrapy の CSS/XPath による高速バッチ処理を行い、セレクタ破損時のみ Crawl4AI + Gemini API による自己修復フォールバックを発動。

---

## フェーズ一覧

### フェーズ 1: インフラ基盤とデータレイクの確立
Kubernetes 上にデータレイクと実行基盤を構築し、Raw データの蓄積を開始。

- [ ] **MinIO デプロイと ILM 設定 (`k8s/minio`)**
  - MinIO の Kubernetes マニフェスト作成
  - 7日間保持後に自動物理削除する ILM (Lifecycle) ルール設定
- [ ] **Scrapy MinIO Gzip 保存ミドルウェアの実装 (`src/infrastructure/minio_client.py`)**
  - レスポンスをフックし、Gzip 圧縮ストリームで MinIO へ即時アップロード
  - メタデータ（URL、ステータス、取得日時）の付与
- [ ] **PostgreSQL マスター DB 連携 (`src/infrastructure/db_client.py`)**
  - `event_schedules` テーブルの自動マイグレーションと Upsert ロジック

---

### フェーズ 2: オーケストレーションと実行環境の統合
Estela プラットフォームおよび Browserless を導入し、ジョブ管理と動的レンダリングを整備。

- [ ] **Estela プラットフォームのデプロイ (`k8s/estela`)**
  - Estela API, Web UI, Redis, Celery ワーカーの Kubernetes デプロイ
  - Scrapy プロジェクトの Estela 連携設定 (`scrapy.cfg`)
- [ ] **Browserless プロキシ連携 (`k8s/browserless`)**
  - 動的 SPA サイト用のヘッダ/プロキシミドルウェア整備
- [ ] **サイト固有 Spider の実装 (`src/scrapers/scrapy_project/spiders/`)**
  - 対象サイト（例: equal-love 等）の機械的セレクタ Spider 実装
  - Pydantic バリデーションパイプラインとの連携

---

### フェーズ 3: 自律的 LLM フォールバックとルール生成基盤
セレクタ破損時の自動復旧パイプラインと開発支援ツールを構築。

- [ ] **Crawl4AI によるデータ浄化 (`src/infrastructure/llm_fallback/crawl4ai_runner.py`)**
  - 生 HTML から不要 DOM を除去し、クリーンな Markdown を生成
- [ ] **Gemini API Structured Outputs による抽出 (`src/infrastructure/llm_fallback/prompt_manager.py`)**
  - Pydantic スキーマに基づく構造化 JSON 抽出
  - 1日あたりの呼び出し回数リミッター（ガードレール）
- [ ] **XPath / CSS セレクタ自動生成ツール (`tools/rule_generator/`)**
  - 破損アラート検知時の Slack 通知
  - ローカルで最新 HTML からセレクタ修正案を自動提示する CLI ツール

---

### フェーズ 4: 運用監視と拡張性テスト
複数サイトへのスケールアウトと運用監視を確立。

- [ ] **Estela ダッシュボードによる運用監視**
  - ジョブログ、成功/失敗率、所要時間の可視化
- [ ] **Slack アラート連携**
  - パース失敗・フォールバック発動時の通知
- [ ] **10+ サイトへの Spider 拡張と CI/CD パイプライン検証**
