from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest

from helpers import parse

LINK_ATTRS = {"a": "href", "link": "href", "script": "src", "img": "src", "source": "src"}


def resolve(site: Path, html: Path, path: str) -> Path | None:
    """The file inside `site` that a decoded link path names; a directory means its index.html."""
    target = (site / path.lstrip("/") if path.startswith("/") else html.parent / path).resolve()
    if target.is_dir():
        target = target / "index.html"
    return target if target.is_file() and target.is_relative_to(site) else None


def link_works(site: Path, html: Path, link: str, ids: dict[Path, set[str]]) -> bool:
    parts = urlsplit(link)
    if not link or "ZgotmplZ" in link:
        return False  # empty, or a URL that Go templates replaced because it was unsafe
    if parts.scheme or parts.netloc:
        return True  # external or mailto:; not checked
    target = resolve(site, html, unquote(parts.path)) if parts.path else html
    if target is None:
        return False
    fragment = unquote(parts.fragment)
    if not fragment or fragment.lower() == "top" or target.suffix != ".html":
        return True  # "#top" means the top of the page in HTML
    return fragment in ids.get(target, set())  # .get: a case-insensitive disk finds /DOCS/ but the key is /docs/


def broken_links(site: Path) -> list[tuple[str, str]]:
    """(page, link) for each empty link, missing file and missing #id in the built site."""
    site = site.resolve()
    soups = {html: parse(html) for html in site.rglob("*.html")}
    ids = {html: {e["id"] for e in soup.find_all(id=True)} for html, soup in soups.items()}
    return sorted(
        (str(html.relative_to(site)), element[attr])
        for html, soup in soups.items()
        for tag, attr in LINK_ATTRS.items()
        for element in soup.find_all(tag, attrs={attr: True})
        if not link_works(site, html, element[attr].strip(), ids)
    )


@pytest.mark.parametrize("site_fixture", ["prod_site", "draft_site"])
def test_internal_links_resolve(site_fixture: str, request: pytest.FixtureRequest) -> None:
    assert broken_links(request.getfixturevalue(site_fixture)) == []


def test_link_check_finds_each_kind_of_broken_link(tmp_path: Path) -> None:
    site = tmp_path / "site"
    (site / "docs").mkdir(parents=True)
    (site / "docs" / "my file.txt").write_text("text", encoding="utf-8")
    (site / "docs" / "index.html").write_text('<h2 id="setup">Setup</h2>', encoding="utf-8")
    (tmp_path / "outside.html").write_text("", encoding="utf-8")
    good = ["/docs/my%20file.txt", "/docs/#setup", "docs", "docs/index.html#setup", "#main", "#top", "https://example.com/x"]
    # /DOCS/ is a different path on the server; on a case-insensitive disk it must still not crash the check.
    bad = ["", "#ZgotmplZ", "/docs/#install", "#nowhere", "/missing/", "/docs/my file.pdf", "../outside.html", "/DOCS/#setup"]
    links = "".join(f'<a href="{link}">x</a>' for link in good + bad)
    (site / "index.html").write_text(f'<main id="main">{links}<a href>x</a></main>', encoding="utf-8")
    assert broken_links(site) == sorted([("index.html", link) for link in bad] + [("index.html", "")])
