import re

import pytest

from helpers import ROOT

CSS = (ROOT / "assets" / "css" / "main.css").read_text(encoding="utf-8")

# Text colour on background colour. Muted text never sits on the grid band (4.29:1 in light).
PAIRS = [
    ("ink", "paper"), ("muted", "paper"), ("pencil", "paper"),
    ("ink", "code-bg"), ("muted", "code-bg"), ("pencil", "code-bg"),
    ("ink", "grid"), ("pencil", "grid"),
]


def tokens(scheme: str) -> dict[str, str]:
    block = re.search(rf"/\* tokens:{scheme} \*/(.*?)/\* end tokens \*/", CSS, re.S)
    assert block, f"main.css has no tokens:{scheme} block"
    return dict(re.findall(r"--([a-z-]+):\s*(#[0-9A-Fa-f]{6})", block.group(1)))


def luminance(color: str) -> float:
    channels = [int(color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(a: str, b: str) -> float:
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


@pytest.mark.parametrize("scheme", ["light", "dark"])
@pytest.mark.parametrize(("fg", "bg"), PAIRS)
def test_text_contrast_meets_wcag_aa(scheme: str, fg: str, bg: str) -> None:
    colors = tokens(scheme)
    assert contrast(colors[fg], colors[bg]) >= 4.5


def test_font_files_in_css_exist() -> None:
    urls = re.findall(r'url\("(/fonts/[^"]+)"\)', CSS)
    assert len(urls) == 5
    for url in urls:
        assert (ROOT / "static" / url.lstrip("/")).is_file(), url
