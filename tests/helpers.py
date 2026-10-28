"""Shared helpers for the site tests."""

import shutil
import subprocess
import tomllib
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
CONFIG = tomllib.loads((ROOT / "hugo.toml").read_text(encoding="utf-8"))

# What Hugo needs to build the site. Templates only name static files, so static/ stays out.
SITE_SOURCES = ["hugo.toml", "archetypes", "assets", "content", "data", "layouts"]

# The YAML between the --- lines of the post that build_post adds.
POST_FRONT_MATTER = "title: Test\ndate: 2026-01-02\ndescription: Test post.\n"


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


def build_post(
    tmp_path: Path, body: str, front_matter: str = POST_FRONT_MATTER, site: Path | None = None
) -> tuple[subprocess.CompletedProcess[str], Path]:
    """Build a copy of the site with one extra post, /posts/test-post/, into tmp_path / "out".

    Pass `site` to build a copy that the test changed first. Returns the Hugo result and the output dir.
    """
    site = site or copy_site(tmp_path / "src")
    (site / "content" / "posts" / "test-post.md").write_text(f"---\n{front_matter}---\n\n{body}\n", encoding="utf-8")
    out = tmp_path / "out"
    return hugo_build(site, out), out


def clear_entries(site: Path) -> None:
    """Delete every post and note in a copied site. The section pages stay."""
    for section in ("posts", "notes"):
        for entry in (site / "content" / section).iterdir():
            if entry.name == "_index.md":
                continue
            if entry.is_dir():
                shutil.rmtree(entry)
            else:
                entry.unlink()


def parse(path: Path) -> BeautifulSoup:
    return BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")


def page(site: Path, url: str) -> BeautifulSoup:
    """Parse the built file for a site URL such as "/posts/" or "/404.html"."""
    rel = url.lstrip("/")
    return parse(site / rel if rel.endswith(".html") else site / rel / "index.html")
