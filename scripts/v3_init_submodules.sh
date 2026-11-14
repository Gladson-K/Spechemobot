#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

command -v git >/dev/null || { echo "git is required"; exit 1; }
[[ -f .gitmodules ]] || { echo ".gitmodules is missing at repo root"; exit 2; }
git rev-parse --is-inside-work-tree >/dev/null

# Git LFS is required by o3de-extras asset gems. Install it on the host first.
if command -v git-lfs >/dev/null 2>&1; then
  git lfs install --local >/dev/null 2>&1 || true
else
  echo "warning: git-lfs not found; O3DE asset gems may be incomplete"
fi

# Register each declared submodule as a gitlink. This is required when .gitmodules
# was delivered in a ZIP and the original gitlink entries are not present.
while IFS= read -r key; do
  name="${key#submodule.}"
  name="${name%.path}"
  path="$(git config -f .gitmodules --get "submodule.${name}.path")"
  url="$(git config -f .gitmodules --get "submodule.${name}.url")"
  if git ls-files --stage -- "$path" | grep -q '^160000 '; then
    echo "Already registered: $path"
  elif [[ -e "$path/.git" ]]; then
    echo "Directory already contains a git checkout: $path"
  else
    echo "Adding submodule: $path"
    mkdir -p "$(dirname "$path")"
    git submodule add --depth 1 "$url" "$path"
  fi
done < <(git config -f .gitmodules --name-only --get-regexp '^submodule\..*\.path$')

git submodule sync --recursive
git submodule update --init --recursive

if [[ -d third_party/o3de-extras/.git ]] && command -v git-lfs >/dev/null 2>&1; then
  git -C third_party/o3de-extras lfs install --local >/dev/null 2>&1 || true
  git -C third_party/o3de-extras lfs pull || true
fi

echo "Initialized submodules:"
git submodule status
