# lumiscrape

General-purpose web scraping and data integration platform using Scrapy, Estela, MinIO, Crawl4AI, and LLM-assisted self-healing.

[![CI](https://github.com/AobaIwaki123/lumiscrape/actions/workflows/ci.yml/badge.svg)](https://github.com/AobaIwaki123/lumiscrape/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 概要

`lumiscrape` は、様々な Web サイトからイベント情報等のデータを収集し、共通フォーマットに正規化して蓄積する統合データ基盤です。

- **Estela オーケストレーション**: Kubernetes 上で動作するオープンソースの Scrapy 管理プラットフォームを採用し、スケジュール管理・実行履歴・ログ可視化を実現（自作 UI 開発を不要化）。
- **Scrapy + Clean Architecture**: 高スループットな非同期クローラーをドメイン（型）・インフラ（外部接続）・アプリ（クローラー）に分離して保守性を担保。
- **データレイク (MinIO)**: 取得した生 HTML/JSON を即座に gzip 圧縮して保存（7日間保持後に自動削除する ILM 設定）。
- **Browserless レンダリング分離**: 動的 SPA サイトのレンダリングを外部プロキシに委譲し、クローラーコンテナの軽量性を維持。
- **Crawl4AI + LLM フォールバック**: セレクタ破損時の自動復旧（HTML の Markdown 化 ＋ Gemini API Structured Outputs による JSON 抽出とセレクタ修正提案）。

詳細なアーキテクチャについては [docs/architecture.md](docs/architecture.md) を参照してください。

---

## ディレクトリ構成

```text
.
├── k8s/                          # Kubernetes デプロイメント用マニフェスト群
│   ├── minio/                    # MinIO デプロイと ILM (7日自動削除) 設定
│   ├── estela/                   # Estela プラットフォームマニフェスト
│   └── browserless/              # ヘッドレスブラウザプロキシ
│
├── src/                          # Python アプリケーションルート (パッケージ)
│   ├── core/                     # 【ドメイン層】Pydantic スキーマ・カスタム例外
│   ├── infrastructure/           # 【インフラ層】MinIO, PostgreSQL, LLM フォールバック
│   │   └── llm_fallback/         # Crawl4AI ノイズ除去 & Gemini API 抽出
│   └── scrapers/                 # 【アプリケーション層】Scrapy プロジェクト
│       └── scrapy_project/       # Spiders, Middlewares, Pipelines
│
├── tools/                        # 開発支援スクリプト群
│   ├── rule_generator/           # LLM を用いた XPath/CSS セレクタ自動生成ツール
│   └── local_tester.py           # ローカル Spider 単体実行スクリプト
│
├── pyproject.toml                # パッケージ・依存関係管理 (uv / ruff / pytest / mypy)
├── Dockerfile                    # スクレイパー実行用コンテナイメージ定義
├── ROADMAP.md                    # 実装ロードマップ
└── AGENTS.md                     # 開発・協業規約
```

---

## クイックスタート (ローカル開発)

### 1. 依存ツールの準備
- Python 3.11 以上
- [uv](https://github.com/astral-sh/uv) (推奨) または pip

### 2. 環境構築とローカルテスト
```bash
# 依存関係のインストール
uv pip install -e ".[dev]"

# 全テスト & リント検証
./scripts/verify-all.sh

# Spider のローカル単体実行テスト
python tools/local_tester.py equal_love
```

---

## 環境変数

| 環境変数 | デフォルト値 | 説明 |
| :--- | :--- | :--- |
| `MINIO_ENDPOINT` | `localhost:9000` | MinIO / S3 エンドポイント |
| `MINIO_BUCKET_NAME` | `lumiscrape-raw` | 生データ保存先バケット名 |
| `MINIO_ACCESS_KEY` | `minioadmin` | MinIO アクセスキー |
| `MINIO_SECRET_KEY` | `minioadmin` | MinIO シークレットキー |
| `DATABASE_URL` | `postgresql://lumiscrape:lumiscrape@localhost:5432/lumiscrape` | PostgreSQL 接続 DSN |
| `GEMINI_API_KEY` | `""` | LLM フォールバック & ルール生成用 API キー |
| `BROWSERLESS_URL` | `http://localhost:3000` | Browserless ヘッドレスブラウザ URL |

---

## 開発・コントリビューション規約

本プロジェクトのコード変更・PR 起票にあたっては、[AGENTS.md](AGENTS.md) を必ず遵守してください。

- **PR-Only 運用**: `main` ブランチへの直接作業は禁止。Git Worktree（`./scripts/worktree.sh`）を使用してトピックブランチで作業します。
- **CI-Green 原則**: コミット・Push 前に必ず `./scripts/verify-all.sh` をパスさせてください。

---

## ライセンス

[MIT License](LICENSE) (c) 2026 Aoba Iwaki
