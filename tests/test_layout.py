"""Layout on the screens the app actually gets held on."""
import re

import pytest
from playwright.sync_api import expect

from helpers import close_sheet, labels, open_plot

LANDSCAPE = {"width": 844, "height": 390}
SMALL = {"width": 375, "height": 667}


def panel_box(page):
    return page.locator("#panel").bounding_box()


def test_the_whole_square_is_reachable_below_the_panel(app):
    """The panel covers the top of the map; the fit has to allow for it."""
    box = panel_box(app)
    tops = app.evaluate("""() => [...document.querySelectorAll('.plot-lbl')]
        .map(e => e.getBoundingClientRect().y)""")
    assert min(tops) > box["y"] + box["height"], "plots hidden under the panel"
    assert max(tops) < app.viewport_size["height"]


def test_the_panel_never_grows_past_the_screen(app):
    box = panel_box(app)
    assert box["y"] + box["height"] <= app.viewport_size["height"] + 1


def test_opening_a_sheet_shrinks_the_panel_to_its_readout(app):
    tall = panel_box(app)["height"]
    open_plot(app, 8)
    assert panel_box(app)["height"] < tall
    close_sheet(app)
    assert panel_box(app)["height"] == pytest.approx(tall, abs=1)


def test_the_plot_under_discussion_stays_visible_beside_the_sheet(app):
    open_plot(app, 8)
    app.wait_for_timeout(600)          # the map slides the plot into view
    box = app.locator(".plot-lbl", has_text=re.compile(r"^8$")).first.bounding_box()
    panel = panel_box(app)
    sheet = app.locator("#sheet").bounding_box()
    assert panel["y"] + panel["height"] < box["y"] < sheet["y"]


def test_the_collapse_toggle_is_hidden_while_a_sheet_covers_the_controls(app):
    """It used to do nothing visible but still flip the stored state."""
    expect(app.locator("#toggle")).to_be_visible()
    open_plot(app, 8)
    expect(app.locator("#toggle")).to_be_hidden()
    close_sheet(app)
    expect(app.locator("#toggle")).to_be_visible()


def test_the_walk_to_row_survives_collapsing_the_panel(app):
    open_plot(app, 8)
    app.locator("#pGo").click()
    close_sheet(app)
    app.locator("#toggle").click()
    expect(app.locator("#more")).not_to_have_class("open")
    expect(app.locator("#nav")).to_be_visible()


class TestHeldSideways:
    @pytest.fixture(autouse=True)
    def rotate(self, app):
        app.set_viewport_size(LANDSCAPE)
        app.locator("#btnFit").click()
        app.wait_for_timeout(600)

    def test_the_panel_still_fits_the_screen(self, app):
        box = panel_box(app)
        assert box["y"] + box["height"] <= LANDSCAPE["height"] + 1

    def test_every_control_stays_reachable(self, app):
        """Save offline was pushed off a 390 px tall screen entirely."""
        for control in ["#btnLocate", "#btnFit", "#btnOffline"]:
            app.locator(control).scroll_into_view_if_needed()
            expect(app.locator(control)).to_be_in_viewport()

    def test_the_square_uses_the_room_beside_the_panel(self, app):
        box = panel_box(app)
        xs = app.evaluate("""() => [...document.querySelectorAll('.plot-lbl')]
            .map(e => e.getBoundingClientRect().x)""")
        assert min(xs) > box["x"] + box["width"], "plots hidden behind the panel"
        assert labels(app) == 24


class TestSmallPhone:
    @pytest.fixture(autouse=True)
    def shrink(self, app):
        app.set_viewport_size(SMALL)
        app.locator("#btnFit").click()
        app.wait_for_timeout(600)

    def test_the_panel_fits_and_the_plots_are_clear_of_it(self, app):
        box = panel_box(app)
        assert box["y"] + box["height"] <= SMALL["height"] + 1
        tops = app.evaluate("""() => [...document.querySelectorAll('.plot-lbl')]
            .map(e => e.getBoundingClientRect().y)""")
        assert min(tops) > box["y"] + box["height"]
