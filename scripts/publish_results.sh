#!/bin/bash
# Copy a results folder into the `ci-results` branch (so logs and pictures can be read without the Actions UI).
#   scripts/publish_results.sh <source dir> <destination path in ci-results> "<commit message>"
set -eo pipefail
SRC=$(realpath "$1"); DEST=$2; MSG=$3
URL="https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_REPOSITORY}.git"
W=$(mktemp -d)
if git ls-remote --exit-code --heads "$URL" ci-results > /dev/null 2>&1; then
  git clone -q --depth 1 --branch ci-results "$URL" "$W"
else
  git -C "$W" init -q; git -C "$W" checkout -q -b ci-results; git -C "$W" remote add origin "$URL"
fi
{ echo "commit: ${GITHUB_SHA}"; echo "run: ${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID}"; date -u; } > "$SRC/RUN_INFO.txt"
for i in 1 2 3 4 5 6; do
  rm -rf "$W/$DEST"; mkdir -p "$W/$DEST"; cp -r "$SRC/." "$W/$DEST/"
  git -C "$W" add -A
  git -C "$W" -c user.name=github-actions -c user.email=actions@github.com commit -q -m "$MSG" || true
  if git -C "$W" push -q origin ci-results; then echo "published to ci-results/$DEST"; exit 0; fi
  sleep $((RANDOM % 15 + 5))
  git -C "$W" fetch -q --depth 1 origin ci-results && git -C "$W" reset -q --hard FETCH_HEAD
done
echo "could not publish"; exit 1
