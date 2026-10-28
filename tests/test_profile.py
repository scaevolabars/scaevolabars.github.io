import re
import subprocess
import tomllib
from pathlib import Path

import pytest

from helpers import ROOT, copy_site, hugo_build, page

CONFIG = tomllib.loads((ROOT / "hugo.toml").read_text(encoding="utf-8"))

# Fixture data, so the structure tests do not depend on the owner's CV and projects.
CV_YAML = """\
pdf: ""
sections:
  - title: Experience
    entries:
      - when: "2021 – now"
        what: Engineer
        where: Acme
        text: "First paragraph.\\n\\nSecond paragraph."
      - when: "2019 – 2021"
        what: Intern
        where: ""
        text: ""
  - title: Skills
    entries:
      - when: Languages
        what: "C++, Rust"
"""
PROJECTS_YAML = """\
- name: Alpha
  year: 2026
  text: "What Alpha does."
  links:
    - label: Code
      url: "https://github.com/example/alpha"
    - label: Notes
      url: "/notes/"
- name: Beta
  year: 2025
  text: "What Beta does."
"""
BAD_DATA = {
    "cv without sections": ("cv.yaml", 'pdf: ""\nsections: []\n', 'data/cv.yaml: "sections" must be a non-empty list'),
    "cv entry without what": (
        "cv.yaml",
        "sections:\n  - title: Experience\n    entries:\n      - when: 2020\n",
        'data/cv.yaml: section "Experience", entry 1 needs "when" and "what"',
    ),
    "project link typo": (
        "projects.yaml",
        "- name: Alpha\n  text: Text.\n  links:\n    - label: Code\n      ulr: https://example.com\n",
        'data/projects.yaml: project "Alpha", link 1 needs a "label" and a "url" that starts with https:// or /',
    ),
    "project link not https": (
        "projects.yaml",
        "- name: Alpha\n  text: Text.\n  links:\n    - label: Code\n      url: http://example.com\n",
        'data/projects.yaml: project "Alpha", link 1 needs a "label" and a "url" that starts with https:// or /',
    ),
    "project link protocol-relative": (
        "projects.yaml",
        "- name: Alpha\n  text: Text.\n  links:\n    - label: Code\n      url: //example.com\n",
        'data/projects.yaml: project "Alpha", link 1 needs a "label" and a "url" that starts with https:// or /',
    ),
    "project links not a list": (
        "projects.yaml",
        "- name: Alpha\n  text: Text.\n  links: https://example.com\n",
        'data/projects.yaml: project "Alpha": "links" must be a list',
    ),
    "project name is a number": ("projects.yaml", "- name: 2048\n", 'data/projects.yaml: project "2048" needs "name" and "text"'),
    "cv section without title": (
        "cv.yaml",
        "sections:\n  - entries:\n      - when: 2020\n        what: Engineer\n",
        'data/cv.yaml: section 1 needs a "title" and a non-empty "entries" list',
    ),
}


@pytest.fixture(scope="module")
def fixture_site(tmp_path_factory: pytest.TempPathFactory) -> Path:
    src = copy_site(tmp_path_factory.mktemp("profile-src"))
    (src / "data" / "cv.yaml").write_text(CV_YAML, encoding="utf-8")
    (src / "data" / "projects.yaml").write_text(PROJECTS_YAML, encoding="utf-8")
    dest = tmp_path_factory.mktemp("profile")
    result = hugo_build(src, dest)
    assert result.returncode == 0, result.stderr + result.stdout
    return dest


@pytest.fixture(scope="module")
def front_matter(tmp_path_factory: pytest.TempPathFactory) -> dict[str, dict]:
    """Front matter of the profile pages. Hugo parses it (any YAML style) and writes TOML for tomllib."""
    out = tmp_path_factory.mktemp("toml")
    subprocess.run(
        ["hugo", "convert", "toTOML", "--source", str(ROOT), "--output", str(out)],
        check=True, capture_output=True, text=True,
    )
    pages = {}
    for name in ("about", "cv", "projects"):
        text = (out / "content" / f"{name}.md").read_text(encoding="utf-8")
        pages[name] = tomllib.loads(re.match(r"\+\+\+\n(.*?)\n\+\+\+\n", text, re.DOTALL).group(1))
    return pages


