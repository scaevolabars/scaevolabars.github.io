import re
from pathlib import Path

import pytest

from helpers import ROOT, page

CSS = (ROOT / "assets" / "css" / "main.css").read_text(encoding="utf-8")
FONTS_SH = (ROOT / "scripts" / "fonts.sh").read_text(encoding="utf-8")

FG, BG = {"ink", "muted", "pencil"}, {"paper", "code-bg", "grid"}
NEVER = {("muted", "grid")}  # 4.29:1 in light; muted never sits on the band
PAIRS = sorted((f, b) for f in FG for b in BG if (f, b) not in NEVER)

TOKEN_BLOCK = re.compile(r"/\* tokens:(\w+) \*/(.*?)/\* end tokens \*/", re.S)
CUSTOM_PROPERTY = re.compile(r"--([\w-]+)\s*:\s*([^;}]+)")
HEX6 = re.compile(r"#[0-9A-Fa-f]{6}")
COLOUR_LITERAL = re.compile(
    r"#[0-9A-Fa-f]{3,8}\b|\b(?:rgba?|hsla?|hwb|lab|lch|oklab|oklch|color|color-mix)\(", re.I
)
FONT_URL = re.compile(r'url\("(/fonts/[^"]+)"\)')


def tokens(scheme: str) -> dict[str, str]:
    """Every custom property in the scheme's token block. Each value must be #rrggbb."""
    blocks = dict(TOKEN_BLOCK.findall(CSS))
    assert scheme in blocks, f"main.css has no tokens:{scheme} block"
    found = {name: value.strip() for name, value in CUSTOM_PROPERTY.findall(blocks[scheme])}
    for name, value in found.items():
        assert HEX6.fullmatch(value), f"tokens:{scheme}: --{name} is {value!r}, not #rrggbb"
    return found


def luminance(color: str) -> float:
    channels = [int(color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(a: str, b: str) -> float:
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


@pytest.mark.parametrize("scheme", ["light", "dark"])
def test_scheme_defines_exactly_the_colour_tokens(scheme: str) -> None:
    assert set(tokens(scheme)) == FG | BG


@pytest.mark.parametrize("scheme", ["light", "dark"])
@pytest.mark.parametrize(("fg", "bg"), PAIRS)
def test_text_contrast_meets_wcag_aa(scheme: str, fg: str, bg: str) -> None:
    colors = tokens(scheme)
    assert contrast(colors[fg], colors[bg]) >= 4.5


def test_colours_are_set_only_in_token_blocks() -> None:
    # A colour token or a raw colour anywhere else would escape the contrast check.
    rest = TOKEN_BLOCK.sub("", CSS)
    assert COLOUR_LITERAL.findall(rest) == []


def test_font_files_in_css_exist() -> None:
    urls = FONT_URL.findall(CSS)
    assert len(urls) == 5
    for url in urls:
        assert (ROOT / "static" / url.lstrip("/")).is_file(), url


def test_preloaded_fonts_are_font_face_sources(prod_site: Path) -> None:
    preloads = [link["href"] for link in page(prod_site, "/").select('link[rel="preload"][as="font"]')]
    assert preloads
    assert set(preloads) <= set(FONT_URL.findall(CSS))


def ranges(text: str) -> list[str]:
    return [r.strip().upper() for r in text.split(",")]


def test_unicode_ranges_match_fonts_sh() -> None:
    variables = {name: ranges(value) for name, value in re.findall(r'^(\w+)="(U\+[^"]+)"$', FONTS_SH, re.M)}
    script = {file: variables[var] for var, file in re.findall(r'^subset "\S+" "\$(\w+)" "\$out/([\w.-]+)"$', FONTS_SH, re.M)}
    css = {}
    for face in re.findall(r"@font-face\s*\{(.*?)\}", CSS, re.S):
        file = FONT_URL.search(face).group(1).removeprefix("/fonts/")
        declared = re.search(r"unicode-range:\s*([^;]+);", face)
        css[file] = ranges(declared.group(1)) if declared else None
    assert script and css == script
