"""What the surveyor meets on opening the app for the first time."""
from playwright.sync_api import expect

from helpers import labels, marker_gap


def test_the_square_and_all_its_plots_are_drawn(app):
    assert labels(app) == 24


def test_the_readout_names_a_control_that_is_actually_on_screen(app):
    """The panel opens expanded, so pointing at the collapse toggle would lie."""
    expect(app.locator("#more")).to_have_class("open")
    expect(app.locator("#sub")).to_have_text("Tap Locate to start GPS")
    expect(app.locator("#btnLocate")).to_be_visible()


def test_the_collapsed_readout_points_at_the_toggle_instead(app):
    app.locator("#toggle").click()
    expect(app.locator("#more")).not_to_have_class("open")
    expect(app.locator("#sub")).to_contain_text("then Locate")


def test_no_fix_is_reported_until_gps_is_started(app):
    expect(app.locator("#lGrid")).to_have_text("— no GPS fix —")
    expect(app.locator("#lGrid")).to_have_class("none")


def test_nothing_is_chosen_and_the_hint_says_how_to_start(app):
    expect(app.locator("#btnPlots")).to_contain_text("0 of 5 chosen")
    expect(app.locator("#hint")).to_be_visible()


def test_the_walk_to_row_is_hidden_until_there_is_somewhere_to_walk(app):
    expect(app.locator("#nav")).not_to_have_class("on")


def test_the_nearest_plot_line_is_hidden_without_a_fix(app):
    expect(app.locator("#near")).to_be_hidden()


def test_plot_numbers_are_legible_in_the_opening_view(app):
    """A fixed zoom threshold once hid every number on the opening view."""
    gap = marker_gap(app)
    assert gap is not None and gap >= 34, f"plots only {gap} px apart"


def test_the_sheet_legend_explains_its_shading(app):
    """The build strips the sheet's own legend, so the app has to carry it."""
    expect(app.locator("#legend")).to_contain_text("broadleaved woodland")


def test_openstreetmap_attribution_is_present(app):
    expect(app.locator(".leaflet-control-attribution")).to_contain_text("OpenStreetMap")
