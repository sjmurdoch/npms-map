"""Working with no signal, which is the normal case in the field."""
import pytest
from playwright.sync_api import expect

from helpers import choose, stored

pytestmark = pytest.mark.slow


def wait_for_controlling_worker(page):
    page.wait_for_function(
        "() => !!(navigator.serviceWorker && navigator.serviceWorker.controller)",
        timeout=15000)


def test_the_service_worker_precaches_the_shell(app):
    wait_for_controlling_worker(app)
    cached = app.evaluate("""async () => {
      const names = await caches.keys();
      const shell = names.find(n => n.includes('shell'));
      const keys = await (await caches.open(shell)).keys();
      return keys.map(r => new URL(r.url).pathname);
    }""")
    for needed in ["/index.html", "/app.js", "/geo.js", "/tl3443_overlay.png"]:
        assert any(p.endswith(needed) for p in cached), f"{needed} not precached"


def test_the_app_starts_with_the_network_cut(app, context):
    wait_for_controlling_worker(app)
    choose(app, 8, habitat="arable")
    context.set_offline(True)
    try:
        app.reload()
        app.wait_for_function(
            "() => document.querySelectorAll('.leaflet-overlay-pane path').length > 0")
        expect(app.locator("#btnPlots")).to_contain_text("1 of 5 chosen")
        assert app.locator(".plot-lbl").count() == 24
        assert app.locator(".leaflet-image-layer").count() == 1
    finally:
        context.set_offline(False)


def test_choices_are_kept_on_the_device_not_the_network(app, context):
    choose(app, 13, habitat="woodland")
    context.set_offline(True)
    try:
        assert stored(app)["plots"]["13"]["habitat"] == "woodland"
    finally:
        context.set_offline(False)


def test_a_missing_tile_does_not_break_the_map(app, context):
    """Uncached tiles are served as blanks rather than failing the page."""
    wait_for_controlling_worker(app)
    context.set_offline(True)
    try:
        app.locator("#btnFit").click()
        app.wait_for_timeout(800)
        assert app.locator(".plot-lbl").count() == 24
    finally:
        context.set_offline(False)
