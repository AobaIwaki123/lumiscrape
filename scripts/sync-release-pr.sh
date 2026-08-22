#!/usr/bin/env bash
# ==============================================================================
# sync-release-pr.sh - Automated Release PR creator/updater (main -> release)
# ==============================================================================

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

echo "Fetching latest branches and tags..."
git fetch --tags origin main release || true

UNRELEASED_COMMITS=$(git log origin/release..origin/main --oneline --no-merges || true)

if [ -z "$UNRELEASED_COMMITS" ]; then
  echo "No unreleased commits found between origin/release and origin/main. Nothing to do."
  exit 0
fi

echo "Found unreleased commits:"
echo "$UNRELEASED_COMMITS"
echo ""

MERGED_PRS=$(git log origin/release..origin/main --merges --oneline | grep -oE '#[0-9]+' | sort -V -r -u || true)
RELEASE_NOTES_ITEMS=""
if [ -n "$MERGED_PRS" ]; then
  while read -r pr_ref; do
    if [ -n "$pr_ref" ]; then
      pr_num="${pr_ref#\#}"
      pr_title=""
      if command -v gh &>/dev/null; then
        pr_title=$(gh pr view "$pr_num" --json title --jq '.title' 2>/dev/null || true)
      fi
      if [ -n "$pr_title" ]; then
        RELEASE_NOTES_ITEMS="${RELEASE_NOTES_ITEMS}
- #${pr_num}: ${pr_title}"
      else
        RELEASE_NOTES_ITEMS="${RELEASE_NOTES_ITEMS}
- #${pr_num}"
      fi
    fi
  done <<< "$MERGED_PRS"
fi

if [ -z "$RELEASE_NOTES_ITEMS" ]; then
  RELEASE_NOTES_ITEMS=$(echo "$UNRELEASED_COMMITS" | sed 's/^/- /')
fi

DATE=$(date +%Y-%m-%d)
PREV_TAG=$(git tag -l 'v*' | sort -V | tail -n 1)
if [ -z "$PREV_TAG" ]; then
  PREV_TAG="v1.0.0"
fi
echo "Current highest version tag: ${PREV_TAG}"
CLEAN_VER=$(echo "$PREV_TAG" | sed -E 's/^(lumiscrape-)?v?//')
MAJOR=$(echo "$CLEAN_VER" | cut -d. -f1)
MINOR=$(echo "$CLEAN_VER" | cut -d. -f2)
NEXT_MINOR=$((MINOR + 1))
NEXT_TAG="v${MAJOR}.${NEXT_MINOR}.0"
echo "Calculated next release tag: ${NEXT_TAG}"

git config user.name "github-actions[bot]" 2>/dev/null || true
git config user.email "github-actions[bot]@users.noreply.github.com" 2>/dev/null || true

STAGE_BRANCH="release-stage/${NEXT_TAG}"
echo "Preparing staging branch: ${STAGE_BRANCH}..."

git checkout -B "$STAGE_BRANCH" origin/release

echo "Merging origin/main into staging branch..."
git merge -X theirs origin/main -m "chore: sync main into ${STAGE_BRANCH}"

echo "Updating Kubernetes manifests to release version ${NEXT_TAG} on ${STAGE_BRANCH}..."
if [[ -f "k8s/dashboard/deployment.yml" ]]; then
  sed -i.bak -E "s|(image: ghcr\.io/aobaiwaki123/lumiscrape:).*|\1${NEXT_TAG}|" k8s/dashboard/deployment.yml
  sed -i.bak -E "s|(value: \"ghcr\.io/aobaiwaki123/lumiscrape:).*|\1${NEXT_TAG}\"|" k8s/dashboard/deployment.yml
fi
if [[ -f "k8s/dashboard/kustomization.yml" ]]; then
  sed -i.bak -E "s/(newTag: ).*/\1${NEXT_TAG}/" k8s/dashboard/kustomization.yml
fi
rm -f k8s/dashboard/*.bak

git add k8s/dashboard/deployment.yml k8s/dashboard/kustomization.yml 2>/dev/null || true
if ! git diff --cached --quiet; then
  git commit -m "chore(release): bump k8s manifest image tag to ${NEXT_TAG}"
fi

echo "Pushing staging branch ${STAGE_BRANCH} to origin with retry..."
for attempt in 1 2 3; do
  if git push -u --force origin "$STAGE_BRANCH"; then
    break
  fi
  echo "Push failed on attempt $attempt, retrying in 2 seconds..."
  sleep 2
done

PR_TITLE="release: 本番リリース ${NEXT_TAG} (${DATE})"

PR_BODY="## 本番リリース PR: \`${STAGE_BRANCH}\` -> \`release\` (${NEXT_TAG})

本 PR は \`main\` ブランチの開発成果を取りまとめ、マニフェストタグを **${NEXT_TAG}** に更新して本番 \`release\` ブランチへ反映するための Release PR です。

### 含まれる変更・機能一覧
${RELEASE_NOTES_ITEMS}

### リリース後の自動実行項目
- [ ] 次期 Git リリースタグ (**${NEXT_TAG}**) の自動発行
- [ ] GitHub Release ノートの自動生成 & GoReleaser バイナリ配布
- [ ] GHCR へのマルチアーキテクチャ OCI コンテナイメージ (\`ghcr.io/aobaiwaki123/lumiscrape:${NEXT_TAG}\`) 自動 Push
- [ ] 自宅 Kubernetes クラスタ (ArgoCD) への自動同期 & ローリングアップデート
- [ ] 一時ステージングブランチ (\`${STAGE_BRANCH}\`) の自動削除"

EXISTING_PR=$(gh pr list --base release --head "$STAGE_BRANCH" --json number --jq '.[0].number' || true)

if [ -n "$EXISTING_PR" ]; then
  echo "Updating existing Release PR #${EXISTING_PR}..."
  gh pr edit "$EXISTING_PR" --title "$PR_TITLE" --body "$PR_BODY"
  echo "Successfully updated Release PR #${EXISTING_PR}."
else
  echo "Creating new Release PR from ${STAGE_BRANCH} to release..."
  gh pr create \
    --base release \
    --head "$STAGE_BRANCH" \
    --title "$PR_TITLE" \
    --body "$PR_BODY"
  echo "Successfully created Release PR."
fi
