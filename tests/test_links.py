from collections.abc import Iterator
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from bs4 import BeautifulSoup

LINK_ATTRS = {"a": "href", "link": "href", "script": "src", "img": "src", "source": "src"}


def internal_paths(site: Path) -> Iterator[tuple[Path, str]]:
    for html in site.rglob("*.html"):
        soup = BeautifulSoup(html.read_text(encoding="utf-8"), "html.parser")
        for tag, attr in LINK_ATTRS.items():
            for element in soup.find_all(tag):
                parts = urlsplit(element.get(attr) or "")
                if parts.scheme or parts.netloc or not parts.path:
                    continue  # external, mailto:, or a same-page #fragment
                yield html, parts.path


def resolve(site: Path, html: Path, path: str) -> Path:
    target = site / path.lstrip("/") if path.startswith("/") else html.parent / path
    return target / "index.html" if path.endswith("/") else target


@pytest.mark.parametrize("site_fixture", ["prod_site", "draft_site"])
def test_internal_links_resolve(site_fixture: str, request: pytest.FixtureRequest) -> None:
    site = request.getfixturevalue(site_fixture)
    broken = [
        (str(html.relative_to(site)), path)
        for html, path in internal_paths(site)
        if not resolve(site, html, path).exists()
    ]
    assert broken == []
