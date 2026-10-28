from pathlib import Path

import pytest

from helpers import build_post


def placeholder_hits(site: Path) -> list[str]:
    """Built files (pages, feeds, sitemap), relative to `site`, that still contain template text.

    Every placeholder starts "PLACEHOLDER:".
    """
    return sorted(
        str(rel)
        for path in site.rglob("*")
        if path.is_file()
        # vendor/ holds the KaTeX and Mermaid files from npm, not our text.
        and (rel := path.relative_to(site)).parts[0] != "vendor"
        and b"PLACEHOLDER:" in path.read_bytes()
    )


@pytest.mark.content
def test_no_placeholder_text_is_published(prod_site: Path) -> None:
    hits = placeholder_hits(prod_site)
    assert hits == [], (
        "Replace the PLACEHOLDER: text in content/ and data/ before you publish "
        f"(grep -rn 'PLACEHOLDER:' content data). Built files with it: {hits}"
    )


def test_placeholder_scan_finds_feed_only_text(tmp_path: Path) -> None:
    # A summary goes only into the feeds when the post has its own description.
    front_matter = (
        "title: Test\ndate: 2026-01-02\ntopics: [math]\n"
        'description: "A real description."\nsummary: "PLACEHOLDER: one sentence for the feed."\n'
    )
    result, out = build_post(tmp_path, "The PLACEHOLDER pattern in C++ is not template text.", front_matter)
    assert result.returncode == 0, result.stderr + result.stdout
    hits = placeholder_hits(out)
    assert {"index.xml", "posts/index.xml", "topics/math/index.xml"} <= set(hits), hits
    assert "posts/test-post/index.html" not in hits
