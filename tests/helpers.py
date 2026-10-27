"""Shared helpers for the site tests."""

import shutil
import subprocess
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent

# What Hugo needs to build the site. Templates only name static files, so static/ stays out.
SITE_SOURCES = ["hugo.toml", "archetypes", "assets", "content", "data", "layouts"]


def hugo_build(source: Path, dest: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    """Build the site at `source` into `dest` with the production flags."""
    return subprocess.run(
        ["hugo", "--gc", "--minify", "--panicOnWarning",
         "--source", str(source), "--destination", str(dest), *extra],
        capture_output=True,
        text=True,
        check=False,
    )


def copy_site(dest: Path) -> Path:
    """Copy the site sources into `dest`, so a test can change them and build."""
    dest.mkdir(parents=True, exist_ok=True)
    for name in SITE_SOURCES:
        src = ROOT / name
        if src.is_dir():
            shutil.copytree(src, dest / name)
        elif src.is_file():
            shutil.copy2(src, dest / name)
    return dest


def parse(path: Path) -> BeautifulSoup:
    return BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")


def page(site: Path, url: str) -> BeautifulSoup:
    """Parse the built file for a site URL such as "/posts/" or "/404.html"."""
    rel = url.lstrip("/")
    return parse(site / rel if rel.endswith(".html") else site / rel / "index.html")
