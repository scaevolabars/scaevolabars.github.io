import tomllib
from datetime import date
from pathlib import Path

import pytest
from bs4 import BeautifulSoup, Tag

from helpers import ROOT, clear_entries, copy_site, hugo_build, page, parse

CONFIG = tomllib.loads((ROOT / "hugo.toml").read_text(encoding="utf-8"))
BASE_URL = CONFIG["baseURL"]
NAV = ["Writing", "Notes", "Projects", "CV", "About"]
PAGES = ["/", "/posts/", "/notes/", "/about/", "/cv/", "/projects/", "/404.html"]
PROFILE = ["about/", "cv/", "projects/"]
SITES = ["prod_site", "draft_site"]
# Draft fixtures, newest first. Only --buildDrafts builds have them.
SAMPLES = {
    "posts": ["Sample post with every feature", "Sample post from an earlier year"],
    "notes": ["Sample note: Attention Is All You Need"],
}
BAD_FRONT_MATTER = {
    "unknown topic": ("title: Bad\ndate: 2026-01-01\ntopics: [astrology]\n", 'unknown topic "astrology"'),
    "topics not a list": ("title: Bad\ndate: 2026-01-01\ntopics: trading\n", "topics must be a list"),
    "no date": ("title: Bad\ntopics: [trading]\n", "the date is missing"),
    "empty title": ('title: ""\ndate: 2026-01-01\n', "the title is empty"),
}


def entries(soup: BeautifulSoup | Tag) -> list[tuple[date, str]]:
    """(date, title) of each entry in a list, in page order."""
    return [
        (date.fromisoformat(li.time["datetime"]), li.select_one(".entry__title").get_text())
        for li in soup.select("li.entry")
    ]


def in_order(titles: list[str], expected: list[str]) -> bool:
    """Whether the `expected` titles that appear in `titles` keep their relative order."""
    return [t for t in titles if t in expected] == [t for t in expected if t in titles]


def test_production_build_writes_home(prod_site: Path) -> None:
    assert (prod_site / "index.html").is_file()


@pytest.mark.parametrize("url", PAGES)
def test_page_has_nav_skip_link_and_stylesheet(prod_site: Path, url: str) -> None:
    soup = page(prod_site, url)
    assert [a.get_text(strip=True) for a in soup.select("nav.band__nav a")] == NAV
    assert soup.select_one("a.skip")["href"] == "#main"
    assert soup.select_one("main#main") is not None
    assert soup.select_one("link[rel=stylesheet][integrity]") is not None


@pytest.mark.parametrize("site_fixture", SITES)
def test_every_page_has_lang_one_h1_canonical_and_description(
    site_fixture: str, request: pytest.FixtureRequest
) -> None:
    site = request.getfixturevalue(site_fixture)
    for html in sorted(site.rglob("*.html")):
        name = str(html.relative_to(site))
        soup = parse(html)
        assert soup.html.get("lang"), name
        assert len(soup.find_all("h1")) == 1, name
        assert soup.select_one("meta[name=description]")["content"].strip(), name
        canonical = soup.select_one("link[rel=canonical]")
        if name == "404.html":
            assert canonical is None
        else:
            assert canonical["href"].startswith(BASE_URL), name


def test_nav_marks_current_section(draft_site: Path) -> None:
    archive = page(draft_site, "/posts/")
    assert archive.select_one("nav.band__nav a[aria-current=page]").get_text() == "Writing"
    post = page(draft_site, "/posts/sample-features/")
    assert post.select_one("nav.band__nav a[aria-current=true]").get_text() == "Writing"


def test_home_band_holds_name_and_intro(prod_site: Path) -> None:
    band = page(prod_site, "/").select_one("header.band--home")
    assert band.select_one("h1.band__title").get_text() == CONFIG["title"]
    assert band.select_one(".band__lede").get_text(strip=True)


def test_empty_states(empty_site: Path) -> None:
    empties = page(empty_site, "/").select("p.empty")
    assert len(empties) == 2
    assert empties[0].select_one('a[href="/index.xml"]') is not None
    for url in ("/posts/", "/notes/", "/topics/"):
        assert page(empty_site, url).select_one("p.empty") is not None, url


