import re
import tomllib
from pathlib import Path

import pytest

from helpers import ROOT, page

CONFIG = tomllib.loads((ROOT / "hugo.toml").read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", ["about", "cv", "projects"])
def test_profile_page_uses_front_matter_description(prod_site: Path, name: str) -> None:
    # The summary fallback would mix headings, print-only links and list items into one line.
    source = (ROOT / "content" / f"{name}.md").read_text(encoding="utf-8")
    front_matter = source.split("---")[1]
    description = re.search(r'^description: "(.+)"$', front_matter, re.MULTILINE)
    assert description, f"content/{name}.md needs a description"
    meta = page(prod_site, f"/{name}/").select_one("meta[name=description]")
    assert meta["content"] == description.group(1)


def test_cv_renders_sections_from_data(prod_site: Path) -> None:
    soup = page(prod_site, "/cv/")
    assert [h.get_text() for h in soup.select(".cv-section h2")] == ["Experience", "Education", "Skills"]
    assert soup.select(".cv-list dt") and soup.select(".cv-list dd .cv-what")


def test_printed_cv_shows_site_and_github_addresses(prod_site: Path) -> None:
    # Print hides the footer, so the CV carries the addresses as visible text.
    contact = page(prod_site, "/cv/").select_one("p.cv-contact")
    links = contact.select("a")
    assert [a["href"] for a in links] == [CONFIG["baseURL"], f"https://github.com/{CONFIG['params']['github']}"]
    for a in links:
        assert a.get_text() == a["href"].removeprefix("https://").rstrip("/")


def test_projects_render_from_data(prod_site: Path) -> None:
    project = page(prod_site, "/projects/").select_one("section.project")
    assert project.select_one("h2.project__name") is not None
    assert project.select_one(".project__links a")["href"].startswith("https://")
