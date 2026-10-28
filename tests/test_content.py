from pathlib import Path

import pytest


@pytest.mark.content
def test_no_placeholder_text_is_published(prod_site: Path) -> None:
    hits = sorted(
        str(path.relative_to(prod_site))
        for path in prod_site.rglob("*.html")
        if "PLACEHOLDER" in path.read_text(encoding="utf-8")
    )
    assert hits == [], f"Replace the PLACEHOLDER text in content/ and data/ before you publish: {hits}"
