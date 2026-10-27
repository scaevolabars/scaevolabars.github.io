#!/usr/bin/env bash
# Rebuild the font subsets in static/fonts/. Outputs are committed; run only to change them.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
out="$root/static/fonts"
src="https://raw.githubusercontent.com/google/fonts/main/ofl"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$out"

curl -fsSL "$src/literata/Literata%5Bopsz,wght%5D.ttf" -o "$tmp/literata.ttf"
curl -fsSL "$src/literata/Literata-Italic%5Bopsz,wght%5D.ttf" -o "$tmp/literata-italic.ttf"
curl -fsSL "$src/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf" -o "$tmp/jetbrains-mono.ttf"
curl -fsSL "$src/literata/OFL.txt" -o "$out/Literata-OFL.txt"
curl -fsSL "$src/jetbrainsmono/OFL.txt" -o "$out/JetBrainsMono-OFL.txt"

# Keep these ranges in sync with the unicode-range values in assets/css/main.css.
latin="U+0000-017F,U+0370-03FF,U+2000-206F,U+2070-209F,U+20AC,U+2100-214F,U+2190-21FF,U+2200-22FF,U+25A0-25FF,U+FFFD"
cyrillic="U+0400-045F,U+0490-0491,U+04B0-04B1,U+2116"
mono="U+0000-017F,U+0370-03FF,U+0400-045F,U+2000-206F,U+2070-209F,U+20AC,U+2190-21FF,U+2200-22FF,U+2500-257F,U+25A0-25FF"

subset() {
  uvx --from 'fonttools[woff]' pyftsubset "$1" --unicodes="$2" \
    --layout-features='*' --flavor=woff2 --output-file="$3"
}

subset "$tmp/literata.ttf" "$latin" "$out/literata.woff2"
subset "$tmp/literata.ttf" "$cyrillic" "$out/literata-cyrillic.woff2"
subset "$tmp/literata-italic.ttf" "$latin" "$out/literata-italic.woff2"
subset "$tmp/literata-italic.ttf" "$cyrillic" "$out/literata-italic-cyrillic.woff2"
subset "$tmp/jetbrains-mono.ttf" "$mono" "$out/jetbrains-mono.woff2"
ls -l "$out"
