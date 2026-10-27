import subprocess
from pathlib import Path

import pytest

from helpers import ROOT, hugo_build


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
