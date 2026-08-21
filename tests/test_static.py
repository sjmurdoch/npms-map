"""Checks on the files themselves, independent of a browser."""
import json
import re
import subprocess
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parent.parent
SCRIPTS = ["app.js", "geo.js", "sw.js", "vendor/leaflet.js"]


@pytest.mark.parametrize("name", SCRIPTS)
def test_javascript_parses(name):
    subprocess.run(["node", "--check", str(APP / name)], check=True,
                   capture_output=True)


def test_index_html_is_well_formed():
    import html.parser

    class Strict(html.parser.HTMLParser):
        def error(self, message):
            raise AssertionError(message)

    Strict().feed((APP / "index.html").read_text())


def test_every_precached_shell_file_exists():
    """A missing entry makes the service worker install fail and offline break."""
    sw = (APP / "sw.js").read_text()
    listed = re.search(r"const SHELL_FILES = \[(.*?)\];", sw, re.S).group(1)
    for name in re.findall(r'"([^"]+)"', listed):
        if name == "./":
            continue
        assert (APP / name).exists(), f"{name} is precached but missing"


def test_index_loads_only_scripts_that_exist():
    html = (APP / "index.html").read_text()
    for src in re.findall(r'<script src="([^"]+)"', html):
        assert (APP / src).exists(), f"{src} is referenced but missing"


def test_the_archived_species_work_is_not_wired_in():
    """It is parked deliberately; nothing in the app may pull it back in."""
    for name in ["index.html", "app.js", "sw.js", "manifest.webmanifest"]:
        text = (APP / name).read_text()
        assert "species.js" not in text, f"{name} references the archived data"
    assert (APP / "archive/species-extraction.tar.gz").exists()


def test_manifest_is_valid_json_and_names_real_icons():
    manifest = json.loads((APP / "manifest.webmanifest").read_text())
    for icon in manifest.get("icons", []):
        assert (APP / icon["src"]).exists(), f"{icon['src']} is missing"


def test_site_is_published_noindex():
    """The sheet is licensed OS material; it must not be indexed."""
    html = (APP / "index.html").read_text()
    assert re.search(r'name="robots"[^>]*noindex', html)
    assert "noindex" in (APP / "robots.txt").read_text().lower() or \
           "Disallow: /" in (APP / "robots.txt").read_text()
