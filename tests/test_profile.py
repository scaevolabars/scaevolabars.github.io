import tomllib
from pathlib import Path

from helpers import ROOT, page

CONFIG = tomllib.loads((ROOT / "hugo.toml").read_text(encoding="utf-8"))


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
