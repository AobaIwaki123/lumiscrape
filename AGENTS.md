# lumiscrape 開発・協業規約 (AGENTS.md)

本ドキュメントは、AIエージェントおよび開発者が `lumiscrape` リポジトリで作業する際の共通規約を定義します。

---

## 1. Git & Pull Request & Worktree 運用ルール

- **`main` ブランチへの直接コミットおよび直接 Push は禁止**します。
- **すべてのタスク作業は Git Worktree（`.worktrees/<branch-name>`）を作成して行います**。ルート作業領域（`main` 等）での直接作業は禁止します（`./scripts/worktree.sh create <branch-name>` を活用）。
- **PR の単一責務の原則 (Single Responsibility PR)**: 各 PR は単一の明確な目的（バグ修正、機能追加、テスト追加、ドキュメント更新、CI/CD設定等）に限定し、無関係な変更の混在を禁止します。独立した改善は別ブランチを切って別 PR として起票します。
- **PR タイトルは、リリースノートだけを見て何をやったかが一目で分かるように、具体的かつ明瞭な日本語で記述します**（例: `feat: Scrapy 用 MinIO Gzip 保存ミドルウェアの実装`, `feat: Crawl4AI と Gemini API による LLM フォールバック基盤の構築`）。
- 複数ステップの開発を行う場合は、親ブランチからの Stacked PR（積み上げ型 PR）として作成します。
- **エージェントによる PR の自律的なマージ・クローズは禁止**します。PR 作成と CI（Lint / Test / TypeCheck）の通過確認までを作業範囲とし、マージはユーザーのレビュー・判断に委ねます。

---

## 2. アーキテクチャとコード規約 (Clean Architecture 準拠)

- **依存の方向の一方向性**:
  - `src/core/` (ドメイン層): Pydantic モデルや共通例外を定義。外部モジュールに依存してはならない。
  - `src/infrastructure/` (インフラ層): MinIO、PostgreSQL、LLM フォールバック (Crawl4AI / Gemini API) との通信を担当。
  - `src/scrapers/` (アプリケーション層): Scrapy Spider、Middleware、Pipeline を配置。インフラ層およびドメイン層を呼び出す。
- **型安全性の徹底**:
  - すべての関数・メソッドに適切な型ヒント（Type Annotation）を付与し、MyPy 厳格モード（`strict = true`）をパスさせます。
- **Scrapy と外部ロジックの隔離**:
  - Spider 内に複雑な DB ロジックやストレージ保存処理を直接記述せず、必ず `middlewares.py` や `pipelines.py` を介してインフラ層（`infrastructure/`）を呼び出します。

---

## 3. ドキュメント規約

- README、ROADMAP、設計仕様書などの公式ドキュメントでは、**原則として絵文字（emoji）を使用しません**。
- 清潔でプロフェッショナルな Markdown 記述を徹底します。
- **Mermaid 構文エラーの撲滅**:
  - Mermaid 図を作成・更新する際は、ノードラベル、エッジテキスト（`-->|"..."|`）、SequenceDiagram の participant 名・Note 本文に含まれる特殊文字（`{`, `}`, `(`, `)`, `#`, `/`, `.`, `-` 等）を **必ずダブルクォート (`"..."`) でエスケープ・クォート** します。
  - 作成・編集後は、GitHub Markdown レンダラーで構文エラー（Parse error）が発生しないか **必ずセルフレビュー（Double-Check）** を実施します。

---

## 4. 品質基準 (Quality Gate) & CI-Green 原則

- **CI が通るまで絶対にマージしない**:
  - すべての PR は、GitHub Actions CI（`ruff check`, `ruff format`, `mypy`, `pytest`）が 100% PASS (Green) することを確認するまで、**絶対にマージを行ってはなりません**。
  - CI が `pending`（実行中）または `failure`（失敗）の状態でのマージは例外なく禁止します。
- コミット・Push 前に必ず `./scripts/verify-all.sh` をローカルで実行し、事前検証を徹底します。
