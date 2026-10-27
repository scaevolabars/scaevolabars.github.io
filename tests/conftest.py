import shutil
import subprocess
from pathlib import Path

import pytest

from helpers import ROOT, copy_site, hugo_build


@pytest.fixture(scope="session", autouse=True)
def vendor() -> None:
    subprocess.run([str(ROOT / "scripts" / "vendor.sh")], check=True)


@pytest.fixture(scope="session")
def prod_site(tmp_path_factory: pytest.TempPathFactory) -> Path:
    dest = tmp_path_factory.mktemp("prod")
    result = hugo_build(ROOT, dest)
    assert result.returncode == 0, result.stderr + result.stdout
    return dest


@pytest.fixture(scope="session")
def draft_site(tmp_path_factory: pytest.TempPathFactory) -> Path:
    dest = tmp_path_factory.mktemp("drafts")
    result = hugo_build(ROOT, dest, "--buildDrafts")
    assert result.returncode == 0, result.stderr + result.stdout
    return dest


@pytest.fixture(scope="session")
def empty_site(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A production build of a copy with no posts and no notes."""
    src = copy_site(tmp_path_factory.mktemp("empty-src"))
    for section in ("posts", "notes"):
        for entry in (src / "content" / section).iterdir():
            if entry.name == "_index.md":
                continue
            if entry.is_dir():
                shutil.rmtree(entry)
            else:
                entry.unlink()
    dest = tmp_path_factory.mktemp("empty")
    result = hugo_build(src, dest)
    assert result.returncode == 0, result.stderr + result.stdout
    return dest