@pytest.mark.parametrize(("section", "limit"), [("posts", 5), ("notes", 3)])
def test_home_lists_the_newest_entries(draft_site: Path, section: str, limit: int) -> None:
    block = page(draft_site, "/").select_one(f"section[aria-labelledby=latest-{section}]")
    latest = entries(block)
    archive = entries(page(draft_site, f"/{section}/"))
    assert 0 < len(latest) == min(limit, len(archive))
    dates = [d for d, _ in latest]
    assert dates == sorted((d for d, _ in archive), reverse=True)[: len(latest)]
    titles = [t for _, t in latest]
    assert set(titles) <= {t for _, t in archive}
    assert in_order(titles, SAMPLES[section])
    for li in block.select("li.entry"):
        day = date.fromisoformat(li.time["datetime"])
        assert li.select_one(".entry__date").get_text() == day.strftime("%d %b %Y")


def test_home_shows_five_newest_posts_and_three_newest_notes(tmp_path: Path) -> None:
    src = copy_site(tmp_path / "src")
    clear_entries(src)
    days = {
        "posts": ["2024-03-01", "2025-11-30", "2023-07-15", "2025-01-02", "2024-12-31", "2022-05-05"],
        "notes": ["2023-02-02", "2025-06-06", "2024-04-04", "2022-01-01"],
    }
    for section, dates in days.items():
        for i, day in enumerate(dates):
            (src / "content" / section / f"entry-{i}.md").write_text(
                f'---\ntitle: "{section} {day}"\ndate: {day}\ntopics: [math]\n---\nText.\n',
                encoding="utf-8",
            )
    result = hugo_build(src, tmp_path / "out")
    assert result.returncode == 0, result.stderr + result.stdout
    home = page(tmp_path / "out", "/")
    for section, limit in (("posts", 5), ("notes", 3)):
        block = home.select_one(f"section[aria-labelledby=latest-{section}]")
        newest = sorted(days[section], reverse=True)[:limit]
        assert entries(block) == [(date.fromisoformat(d), f"{section} {d}") for d in newest]


@pytest.mark.parametrize("section", ["posts", "notes"])
def test_archive_groups_entries_by_year_newest_first(draft_site: Path, section: str) -> None:
    soup = page(draft_site, f"/{section}/")
    years = [h.get_text() for h in soup.select("h2.year__label")]
    assert years and years == sorted(set(years), reverse=True)
    for group in soup.select("section.year"):
        year = group.select_one("h2.year__label").get_text()
        for li in group.select("li.entry"):
            day = date.fromisoformat(li.time["datetime"])
            assert str(day.year) == year
            assert li.select_one(".entry__date").get_text() == day.strftime("%d %b")
    dates = [d for d, _ in entries(soup)]
    assert dates == sorted(dates, reverse=True)
    titles = [t for _, t in entries(soup)]
    assert set(SAMPLES[section]) <= set(titles)
    assert in_order(titles, SAMPLES[section])


def test_post_shows_date_and_topic_links(draft_site: Path) -> None:
    meta = page(draft_site, "/posts/sample-features/").select_one("p.meta")
    assert meta.select_one("time")["datetime"] == "2026-10-27"
    assert meta.select_one("time").get_text() == "27 October 2026"
    links = [(a.get_text(), a["href"]) for a in meta.select("a")]
    assert links == [("Trading systems", "/topics/trading/"), ("Low-latency C++/Rust", "/topics/low-latency/")]


def test_topic_page_uses_display_name(draft_site: Path) -> None:
    soup = page(draft_site, "/topics/low-latency/")
    assert soup.select_one("h1.page-title").get_text() == "Low-latency C++/Rust"
    assert soup.title.get_text() == "Low-latency C++/Rust | Sergey Bars"
    assert "Sample post with every feature" in soup.select_one(".entries").get_text()


def test_topic_index_counts_entries_with_a_label(draft_site: Path) -> None:
    items = page(draft_site, "/topics/").select(".topic-list li")
    assert items
    for li in items:
        count, label = li.select_one(".count").get_text().split(" ")
        assert label == ("entry" if count == "1" else "entries")
        assert int(count) == len(page(draft_site, li.a["href"]).select(".entries li"))