@pytest.mark.parametrize("name", ["about", "cv", "projects"])
def test_profile_page_uses_front_matter_description(
    prod_site: Path, front_matter: dict[str, dict], name: str
) -> None:
    # The summary fallback would mix headings, print-only links and list items into one line.
    description = front_matter[name].get("description", "").strip()
    assert description, f"content/{name}.md needs a description"
    assert page(prod_site, f"/{name}/").select_one("meta[name=description]")["content"] == description


def test_cv_renders_sections_from_data(fixture_site: Path) -> None:
    cv = page(fixture_site, "/cv/").select_one(".prose > .cv")
    assert [h.get_text() for h in cv.select(":scope > .cv-section > h2")] == ["Experience", "Skills"]
    assert [dt.get_text() for dt in cv.select(".cv-section > dl.cv-list > dt")] == ["2021 – now", "2019 – 2021", "Languages"]
    first, second, third = cv.select(".cv-list > dd")
    assert first.select_one(".cv-what").get_text() == "Engineer"
    assert ", Acme" in first.get_text()
    assert [p.get_text() for p in first.select("div.cv-text > p")] == ["First paragraph.", "Second paragraph."]
    assert second.get_text() == "Intern" and second.select_one(".cv-text") is None
    assert third.get_text() == "C++, Rust"


def test_projects_render_from_data(fixture_site: Path) -> None:
    projects = page(fixture_site, "/projects/").select("section.project")
    names = [p.select_one("h2.project__name").find(string=True, recursive=False).strip() for p in projects]
    assert names == ["Alpha", "Beta"]
    assert projects[0].select_one("p").get_text() == "What Alpha does."
    links = [(a.get_text(), a["href"]) for a in projects[0].select(".project__links a")]
    assert links == [("Code", "https://github.com/example/alpha"), ("Notes", "/notes/")]
    assert projects[1].select_one(".project__links") is None


def test_real_profile_data_renders(prod_site: Path) -> None:
    # The build checks the data, so only what holds for any valid data files is asserted here.
    sections = page(prod_site, "/cv/").select(".cv > .cv-section")
    assert sections
    for section in sections:
        assert section.select_one("h2").get_text(strip=True)
        assert len(section.select("dt")) == len(section.select("dd")) > 0
    projects = page(prod_site, "/projects/").select("section.project")
    assert projects and all(p.select_one("h2.project__name").get_text(strip=True) for p in projects)


@pytest.mark.parametrize(("file", "data", "message"), BAD_DATA.values(), ids=BAD_DATA.keys())
def test_bad_profile_data_fails_the_build(tmp_path: Path, file: str, data: str, message: str) -> None:
    src = copy_site(tmp_path / "src")
    (src / "data" / file).write_text(data, encoding="utf-8")
    result = hugo_build(src, tmp_path / "out")
    assert result.returncode != 0
    output = result.stderr + result.stdout
    assert message in output
    assert "%!" not in output  # no broken printf verbs


def test_printed_cv_shows_site_and_github_addresses(prod_site: Path) -> None:
    # Print hides the footer, so the CV lists the addresses as visible text, one per item like the footer.
    items = page(prod_site, "/cv/").select("ul.cv-contact > li")
    links = [li.select_one("a") for li in items]
    assert [a["href"] for a in links] == [CONFIG["baseURL"], f"https://github.com/{CONFIG['params']['github']}"]
    for li, a in zip(items, links):
        assert li.get_text() == a.get_text() == a["href"].removeprefix("https://").rstrip("/")
