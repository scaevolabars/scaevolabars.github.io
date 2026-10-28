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
# The stamp stays out of static/: Hugo publishes dotfiles from there.
stamp="$root/.vendor-stamp"
want="katex-$KATEX_VERSION mermaid-$MERMAID_VERSION"

if [[ -f "$stamp" && "$(cat "$stamp")" == "$want" &&
      -f "$out/katex/katex.min.css" && -f "$out/mermaid/mermaid.esm.min.mjs" ]]; then
  exit 0
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

sha256() {
  if command -v sha256sum >/dev/null; then sha256sum "$1"; else shasum -a 256 "$1"; fi | cut -d' ' -f1
}

fetch() {
  local name=$1 version=$2 sha=$3
  local tgz="$tmp/$name.tgz"
  curl -fsSL --retry 3 --retry-connrefused "https://registry.npmjs.org/$name/-/$name-$version.tgz" -o "$tgz"
  if [[ "$(sha256 "$tgz")" != "$sha" ]]; then
    echo "vendor: $name $version checksum mismatch" >&2
    exit 1
  fi
  mkdir -p "$tmp/$name"
  tar -xzf "$tgz" -C "$tmp/$name"
}

fetch katex "$KATEX_VERSION" "$KATEX_SHA256"
fetch mermaid "$MERMAID_VERSION" "$MERMAID_SHA256"

rm -rf "$out" "$stamp"
mkdir -p "$out/katex/fonts" "$out/mermaid/chunks/mermaid.esm.min"
cp "$tmp/katex/package/dist/katex.min.css" "$out/katex/"
cp "$tmp/katex/package/dist/fonts/"*.woff2 "$out/katex/fonts/"
cp "$tmp/mermaid/package/dist/mermaid.esm.min.mjs" "$out/mermaid/"
cp "$tmp/mermaid/package/dist/chunks/mermaid.esm.min/"*.mjs "$out/mermaid/chunks/mermaid.esm.min/"
echo "$want" > "$stamp"
echo "vendor: $want"