@pytest.mark.parametrize(("front_matter", "message"), BAD_FRONT_MATTER.values(), ids=BAD_FRONT_MATTER.keys())
def test_bad_front_matter_fails_the_build(tmp_path: Path, front_matter: str, message: str) -> None:
    src = copy_site(tmp_path / "src")
    (src / "content" / "posts" / "bad.md").write_text(f"---\n{front_matter}---\nText.\n", encoding="utf-8")
    result = hugo_build(src, tmp_path / "out")
    assert result.returncode != 0
    assert f"posts/bad.md: {message}" in result.stderr + result.stdout


def test_description_falls_back_to_summary(tmp_path: Path) -> None:
    src = copy_site(tmp_path / "src")
    (src / "content" / "posts" / "plain.md").write_text(
        "---\ntitle: Plain\ndate: 2026-01-02\n---\nNo description. It's about `vector<T>`.\n\nSecond paragraph.\n",
        encoding="utf-8",
    )
    result = hugo_build(src, tmp_path / "out")
    assert result.returncode == 0, result.stderr + result.stdout
    meta = page(tmp_path / "out", "/posts/plain/").select_one("meta[name=description]")
    assert meta["content"] == "No description. It’s about vector<T>. Second paragraph."


def test_prose_table_scrolls_in_a_focusable_region(tmp_path: Path) -> None:
    src = copy_site(tmp_path / "src")
    (src / "content" / "posts" / "table.md").write_text(
        "---\ntitle: Table\ndate: 2026-01-02\n---\n| Venue | Fills |\n|---|---:|\n| A | 1,204 |\n",
        encoding="utf-8",
    )
    result = hugo_build(src, tmp_path / "out")
    assert result.returncode == 0, result.stderr + result.stdout
    table = page(tmp_path / "out", "/posts/table/").select_one(".prose table")
    region = table.parent
    assert region.name == "div" and region["class"] == ["table-scroll"]
    assert region["role"] == "region" and region["tabindex"] == "0" and region["aria-label"] == "Table"
    # Hugo's alignment output survives the wrapper. --minify drops the space after the colon.
    assert [td.get("style", "").replace(" ", "") for td in table.select("tbody td")] == ["", "text-align:right"]


def test_note_shows_paper_reference(draft_site: Path) -> None:
    paper = page(draft_site, "/notes/sample-note/").select_one("p.paper")
    assert paper.select_one("a")["href"] == "https://arxiv.org/abs/1706.03762"
    assert paper.get_text() == "Notes on Attention Is All You Need, Vaswani et al. (2017)."


def test_drafts_are_not_published(prod_site: Path) -> None:
    for path in ("posts/sample-features", "posts/sample-older", "notes/sample-note"):
        assert not (prod_site / path).exists(), path
    for name in ("index.xml", "sitemap.xml", "index.html"):
        assert "sample-" not in (prod_site / name).read_text(encoding="utf-8"), name


def test_sitemap_lists_profile_pages(prod_site: Path) -> None:
    sitemap = (prod_site / "sitemap.xml").read_text(encoding="utf-8")
    for path in PROFILE:
        assert f"<loc>{BASE_URL}{path}</loc>" in sitemap, path


@pytest.mark.parametrize("site_fixture", SITES)
def test_lists_and_feeds_leave_out_profile_pages(site_fixture: str, request: pytest.FixtureRequest) -> None:
    site = request.getfixturevalue(site_fixture)
    for feed in site.rglob("*.xml"):
        if feed.name == "sitemap.xml":
            continue
        text = feed.read_text(encoding="utf-8")
        for path in PROFILE:
            assert f"{BASE_URL}{path}" not in text, (str(feed.relative_to(site)), path)
    profile = {f"/{path}" for path in PROFILE}
    for html in site.rglob("*.html"):
        links = {a["href"] for a in parse(html).select(".entries a, .topic-list a")}
        assert not links & profile, str(html.relative_to(site))


def test_robots_txt_points_to_sitemap(prod_site: Path) -> None:
    lines = (prod_site / "robots.txt").read_text(encoding="utf-8").splitlines()
    assert "User-agent: *" in lines
    assert f"Sitemap: {BASE_URL}sitemap.xml" in lines


def test_404_links_home_and_is_not_indexed(prod_site: Path) -> None:
    soup = page(prod_site, "/404.html")
    assert soup.select_one('.prose a[href="/"]') is not None
    assert soup.select_one("meta[name=robots]")["content"] == "noindex"
    assert soup.select_one("link[rel=canonical]") is None
    assert soup.select_one('meta[property="og:url"]') is None
