import re
import subprocess
from pathlib import Path

from bs4 import BeautifulSoup

from helpers import ROOT, copy_site, hugo_build, page

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
            soup = BeautifulSoup(html.read_text(encoding="utf-8"), "html.parser")
            assert bool(soup.select("script")) == bool(soup.select("pre.mermaid")), html


def test_code_is_highlighted_with_classes(draft_site: Path) -> None:
    soup = page(draft_site, SAMPLE)
    assert len(soup.select(".prose pre.chroma")) == 2
    assert all(el.get("style") is None for el in soup.select("pre.chroma, pre.chroma *"))
    css = next((draft_site / "css").glob("site.*.css")).read_text(encoding="utf-8")
    assert ".chroma .k" in css


def test_syntax_colours_keep_muted_text_off_the_grid() -> None:
    css = (ROOT / "assets" / "css" / "syntax.css").read_text(encoding="utf-8")
    assert "var(--grid)" not in css, "muted comments on --grid are 4.29:1 in light mode"
