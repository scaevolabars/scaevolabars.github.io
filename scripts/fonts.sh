#!/usr/bin/env bash
# Rebuild the font subsets in static/fonts/. Outputs are committed; run only to change them.
# Run as `devbox run -- scripts/fonts.sh`: it needs the pinned uvx.
set -euo pipefail

GOOGLE_FONTS_REV=ddf386ba1b9fbc6b2c818f1ddcd9148f54ced94b
FONTTOOLS_VERSION=4.68.0
BROTLI_VERSION=1.2.1

root="$(cd "$(dirname "$0")/.." && pwd)"
out="$root/static/fonts"
src="https://raw.githubusercontent.com/google/fonts/$GOOGLE_FONTS_REV/ofl"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$out"

curl -fsSL "$src/literata/Literata%5Bopsz,wght%5D.ttf" -o "$tmp/literata.ttf"
curl -fsSL "$src/literata/Literata-Italic%5Bopsz,wght%5D.ttf" -o "$tmp/literata-italic.ttf"
curl -fsSL "$src/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf" -o "$tmp/jetbrains-mono.ttf"
curl -fsSL "$src/literata/OFL.txt" -o "$tmp/Literata-OFL.txt"
curl -fsSL "$src/jetbrainsmono/OFL.txt" -o "$tmp/JetBrainsMono-OFL.txt"

# Keep these ranges in sync with the unicode-range values in assets/css/main.css.
latin="U+0000-017F,U+0370-03FF,U+2000-206F,U+2070-209F,U+20AC,U+2100-214F,U+2190-21FF,U+2200-22FF,U+25A0-25FF,U+FFFD"
cyrillic="U+0400-045F,U+0490-0491,U+04B0-04B1"
mono="U+0000-017F,U+0370-03FF,U+0400-045F,U+2000-206F,U+2070-209F,U+20AC,U+2190-21FF,U+2200-22FF,U+2500-257F,U+25A0-25FF"

subset() {
  uvx --from "fonttools[woff]==$FONTTOOLS_VERSION" --with "brotli==$BROTLI_VERSION" \
    pyftsubset "$1" --unicodes="$2" --layout-features='*' --flavor=woff2 --output-file="$3"
}

subset "$tmp/literata.ttf" "$latin" "$out/literata.woff2"
subset "$tmp/literata.ttf" "$cyrillic" "$out/literata-cyrillic.woff2"
subset "$tmp/literata-italic.ttf" "$latin" "$out/literata-italic.woff2"
subset "$tmp/literata-italic.ttf" "$cyrillic" "$out/literata-italic-cyrillic.woff2"
subset "$tmp/jetbrains-mono.ttf" "$mono" "$out/jetbrains-mono.woff2"
cp "$tmp/Literata-OFL.txt" "$tmp/JetBrainsMono-OFL.txt" "$out/"
ls -l "$out"
