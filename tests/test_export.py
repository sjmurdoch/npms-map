"""Getting the chosen plots off the phone: as text, and as a file.

The text goes into the NPMS form. The files go wherever the plan is needed
next — the spreadsheet the records live in, the GPS or phone app that will
navigate to the plots, and the mapping tool that wants the outlines too.
"""
import csv
import datetime
import io
import json
import pathlib
import xml.etree.ElementTree as ET

import pytest
from playwright.sync_api import expect

from helpers import (choose, close_sheet, open_plot, set_bearing, start_move,
                     stored)

GPX = "{http://www.topografix.com/GPX/1/1}"
COLUMNS = ["plot", "grid_ref", "easting", "northing", "latitude", "longitude",
           "habitat", "shape", "bearing_deg", "position", "moved_m", "notes"]
NOTE = 'Gate padlocked, ask at "Beauvale Farm"'      # a comma and quotes to survive


def open_export(page):
    if page.locator("#sheet.open").count():
        close_sheet(page)
    if "open" not in (page.locator("#more").get_attribute("class") or ""):
        page.locator("#toggle").click()
    page.locator("#btnPlots").click()
    page.wait_for_selector("#sheet.open")
    page.locator("#btnFiles").click()
    page.wait_for_selector("#exCsv")


def save(page, button):
    """Tap an export button and read back the file it produced."""
    with page.expect_download() as caught:
        page.locator("#" + button).click()
    got = caught.value
    return got.suggested_filename, pathlib.Path(got.path()).read_text(encoding="utf-8-sig")


@pytest.fixture
def planned(app):
    """Two plots chosen: one on its sheet point, one moved and laid out linear."""
    choose(app, 8, habitat="arable")
    open_plot(app, 8)
    app.locator("#pNote").fill(NOTE)
    close_sheet(app)
    (px, py), ppm = start_move(app, 13)
    app.mouse.click(px + 20 * ppm, py)                 # 20 m due east
    app.locator("#placeOk").click()
    app.locator("#pHab").select_option("woodland")
    app.locator("#pLin").click()
    set_bearing(app, 250)
    open_export(app)
    return app


def test_the_csv_carries_every_plot_and_everything_recorded_about_it(planned):
    name, text = save(planned, "exCsv")
    rows = list(csv.reader(io.StringIO(text)))
    assert rows[0] == COLUMNS
    assert [r[0] for r in rows[1:]] == ["8", "13"], "chosen plots only, in sheet order"

    eight = dict(zip(COLUMNS, rows[1]))
    assert eight["grid_ref"] == "TL 34500 43333"
    assert eight["habitat"] == "Arable field margins"
    assert eight["shape"] == "square" and eight["position"] == "sheet"
    assert float(eight["moved_m"]) == 0
    assert eight["notes"] == NOTE                      # comma and quotes intact
    assert 52 < float(eight["latitude"]) < 53 and -1 < float(eight["longitude"]) < 1

    thirteen = dict(zip(COLUMNS, rows[2]))
    assert thirteen["shape"] == "linear" and thirteen["bearing_deg"] == "250"
    assert thirteen["position"] == "marked"
    assert float(thirteen["moved_m"]) == pytest.approx(20, abs=2)
    assert float(thirteen["easting"]) == pytest.approx(534520, abs=2)


def test_the_csv_is_written_the_way_a_spreadsheet_expects(planned):
    """A byte order mark and CRLF line ends, or Excel mangles notes and rows."""
    with planned.expect_download() as caught:
        planned.locator("#exCsv").click()
    raw = pathlib.Path(caught.value.path()).read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    assert raw.count(b"\r\n") == 3                       # a header and two plots


def test_the_gpx_is_one_waypoint_per_plot(planned):
    name, text = save(planned, "exGpx")
    root = ET.fromstring(text)
    points = root.findall(GPX + "wpt")
    assert [p.find(GPX + "name").text for p in points] == ["TL3443 plot 8", "TL3443 plot 13"]
    assert 52 < float(points[0].get("lat")) < 53
    assert points[0].find(GPX + "desc").text.startswith("TL 34500 43333 · Arable field margins")
    assert "25 × 1 m linear, running 250° out from the point" in points[1].find(GPX + "desc").text
    assert "marked out" in points[1].find(GPX + "desc").text


def test_the_geojson_carries_the_outlines_as_well_as_the_points(planned):
    name, text = save(planned, "exGeo")
    data = json.loads(text)
    assert data["type"] == "FeatureCollection"
    kinds = [(f["properties"]["plot"], f["properties"]["feature"], f["geometry"]["type"])
             for f in data["features"]]
    assert kinds == [(8, "plot point", "Point"), (8, "plot footprint", "Polygon"),
                     (13, "plot point", "Point"), (13, "plot footprint", "Polygon")]

    ring = data["features"][1]["geometry"]["coordinates"][0]
    assert len(ring) == 5 and ring[0] == ring[-1], "a closed square"
    point = data["features"][0]["geometry"]["coordinates"]
    assert min(c[0] for c in ring) < point[0] < max(c[0] for c in ring), "square straddles it"

    line = data["features"][3]["geometry"]["coordinates"][0]
    assert min(c[0] for c in line) < data["features"][2]["geometry"]["coordinates"][0], \
        "a linear plot on a westerly bearing runs west of its point"


def test_the_files_are_named_for_the_square_and_the_day(planned):
    today = datetime.date.today().isoformat()
    for button, ext in [("exCsv", "csv"), ("exGpx", "gpx"), ("exGeo", "geojson")]:
        name, _ = save(planned, button)
        assert name == "NPMS-TL3443-plots-" + today + "." + ext


def test_saving_says_what_was_saved(planned):
    save(planned, "exCsv")
    expect(planned.locator("#exNote")).to_contain_text("Saved NPMS-TL3443-plots")
    expect(planned.locator("#exNote")).to_contain_text("2 plots in it")


def test_the_text_for_the_npms_form_is_here_too(planned):
    copied = planned.evaluate("""async () => {
      let text = null;
      Object.defineProperty(navigator, 'share', { configurable: true, value: undefined });
      navigator.clipboard.writeText = async (t) => { text = t; };
      document.getElementById('exText').click();
      await new Promise(r => setTimeout(r, 100));
      return text;
    }""")
    assert "Plot 8  TL 34500 43333" in copied
    expect(planned.locator("#exText")).to_have_text("Copied to clipboard")


def test_there_is_nothing_to_export_until_plots_are_chosen(app):
    open_export(app)
    expect(app.locator("#sheetTitle")).to_contain_text("nothing chosen yet")
    expect(app.locator("#sheetBody")).to_contain_text("Choose the plots you are going to survey")
    expect(app.locator("#exCsv")).to_be_disabled()


def test_the_export_sheet_goes_back_to_the_plot_list(planned):
    planned.locator("#sheetBack").click()
    expect(planned.locator("#sheetTitle")).to_contain_text("Plots for survey")
