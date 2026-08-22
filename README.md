# lumiscrape

Thin, robust, and LLM-assisted web scraping and data integration platform.

[![CI](https://github.com/AobaIwaki123/lumiscrape/actions/workflows/ci.yml/badge.svg)](https://github.com/AobaIwaki123/lumiscrape/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 概要

`lumiscrape` は、任意の Web サイトに対する高速・堅牢なデータ収集・蓄積・構造化を実現するスクレイピング基盤です。

- **超軽量ランタイム**: Go 言語と標準ライブラリを中心に構成された低レイテンシ・省メモリな常駐スケジューラー。
- **データレイク中心設計**: 取得した生データ (HTML/JSON) を即座に gzip 圧縮し、MinIO (S3 互換ストレージ) に保存（7日間ライフサイクルルール自動適用）。
- **HTMX 管理画面**: JavaScript フレームワーク不要の超軽量 Web UI により、対象 URL の登録・スケジュール管理・リアルタイム死活監視を提供。
- **ルールベース高速パース**: Colly を用いた YAML 設定駆動の機械的パーサーにより、高スループットで構造化 JSON に変換。
- **LLM アシスト型チューニング**: Trafilatura によるノイズ除去と LLM（Gemini API 等）の構造化出力を活用し、抽出ルール（CSS/XPath セレクタ）をオフラインで自動生成。

詳細なアーキテクチャについては [docs/architecture.md](docs/architecture.md) を参照してください。

---

## クイックスタート (ローカル開発)

### 1. 依存ツールの準備
- Go 1.23 以上
- Python 3.11 以上 (ルール自動生成ツール用)
- Docker / Docker Compose (MinIO ローカル起動用)

### 2. ビルドと実行
```bash
# 全テスト & リント検証
./scripts/verify-all.sh

# Web 管理サーバーの起動
go run ./cmd/lumiscrape serve --port 8080
```

---

## ディレクトリ構成

```text
.
├── cmd/
│   └── lumiscrape/           # メイン CLI / サーバーエントリポイント
├── pkg/
│   ├── config/               # YAML 抽出ルール・アプリケーション設定
│   ├── scheduler/            # HTTP 取得・定期実行スケジューラー
│   ├── storage/              # MinIO / S3 クライアント (gzip 保存・ILM)
│   ├── parser/               # Colly 動的パーサーエンジン
│   ├── database/             # サイト登録・実行状態管理
│   └── web/                  # Go net/http + HTMX Web UI
├── tools/
│   └── rule-generator/       # Python + Trafilatura + LLM ルール生成 CLI
├── k8s/                      # Kubernetes & ArgoCD マニフェスト
├── docs/                     # アーキテクチャ・設計仕様書
└── scripts/                  # 検証・Worktree・リリース用スクリプト
```

---

## 環境変数

| 環境変数 | デフォルト値 | 説明 |
| :--- | :--- | :--- |
| `LUMISCRAPE_PORT` | `8080` | Web 管理画面のリッスンポート |
| `LUMISCRAPE_HOST` | `0.0.0.0` | リッスンホスト |
| `LUMISCRAPE_S3_ENDPOINT` | `localhost:9000` | MinIO / S3 エンドポイント |
| `LUMISCRAPE_S3_BUCKET` | `lumiscrape-raw` | 生データ保存先バケット名 |
| `LUMISCRAPE_S3_ACCESS_KEY`| `minioadmin` | S3 アクセスキー |
| `LUMISCRAPE_S3_SECRET_KEY`| `minioadmin` | S3 シークレットキー |
| `LUMISCRAPE_LOG_LEVEL` | `info` | ログレベル (`debug`, `info`, `warn`, `error`) |

---

## 開発・コントリビューション規約

本プロジェクトのコード変更・PR 起票にあたっては、[AGENTS.md](AGENTS.md) を必ず遵守してください。

- **PR-Only 運用**: `main` ブランチへの直接作業は禁止。Git Worktree（`./scripts/worktree.sh`）を使用してブランチ作業を実施します。
- **CI-Green 原則**: コミット・Push 前に必ず `./scripts/verify-all.sh` をパスさせてください。

---

## ライセンス

[MIT License](LICENSE) (c) 2026 Aoba Iwaki
