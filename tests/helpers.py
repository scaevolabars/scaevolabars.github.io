"""Shared helpers for the site tests."""

import subprocess
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent


def hugo_build(source: Path, dest: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    """Build the site at `source` into `dest` with the production flags."""
    return subprocess.run(
        ["hugo", "--gc", "--minify", "--panicOnWarning",
         "--source", str(source), "--destination", str(dest), *extra],
        capture_output=True,
        text=True,
        check=False,
    )


def page(site: Path, url: str) -> BeautifulSoup:
    """Parse the built file for a site URL such as "/posts/" or "/404.html"."""
    rel = url.lstrip("/")
    path = site / rel if rel.endswith(".html") else site / rel / "index.html"
    return BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
