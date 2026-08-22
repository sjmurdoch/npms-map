"""The build: what gets published, and what it says about itself.

The stamp is the only way to tell, from a phone in a field with no signal,
which version of the app it is actually running.
"""
import re
import subprocess
import sys
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parent.parent
SCRIPT = APP / "tools" / "build_site.py"
REV = "abc1234"
WHEN = "2026-08-22T13:07:00Z"


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    out = tmp_path_factory.mktemp("build") / "_site"
    subprocess.run([sys.executable, str(SCRIPT), "--out", str(out),
                    "--rev", REV, "--time", WHEN],
                   check=True, capture_output=True, text=True, cwd=APP)
    return out


def test_the_build_stamps_the_commit_and_the_time_into_the_credits(site):
    credits = (site / "index.html").read_text()
    line = re.search(r'<p id="build">(.*?)</p>', credits, re.S).group(1)
    assert REV in line
    assert "22 August 2026, 13:07 UTC" in line
    assert "<details id=\"credits\">" in credits and line in credits.split("</details>")[0]


def test_the_working_tree_says_it_is_not_a_build(site):
    """Served straight from the tree there is no commit to claim."""
    assert 'id="build">Working copy' in (APP / "index.html").read_text()


def test_the_service_worker_cache_is_named_after_the_build(site):
    """Otherwise a deploy leaves the previous shell in place on every phone."""
    assert 'const VERSION = "%s";' % REV in (site / "sw.js").read_text()
    assert 'const VERSION = "v' in (APP / "sw.js").read_text()


def test_everything_the_app_precaches_is_published(site):
    sw = (site / "sw.js").read_text()
    listed = re.search(r"const SHELL_FILES = \[(.*?)\];", sw, re.S).group(1)
    for name in re.findall(r'"([^"]+)"', listed):
        if name != "./":
            assert (site / name).exists(), f"{name} is precached but not published"


def test_the_workings_are_not_published(site):
    """Tests, tools and notes are not part of the site."""
    published = {p.name for p in site.rglob("*")}
    for name in ["tests", "tools", "README.md", "DOCUMENTATION.md",
                 "COGNITIVE-WALKTHROUGHS.md", "pyproject.toml", "archive"]:
        assert name not in published, f"{name} was published"


def test_a_second_build_replaces_the_first(site):
    subprocess.run([sys.executable, str(SCRIPT), "--out", str(site),
                    "--rev", "deadbee", "--time", WHEN],
                   check=True, capture_output=True, text=True, cwd=APP)
    assert 'const VERSION = "deadbee";' in (site / "sw.js").read_text()


def test_a_directory_it_did_not_build_is_left_alone(tmp_path):
    """--out is a directory this deletes; it must not delete someone's work."""
    mine = tmp_path / "notes"
    mine.mkdir()
    (mine / "field.txt").write_text("a day of records")
    done = subprocess.run([sys.executable, str(SCRIPT), "--out", str(mine)],
                          capture_output=True, text=True, cwd=APP)
    assert done.returncode != 0
    assert "not empty" in done.stderr
    assert (mine / "field.txt").read_text() == "a day of records"
