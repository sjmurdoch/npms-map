"""Fixtures for the NPMS TL3443 field map tests.

The app is a static site with no build step, so the tests serve the working tree
over HTTP and drive it in a real browser. Geolocation is stubbed rather than
using Playwright's own override so that accuracy, heading and speed can be set
exactly, and so a fix arrives synchronously instead of on a timer.
"""
import functools
import http.server
import threading
from pathlib import Path

import pytest

APP_DIR = Path(__file__).resolve().parent.parent
PHONE = {"width": 390, "height": 844}

# Installed before any page script runs, so the app sees it at startup.
GPS_STUB = """
(() => {
  const state = { lat: null, lon: null, acc: 5, heading: null, speed: 0 };
  const watchers = new Map();
  let nextId = 1;

  function emit() {
    if (state.lat === null) return;
    const pos = { timestamp: Date.now(), coords: {
      latitude: state.lat, longitude: state.lon, accuracy: state.acc,
      heading: state.heading, speed: state.speed,
      altitude: null, altitudeAccuracy: null } };
    watchers.forEach((w) => w.ok(pos));
  }

  Object.defineProperty(navigator, 'geolocation', { configurable: true, value: {
    watchPosition(ok, err) {
      const id = nextId++;
      watchers.set(id, { ok, err });
      emit();
      return id;
    },
    clearWatch(id) { watchers.delete(id); },
    getCurrentPosition(ok, err) { watchers.set(nextId++, { ok, err }); emit(); }
  }});

  window.__gps = {
    set(lat, lon, acc, extra) {
      Object.assign(state, { lat, lon, acc }, extra || {});
      emit();
    },
    fail(message) {
      watchers.forEach((w) => w.err && w.err({ code: 2, message }));
    },
    watching() { return watchers.size; }
  };
})();
"""


@pytest.fixture(scope="session")
def server():
    """Serve the working tree; a service worker needs http, not file://."""
    handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                directory=str(APP_DIR))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    httpd.log_message = lambda *a, **k: None
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_port}"
    httpd.shutdown()


@pytest.fixture
def browser_context_args(browser_context_args):
    return {**browser_context_args, "viewport": dict(PHONE),
            "has_touch": True, "is_mobile": True}


@pytest.fixture
def app(page, server):
    """The app loaded on a phone-sized screen with a stubbed GPS, ready to drive."""
    page.add_init_script(GPS_STUB)
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(f"{server}/index.html")
    page.wait_for_function(
        "() => document.querySelectorAll('.leaflet-overlay-pane path').length > 0")
    page.__dict__["errors"] = errors
    yield page
    # A silent exception leaves half the map missing, which most assertions here
    # would not otherwise notice.
    assert not errors, f"uncaught page errors: {errors}"
