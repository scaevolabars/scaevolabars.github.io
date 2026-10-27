from pathlib import Path

from helpers import copy_site, hugo_build, page

SAMPLE = "/posts/sample-features/"


def test_sidenote_is_inline_and_toggleable(draft_site: Path) -> None:
    soup = page(draft_site, SAMPLE)
    toggle = soup.select_one(".prose p > input.note-toggle")
    assert toggle is not None and toggle["type"] == "checkbox"
    label = toggle.find_next_sibling("label")
    assert "note-ref" in label["class"] and label["for"] == toggle["id"]
    assert label.get_text() == "Note "
    note = label.find_next_sibling("span")
    assert "note" in note["class"] and note["role"] == "note"


def test_sidenotes_inside_another_shortcode_get_unique_ids(tmp_path: Path) -> None:
    # Hugo 0.166 reports line 1, column 1 for every nested shortcode, so the position alone repeats.
    site = copy_site(tmp_path / "src")
    (site / "layouts" / "_shortcodes" / "aside.html").write_text('<div class="aside">{{ .Inner }}</div>')
    (site / "content" / "posts" / "nested.md").write_text(
        "---\ntitle: Nested\ndate: 2026-01-02\n---\n\n"
        "{{< aside >}}One.{{< note >}}a{{< /note >}} Two.{{< note >}}b{{< /note >}}{{< /aside >}}\n\n"
        "{{< aside >}}Three.{{< note >}}c{{< /note >}}{{< /aside >}}\n",
        encoding="utf-8",
    )
    result = hugo_build(site, tmp_path / "out")
    assert result.returncode == 0, result.stderr + result.stdout
    ids = [toggle["id"] for toggle in page(tmp_path / "out", "/posts/nested/").select("input.note-toggle")]
    assert len(ids) == 3 and len(set(ids)) == 3, ids
