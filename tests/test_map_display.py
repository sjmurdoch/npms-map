"""How the map draws plots: outlines, marker detail, and the readout."""
import re

import pytest
from playwright.sync_api import expect

from helpers import (choose, close_sheet, footprint, labels, locate,
                     marker_gap, open_plot, outlines, pixels_per_metre,
                     plot_point, set_bearing, stand_at, zoom)


def test_no_outlines_are_drawn_for_plots_nobody_chose(app):
    """Twenty-four outlines is clutter that unchoosing cannot clear."""
    zoom(app, 4)
    assert outlines(app) == 0


def test_a_chosen_plot_is_outlined_to_scale(app):
    choose(app, 13)
    zoom(app, 4)
    assert outlines(app) == 1


def test_an_open_plot_is_outlined_while_you_look_at_it(app):
    zoom(app, 4)
    open_plot(app, 13)
    assert outlines(app) == 1
    close_sheet(app)
    assert outlines(app) == 0


def test_removing_a_plot_takes_its_outline_away(app):
    zoom(app, 4)
    choose(app, 13)
    assert outlines(app) == 1
    open_plot(app, 13)
    app.locator("#pDrop").click()
    close_sheet(app)
    assert outlines(app) == 0


def test_outlines_disappear_when_they_are_too_small_to_read(app):
    choose(app, 13)
    zoom(app, 4)
    assert outlines(app) == 1
    zoom(app, -4)
    assert outlines(app) == 0


def test_the_plot_being_walked_to_is_outlined(app):
    zoom(app, 4)
    open_plot(app, 13)
    app.locator("#pGo").click()
    close_sheet(app)
    assert outlines(app) == 1


def test_numbers_give_way_to_plain_dots_when_they_would_collide(app):
    """Zoomed out, twenty-four numbers overlapped into an unreadable brick."""
    assert labels(app) == 24
    zoom(app, -2)
    assert labels(app) == 0
    assert app.locator(".leaflet-overlay-pane path").count() > 0


def test_the_plots_drop_out_entirely_once_the_lattice_is_smaller_than_them(app):
    zoom(app, -5)
    assert labels(app) == 0


def test_detail_comes_back_on_zooming_in(app):
    zoom(app, -3)
    assert labels(app) == 0
    zoom(app, 3)
    assert labels(app) == 24
    assert marker_gap(app) >= 34


def test_the_grid_reference_tracks_the_fix(app):
    locate(app, 534350, 243200)
    expect(app.locator("#lGrid")).to_have_text("TL 34350 43200")
    stand_at(app, 534500, 243333.33)
    expect(app.locator("#lGrid")).to_have_text("TL 34500 43333")


def test_being_outside_the_square_is_called_out(app):
    locate(app, 534500, 243500)
    expect(app.locator("#lGrid")).not_to_have_class("out")
    stand_at(app, 535500, 243500)
    expect(app.locator("#lGrid")).to_have_class("out")
    expect(app.locator("#sub")).to_contain_text("outside square")


def test_accuracy_is_always_on_show(app):
    locate(app, 534500, 243333, acc=12)
    expect(app.locator("#sub")).to_contain_text("±12")


def test_the_sheet_can_be_faded_to_see_what_is_underneath(app):
    """Judging access means seeing the roads and field edges the sheet covers."""
    expect(app.locator("#btnSheet")).to_have_text("Hide sheet")
    app.locator("#btnSheet").click()
    expect(app.locator("#btnSheet")).to_have_text("Show sheet")
    assert app.locator(".leaflet-image-layer").evaluate("e => e.style.opacity") == "0"
    app.locator("#btnSheet").click()
    expect(app.locator("#btnSheet")).to_have_text("Hide sheet")
    assert app.locator(".leaflet-image-layer").evaluate("e => e.style.opacity") != "0"


def test_the_opacity_slider_and_the_button_agree(app):
    app.locator("#op").fill("40")
    app.locator("#op").dispatch_event("input")
    expect(app.locator("#opv")).to_have_text("40%")
    expect(app.locator("#btnSheet")).to_have_text("Hide sheet")


def test_a_linear_plot_runs_out_from_the_point_along_its_bearing(app):
    """The tape starts at the sheet's point: nothing of it lies behind."""
    zoom(app, 4)
    open_plot(app, 13)
    app.locator("#pLin").click()
    set_bearing(app, 0)
    px, py = plot_point(app, 13)
    box, ppm = footprint(app), pixels_per_metre(app)
    assert box["height"] == pytest.approx(25 * ppm, abs=4)
    # The narrow dimension, not the square's 5 m. It is not exactly 1 m across:
    # the outline is drawn in grid metres, and grid north sits about 1.5 degrees
    # off screen north here, so a 25 m tape leans that far across the box.
    assert box["width"] < 3 * ppm
    assert box["y"] + box["height"] == pytest.approx(py, abs=4)   # near end at the point
    assert box["x"] + box["width"] / 2 == pytest.approx(px, abs=5)


def test_a_linear_plot_can_run_south_of_the_point(app):
    """Half a circle of bearings would have made this one impossible."""
    zoom(app, 4)
    open_plot(app, 13)
    app.locator("#pLin").click()
    set_bearing(app, 180)
    px, py = plot_point(app, 13)
    box, ppm = footprint(app), pixels_per_metre(app)
    assert box["height"] == pytest.approx(25 * ppm, abs=4)
    assert box["y"] == pytest.approx(py, abs=4)                   # runs away southwards


def test_a_square_plot_still_straddles_the_point(app):
    zoom(app, 4)
    open_plot(app, 13)
    px, py = plot_point(app, 13)
    box, ppm = footprint(app), pixels_per_metre(app)
    assert box["height"] == pytest.approx(5 * ppm, abs=4)
    assert box["y"] + box["height"] / 2 == pytest.approx(py, abs=4)
    assert box["x"] + box["width"] / 2 == pytest.approx(px, abs=4)
