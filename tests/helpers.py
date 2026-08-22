"""Small vocabulary for driving the app, in the terms the app itself uses."""
import re

# Fixed reference points from geo.js, so tests can talk in eastings/northings.
PLOT8 = (534500.0, 243333.33)
PLOT7 = (534333.33, 243333.33)
SQUARE = {"e0": 534000.0, "e1": 535000.0, "n0": 243000.0, "n1": 244000.0}

_BNG_TO_LL = """([e, n]) => {
  const A = GEO.affine, cx = A.cx, cy = A.cy;
  const de = e - A.E0, dn = n - A.N0;
  const ll = L.CRS.EPSG3857.unproject(
    L.point(cx[0]*de + cx[1]*dn + cx[2], cy[0]*de + cy[1]*dn + cy[2]));
  return [ll.lat, ll.lng];
}"""


def bng_to_latlon(page, e, n):
    """Use the app's own georeferencing, so a test can name a grid position."""
    return page.evaluate(_BNG_TO_LL, [e, n])


def stand_at(page, e, n, acc=5, heading=None, speed=0):
    lat, lon = bng_to_latlon(page, e, n)
    page.evaluate(
        "([lat, lon, acc, extra]) => window.__gps.set(lat, lon, acc, extra)",
        [lat, lon, acc, {"heading": heading, "speed": speed}])


def locate(page, e, n, acc=5, **kw):
    """Start GPS if it is not running, then deliver a fix."""
    if page.locator("#btnLocate").inner_text().strip() == "Locate":
        page.locator("#btnLocate").click()
    stand_at(page, e, n, acc, **kw)


def tap_plot_on_map(page, n):
    """Tap the plot's number where it sits on the map."""
    page.locator(".plot-lbl", has_text=re.compile(rf"^{n}$")).first.click()
    page.wait_for_selector("#sheet.open")
    page.wait_for_selector("#pChoose")


def open_plot(page, n):
    """Open a plot through the list, which does not depend on where the map is.

    Tapping it on the map is the surveyor's usual route and has its own tests;
    as a setup step it is unreliable, because a plot can be off screen after a
    zoom and the tap then lands on nothing.
    """
    if page.locator("#sheet.open").count():
        close_sheet(page)
    if "open" not in (page.locator("#more").get_attribute("class") or ""):
        page.locator("#toggle").click()
    page.locator("#btnPlots").click()
    page.wait_for_selector("#sheet.open")
    page.locator(f'[data-plot="{n}"]').click()
    page.wait_for_selector("#pChoose")


def close_sheet(page):
    page.locator("#sheetClose").click()
    page.wait_for_function(
        "() => !document.getElementById('sheet').classList.contains('open')")


def choose(page, n, habitat=None):
    open_plot(page, n)
    if page.locator("#pChoose").get_attribute("aria-pressed") == "false":
        page.locator("#pChoose").click()
    if habitat:
        page.locator("#pHab").select_option(habitat)
    close_sheet(page)


def stored(page):
    return page.evaluate(
        "() => JSON.parse(localStorage.getItem('tl3443.survey') || 'null')")


def outlines(page):
    return page.locator("path.plot-foot").count()


def labels(page):
    return page.locator(".plot-lbl").count()


def zoom(page, steps):
    """Click the zoom control and let the map settle."""
    control = ".leaflet-control-zoom-" + ("in" if steps > 0 else "out")
    for _ in range(abs(steps)):
        page.locator(control).click()
        page.wait_for_timeout(220)
    page.wait_for_timeout(350)


def marker_gap(page):
    """On-screen distance between two plots one lattice step apart.

    This is what decides whether the numbers are drawn, so tests assert against
    it rather than against a zoom level.
    """
    return page.evaluate("""() => {
      const box = (n) => {
        const el = [...document.querySelectorAll('.plot-lbl')]
          .find(e => e.textContent === String(n));
        return el ? el.getBoundingClientRect() : null;
      };
      const a = box(1), b = box(6);
      return a && b ? Math.abs(b.y - a.y) : null;
    }""")


def settled(page):
    """Wait until the map has stopped moving.

    Opening a plot pans it clear of the panel, and until that animation ends the
    labels are still at their old place and the outline has no path at all.
    """
    page.wait_for_function("""() => {
      const pane = document.querySelector('.leaflet-map-pane');
      const foot = document.querySelector('path.plot-foot');
      const now = pane.style.transform + '|' + (foot ? foot.getAttribute('d') : '');
      const was = window.__settle;
      window.__settle = now;
      return now === was;
    }""")


def plot_point(page, n):
    """Where a plot's point sits on screen, read off its number's anchor."""
    settled(page)
    box = page.locator(".plot-lbl", has_text=re.compile(rf"^{n}$")).first.bounding_box()
    return box["x"] + 12, box["y"] - 10       # the label's iconAnchor, from app.js


def footprint(page):
    """The screen box of the one outline currently drawn."""
    settled(page)
    return page.locator("path.plot-foot").first.bounding_box()


def pixels_per_metre(page):
    """Read the map's scale off the lattice, so tests need not know the zoom."""
    settled(page)
    return marker_gap(page) / 166.667


def set_bearing(page, degrees):
    page.locator("#pBrg").fill(str(degrees))
    page.locator("#pBrg").dispatch_event("change")
