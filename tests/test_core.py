import shutil
from pathlib import Path

import pytest

from helpers import ROOT, hugo_build, page

NAV = ["Writing", "Notes", "Projects", "CV", "About"]
PAGES = ["/", "/posts/", "/notes/", "/about/", "/cv/", "/projects/", "/404.html"]
COPY_IGNORE = shutil.ignore_patterns(
    ".git", ".devbox", ".venv", "public", "resources", ".pytest_cache", "__pycache__"
)


def test_production_build_writes_home(prod_site: Path) -> None:
    assert (prod_site / "index.html").is_file()


@pytest.mark.parametrize("url", PAGES)
def test_page_has_nav_skip_link_and_stylesheet(prod_site: Path, url: str) -> None:
    soup = page(prod_site, url)
    assert [a.get_text(strip=True) for a in soup.select("nav.band__nav a")] == NAV
    assert soup.select_one("a.skip")["href"] == "#main"
    assert soup.select_one("main#main") is not None
    assert soup.select_one("link[rel=stylesheet][integrity]") is not None


def test_nav_marks_current_section(draft_site: Path) -> None:
    archive = page(draft_site, "/posts/")
    assert archive.select_one("nav.band__nav a[aria-current=page]").get_text() == "Writing"
    post = page(draft_site, "/posts/sample-features/")
    assert post.select_one("nav.band__nav a[aria-current=true]").get_text() == "Writing"


def test_home_band_holds_name_and_intro(prod_site: Path) -> None:
    band = page(prod_site, "/").select_one("header.band--home")
    assert band.select_one("h1.band__title").get_text() == "Sergey Bars"
    assert "trading systems" in band.select_one(".band__lede").get_text()


def test_home_shows_empty_state_without_entries(prod_site: Path) -> None:
    empties = page(prod_site, "/").select("p.empty")
    assert len(empties) == 2
    assert empties[0].select_one('a[href="/index.xml"]') is not None


def test_home_lists_latest_posts_and_notes(draft_site: Path) -> None:
    soup = page(draft_site, "/")
    posts = [a.get_text() for a in soup.select("section[aria-labelledby=latest-posts] .entry__title")]
    assert posts == ["Sample post with every feature", "Sample post from an earlier year"]
    notes = [a.get_text() for a in soup.select("section[aria-labelledby=latest-notes] .entry__title")]
    assert notes == ["Sample note: Attention Is All You Need"]


def test_archive_groups_posts_by_year_newest_first(draft_site: Path) -> None:
    soup = page(draft_site, "/posts/")
    assert [h.get_text() for h in soup.select("h2.year__label")] == ["2026", "2025"]
    assert soup.select("section.year")[0].select_one(".entry__date").get_text() == "27 Oct"


def test_post_shows_date_and_topic_links(draft_site: Path) -> None:
    meta = page(draft_site, "/posts/sample-features/").select_one("p.meta")
    assert meta.select_one("time")["datetime"] == "2026-10-27"
    assert meta.select_one("time").get_text() == "27 October 2026"
    links = {a.get_text(): a["href"] for a in meta.select("a")}
    assert links == {"Trading systems": "/topics/trading/", "Low-latency C++/Rust": "/topics/low-latency/"}


def test_topic_page_uses_display_name(draft_site: Path) -> None:
    soup = page(draft_site, "/topics/low-latency/")
    assert soup.select_one("h1.page-title").get_text() == "Low-latency C++/Rust"
    assert soup.title.get_text() == "Low-latency C++/Rust | Sergey Bars"
    assert "Sample post with every feature" in soup.select_one(".entries").get_text()


def test_unknown_topic_fails_the_build(tmp_path: Path) -> None:
    src = tmp_path / "src"
    shutil.copytree(ROOT, src, ignore=COPY_IGNORE)
    (src / "content" / "posts" / "bad-topic.md").write_text(
        "---\ntitle: Bad topic\ndate: 2026-01-01\ntopics: [astrology]\n---\nText.\n",
        encoding="utf-8",
    )
    result = hugo_build(src, tmp_path / "out")
    assert result.returncode != 0
    assert 'unknown topic "astrology"' in result.stderr + result.stdout


def test_note_shows_paper_reference(draft_site: Path) -> None:
    paper = page(draft_site, "/notes/sample-note/").select_one("p.paper")
    assert paper.select_one("a")["href"] == "https://arxiv.org/abs/1706.03762"
    assert paper.get_text() == "Notes on Attention Is All You Need, Vaswani et al. (2017)."


def test_drafts_are_not_published(prod_site: Path) -> None:
    assert not (prod_site / "posts" / "sample-features").exists()
    assert not (prod_site / "notes" / "sample-note").exists()


def test_404_links_home(prod_site: Path) -> None:
    assert page(prod_site, "/404.html").select_one('.prose a[href="/"]') is not None
