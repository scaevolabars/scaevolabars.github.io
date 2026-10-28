from pathlib import Path

import pytest

from helpers import copy_site, hugo_build


def placeholder_hits(site: Path) -> list[str]:
    """Built files, relative to `site`, that still contain PLACEHOLDER text.

    Every file counts (pages, feeds, sitemap) except the third-party files in vendor/.
    """
    return sorted(
        str(rel)
        for path in site.rglob("*")
        if path.is_file()
        and (rel := path.relative_to(site)).parts[0] != "vendor"
        and b"PLACEHOLDER" in path.read_bytes()
    )


@pytest.mark.content
def test_no_placeholder_text_is_published(prod_site: Path) -> None:
    hits = placeholder_hits(prod_site)
    assert hits == [], f"Replace the PLACEHOLDER text in content/ and data/ before you publish: {hits}"


def test_placeholder_scan_finds_feed_only_text(tmp_path: Path) -> None:
    # A summary goes only into the feeds when the post has its own description.
    src = copy_site(tmp_path / "src")
    (src / "content" / "posts" / "feed-only.md").write_text(
        "---\ntitle: Feed only\ndate: 2026-01-02\ntopics: [math]\n"
        'description: "A real description."\nsummary: "PLACEHOLDER: one sentence for the feed."\n---\nText.\n',
        encoding="utf-8",
    )
    result = hugo_build(src, tmp_path / "out")
    assert result.returncode == 0, result.stderr + result.stdout
    hits = placeholder_hits(tmp_path / "out")
    assert {"index.xml", "posts/index.xml", "topics/math/index.xml"} <= set(hits), hits
