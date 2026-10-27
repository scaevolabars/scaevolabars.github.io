#!/usr/bin/env bash
# Fetch pinned third-party files into static/vendor/ (git-ignored).
# KaTeX CSS must match the KaTeX version inside Hugo: Hugo 0.166.0 bundles 0.18.4.
set -euo pipefail

KATEX_VERSION=0.18.4
KATEX_SHA256=0090b1ebccc77d1402ec95e85ee539e1da514d6cd6934156c00baf39dcb0e3aa
MERMAID_VERSION=12.2.0
MERMAID_SHA256=071914164d0f6d53e5c26a10a220230d4ae8d37ed0f2263fbf072266f0af3a0a

root="$(cd "$(dirname "$0")/.." && pwd)"
out="$root/static/vendor"
stamp="$out/.versions"
want="katex-$KATEX_VERSION mermaid-$MERMAID_VERSION"

if [[ -f "$stamp" && "$(cat "$stamp")" == "$want" ]]; then
  exit 0
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

fetch() {
  local name=$1 version=$2 sha=$3
  local tgz="$tmp/$name.tgz"
  curl -fsSL "https://registry.npmjs.org/$name/-/$name-$version.tgz" -o "$tgz"
  echo "$sha  $tgz" | shasum -a 256 -c - >/dev/null
  mkdir -p "$tmp/$name"
  tar -xzf "$tgz" -C "$tmp/$name"
}

fetch katex "$KATEX_VERSION" "$KATEX_SHA256"
fetch mermaid "$MERMAID_VERSION" "$MERMAID_SHA256"

rm -rf "$out"
mkdir -p "$out/katex/fonts" "$out/mermaid/chunks/mermaid.esm.min"
cp "$tmp/katex/package/dist/katex.min.css" "$out/katex/"
cp "$tmp/katex/package/dist/fonts/"*.woff2 "$out/katex/fonts/"
cp "$tmp/mermaid/package/dist/mermaid.esm.min.mjs" "$out/mermaid/"
cp "$tmp/mermaid/package/dist/chunks/mermaid.esm.min/"*.mjs "$out/mermaid/chunks/mermaid.esm.min/"
echo "$want" > "$stamp"
echo "vendor: $want"
