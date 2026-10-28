import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from helpers import ROOT, build_post, copy_site, page, parse

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
    body = (
        "{{< aside >}}One.{{< note >}}a{{< /note >}} Two.{{< note >}}b{{< /note >}}{{< /aside >}}\n\n"
        "{{< aside >}}Three.{{< note >}}c{{< /note >}}{{< /aside >}}"
    )
    result, out = build_post(tmp_path, body, site=site)
    assert result.returncode == 0, result.stderr + result.stdout
    ids = [toggle["id"] for toggle in page(out, "/posts/test-post/").select("input.note-toggle")]
    assert len(ids) == 3 and len(set(ids)) == 3, ids


def test_math_renders_at_build_time(draft_site: Path) -> None:
    soup = page(draft_site, SAMPLE)
    assert soup.select_one(".prose .katex-display") is not None
    assert soup.select(".prose p .katex")
    assert soup.select_one(".note .katex") is not None
    assert soup.select_one('link[href="/vendor/katex/katex.min.css"]') is not None
    assert "$5" in soup.select_one(".prose").get_text()


def test_pages_without_math_skip_katex_css(prod_site: Path) -> None:
    assert page(prod_site, "/about/").select_one("link[href*=katex]") is None


def test_katex_css_matches_the_katex_inside_hugo() -> None:
    """Hugo renders math with its bundled KaTeX, so the vendored CSS must be the same version."""
    hugo = subprocess.run(["hugo", "version"], capture_output=True, text=True, check=True).stdout
    assert hugo.startswith("hugo v0.166."), (
        "Hugo changed: look up the KaTeX version it bundles and update KATEX_VERSION in scripts/vendor.sh"
    )
    css = (ROOT / "static" / "vendor" / "katex" / "katex.min.css").read_text(encoding="utf-8")
    assert 'content:"0.18.4"' in css


def test_diagram_page_loads_mermaid_module(draft_site: Path) -> None:
    soup = page(draft_site, SAMPLE)
    assert soup.select_one("pre.mermaid") is not None
    assert [(s.get("type"), s.get("src")) for s in soup.select("script")] == [("module", "/js/diagrams.mjs")]


def test_diagram_module_imports_vendored_mermaid(draft_site: Path) -> None:
    js = (draft_site / "js" / "diagrams.mjs").read_text(encoding="utf-8")
    target = re.search(r'from "(/vendor/[^"]+)"', js).group(1)
    assert (draft_site / target.lstrip("/")).is_file()


def test_only_pages_with_diagrams_load_javascript(prod_site: Path, draft_site: Path) -> None:
    for site in (prod_site, draft_site):
        for html in site.rglob("*.html"):
            soup = parse(html)
            assert bool(soup.select("script")) == bool(soup.select("pre.mermaid")), html


def test_code_is_highlighted_with_classes(draft_site: Path) -> None:
    soup = page(draft_site, SAMPLE)
    assert soup.select(".prose pre.chroma")
    assert all(el.get("style") is None for el in soup.select("pre.chroma, pre.chroma *"))
    css = next((draft_site / "css").glob("site.*.css")).read_text(encoding="utf-8")
    assert ".chroma .k" in css


def test_syntax_colours_keep_muted_text_off_the_grid() -> None:
    css = (ROOT / "assets" / "css" / "syntax.css").read_text(encoding="utf-8")
    assert "var(--grid)" not in css, "muted comments on --grid are 4.29:1 in light mode"


def test_scrolling_blocks_are_reachable_with_tab(draft_site: Path) -> None:
    blocks = page(draft_site, SAMPLE).select(".prose pre")
    assert {"chroma", "mermaid"} <= {name for pre in blocks for name in pre.get("class", [])}
    assert [pre.get("tabindex") for pre in blocks] == ["0"] * len(blocks)


@pytest.mark.parametrize("body", ["The bid was $5 and the ask was $10.", "Sizes 2$ and 3$ only."])
def test_prices_are_not_taken_for_math(tmp_path: Path, body: str) -> None:
    result, _ = build_post(tmp_path, body)
    assert result.returncode != 0
    assert "inline math starts or ends with a space" in result.stderr
    assert "For a dollar sign, write \\$." in result.stderr


def test_escaped_brackets_stay_text(tmp_path: Path) -> None:
    result, out = build_post(tmp_path, r"Read a\[i\] and f\(x\) here.")
    assert result.returncode == 0, result.stderr
    prose = page(out, "/posts/test-post/").select_one(".prose")
    assert "a[i] and f(x)" in prose.get_text()
    assert prose.select_one(".katex") is None


def test_bad_formula_fails_the_build_and_names_the_file(tmp_path: Path) -> None:
    result, _ = build_post(tmp_path, r"Broken $\notacommand{x}$ here.")
    assert result.returncode != 0
    assert "Unable to render math" in result.stderr and "test-post.md" in result.stderr


def test_page_with_math_only_in_a_note_loads_katex_css(tmp_path: Path) -> None:
    result, out = build_post(tmp_path, "Plain text.{{< note >}}Here $x^2$ is math.{{< /note >}} More text.")
    assert result.returncode == 0, result.stderr
    assert page(out, "/posts/test-post/").select_one('link[href="/vendor/katex/katex.min.css"]') is not None


def test_display_math_is_reachable_with_tab(draft_site: Path) -> None:
    blocks = page(draft_site, SAMPLE).select(".katex-display")
    assert blocks and [b.get("tabindex") for b in blocks] == ["0"] * len(blocks)


def test_note_with_block_content_fails_the_build(tmp_path: Path) -> None:
    result, _ = build_post(tmp_path, "Text.{{< note >}}One.\n\nTwo.{{< /note >}} More.")
    assert result.returncode != 0
    assert "a note must be one paragraph of inline text" in result.stderr


@pytest.mark.parametrize("body", ["<div>Raw.</div>\n\nText.", "A vector<T> here."])
def test_raw_html_fails_the_build(tmp_path: Path, body: str) -> None:
    # The README promises this rule. An ignoreLogs entry for this warning would silently drop the HTML instead.
    result, _ = build_post(tmp_path, body)
    assert result.returncode != 0
    assert "Raw HTML omitted" in result.stderr and "warning-goldmark-raw-html" in result.stderr


def feed_items(site: Path) -> dict[str, str]:
    """Every feed item's description, by feed file and item link."""
    items = {}
    for feed in site.rglob("index.xml"):
        for item in ET.parse(feed).getroot().iter("item"):
            items[f"{feed.relative_to(site)} {item.findtext('link')}"] = item.findtext("description") or ""
    return items


def test_feeds_show_notes_inline_and_math_as_mathml(draft_site: Path) -> None:
    items = feed_items(draft_site)
    assert items
    for key, html in items.items():
        for bad in ("<input", "note-ref", "katex-html"):
            assert bad not in html, (key, bad)
    sample = [html for key, html in items.items() if key.startswith("index.xml ") and key.endswith(SAMPLE)]
    assert len(sample) == 1
    assert "later. (Use the mid at" in sample[0] and "<math" in sample[0]


@pytest.mark.parametrize("body", ["Price $p_t$ moves.", "Text.{{< note >}}An aside.{{< /note >}} More."])
def test_entry_needs_a_description_when_its_summary_has_math_or_a_note(tmp_path: Path, body: str) -> None:
    result, _ = build_post(tmp_path, body, "title: Test\ndate: 2026-01-02\n")
    assert result.returncode != 0
    assert "add a description: the first paragraph has math or a note" in result.stderr
    assert "test-post.md" in result.stderr
