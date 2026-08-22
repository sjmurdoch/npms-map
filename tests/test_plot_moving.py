"""Putting a plot where it really is, without having to walk there.

The sheet's point can land in a ditch, a crop or the far side of a fence. On
site the honest answer is to stand on the spot and mark it; at the kitchen
table, with the aerial view showing the hedge and the GPS forty miles away, the
only answer is to tap the map.
"""
import re

import pytest
from playwright.sync_api import expect

from helpers import (close_sheet, metres_apart, sheet_point, start_move,
                     stored)

STEP = 1000.0 / 6.0              # plots 12 and 13 are one lattice step apart


def test_a_plot_can_be_moved_by_tapping_the_map(app):
    """No GPS is involved at any point: this is the route for planning at home."""
    (px, py), ppm = start_move(app, 13)
    app.mouse.click(px + 20 * ppm, py)                 # 20 m due east
    expect(app.locator("#placeText")).to_contain_text(re.compile(r"TL 345[12]\d 43500"))
    app.locator("#placeOk").click()

    e, n = sheet_point(app, 13)
    marked = stored(app)["plots"]["13"]["marked"]
    assert marked["e"] == pytest.approx(e + 20, abs=2)
    assert marked["n"] == pytest.approx(n, abs=2)
    expect(app.locator("#sheetBody")).to_contain_text(re.compile(r"Marked at TL 345[12]\d 435\d\d"))
    expect(app.locator("#sheetBody")).to_contain_text(re.compile(r"(19|20|21) m from the sheet"))


def test_a_moved_plot_counts_as_chosen(app):
    """Nobody moves a plot they are not going to survey."""
    (px, py), ppm = start_move(app, 13)
    app.mouse.click(px + 20 * ppm, py)
    app.locator("#placeOk").click()
    close_sheet(app)
    expect(app.locator("#btnPlots")).to_contain_text("1 of 5 chosen")


def test_the_move_is_only_provisional_until_it_is_confirmed(app):
    """A mis-tap in a field must not silently rewrite the plot's position."""
    (px, py), ppm = start_move(app, 13)
    app.mouse.click(px + 20 * ppm, py)
    app.locator("#placeCancel").click()
    expect(app.locator("#sheetTitle")).to_contain_text("Plot 13")
    expect(app.locator("#sheetBody")).to_contain_text("point printed on the NPMS sheet")
    assert ((stored(app) or {}).get("plots", {}).get("13") or {}).get("marked") is None
    assert metres_apart(app, 12, 13) == pytest.approx(STEP, abs=2)


def test_the_plot_moves_on_the_map_before_the_move_is_committed(app):
    """The point of tapping the map is seeing where the plot lands as you tap."""
    (px, py), ppm = start_move(app, 13)
    app.mouse.click(px + 20 * ppm, py)
    assert metres_apart(app, 12, 13) == pytest.approx(STEP + 20, abs=2)


def test_a_tap_can_be_taken_back_by_tapping_again(app):
    (px, py), ppm = start_move(app, 13)
    app.mouse.click(px + 20 * ppm, py)
    app.mouse.click(px - 20 * ppm, py)                 # 20 m the other way
    app.locator("#placeOk").click()
    e, n = sheet_point(app, 13)
    assert stored(app)["plots"]["13"]["marked"]["e"] == pytest.approx(e - 20, abs=2)


def test_the_numbers_stop_opening_plots_while_one_is_being_moved(app):
    """Mid-move every marker is just more map: opening one would lose the move."""
    start_move(app, 13, zoom_steps=2)
    app.locator(".plot-lbl", has_text=re.compile(r"^14$")).first.click()
    expect(app.locator("#sheet")).not_to_have_class(re.compile("open"))
    app.locator("#placeOk").click()
    expect(app.locator("#sheetTitle")).to_contain_text("Plot 13")
    marked = stored(app)["plots"]["13"]["marked"]
    assert (marked["e"], marked["n"]) == pytest.approx(sheet_point(app, 14), abs=3)


def test_a_plot_moved_on_the_map_can_still_be_put_back(app):
    (px, py), ppm = start_move(app, 13)
    app.mouse.click(px + 20 * ppm, py)
    app.locator("#placeOk").click()
    app.locator("#pUnmark").click()
    assert stored(app)["plots"]["13"]["marked"] is None
    assert metres_apart(app, 12, 13) == pytest.approx(STEP, abs=2)


def test_panning_the_map_is_not_a_tap(app):
    """Looking around for the hedge must not drop the plot where you let go."""
    (px, py), ppm = start_move(app, 13)
    app.mouse.move(px, py + 60)
    app.mouse.down()
    app.mouse.move(px - 120, py + 60, steps=12)
    app.mouse.up()
    expect(app.locator("#placeOk")).to_be_disabled()
    expect(app.locator("#placeText")).to_contain_text("Tap the map where plot 13 really is")


def test_a_tap_outside_the_square_says_so(app):
    """A plot outside the monad is not an NPMS plot, however good the spot looks."""
    start_move(app, 13, zoom_steps=0)
    box = app.locator("#map").bounding_box()
    app.mouse.click(box["x"] + box["width"] - 6, box["y"] + box["height"] / 2)
    expect(app.locator("#placeText")).to_contain_text("outside the square")
