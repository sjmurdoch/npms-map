"""Walking to a plot and marking it out: the surveyor's second task."""
import re
from pathlib import Path

from playwright.sync_api import expect

from helpers import PLOT8, close_sheet, locate, open_plot, stand_at, stored

APP = Path(__file__).resolve().parent.parent

AWAY = (534350.0, 243200.0)      # ~201 m south-west of plot 8, bearing 48 degrees
AT_PLOT8 = (534502.0, 243334.0)  # 2 m from the sheet's point


def walk_to(app, n):
    open_plot(app, n)
    app.locator("#pGo").click()
    close_sheet(app)


def test_asking_to_walk_somewhere_starts_gps_itself(app):
    """Locate sits behind the sheet at that moment, so pointing at it would fail."""
    expect(app.locator("#btnLocate")).to_have_text("Locate")
    walk_to(app, 8)
    expect(app.locator("#btnLocate")).to_have_text("Stop")


def test_distance_and_bearing_to_the_chosen_plot(app):
    walk_to(app, 8)
    stand_at(app, *AWAY)
    expect(app.locator("#navDist")).to_have_text("201 m to plot 8")
    expect(app.locator("#navWhich")).to_contain_text("48° NE")


def test_the_guidance_follows_the_plot_you_picked_not_the_nearest_one(app):
    """Standing next to plot 2 while walking to plot 8 must not steer to plot 2."""
    walk_to(app, 8)
    stand_at(app, *AWAY)
    expect(app.locator("#navDist")).to_contain_text("plot 8")
    expect(app.locator("#near")).to_be_hidden()


def test_arrival_is_announced_when_you_get_there(app):
    walk_to(app, 8)
    stand_at(app, *AWAY)
    stand_at(app, *AT_PLOT8, acc=5)
    expect(app.locator("#navDist")).to_have_text("At plot 8")
    expect(app.locator("#nav")).to_have_class(re.compile("here"))


def test_a_rough_fix_never_claims_you_have_arrived(app):
    """A plot pegged out on a +-55 m fix is in the wrong place permanently."""
    walk_to(app, 8)
    stand_at(app, *AT_PLOT8, acc=55)
    expect(app.locator("#navDist")).not_to_have_text("At plot 8")
    expect(app.locator("#navWhich")).to_contain_text("too rough to place a plot")
    expect(app.locator("#nav")).not_to_have_class(re.compile("here"))


def test_arrival_appears_once_the_fix_sharpens(app):
    walk_to(app, 8)
    stand_at(app, *AT_PLOT8, acc=55)
    stand_at(app, *AT_PLOT8, acc=5)
    expect(app.locator("#navDist")).to_have_text("At plot 8")


def test_turning_the_compass_on_leaves_the_button_alone(app):
    """"Compass on" wrapped onto two lines and left the row of buttons ragged."""
    button = app.locator("#btnCompass")
    one_line = app.locator("#btnLocate").bounding_box()["height"]
    button.click()
    expect(button).to_have_text("Compass")
    expect(button).to_have_attribute("aria-pressed", "true")
    assert button.bounding_box()["height"] == one_line


def test_the_compass_button_never_relabels_itself(app):
    """It has a third of a phone's width: any second word wraps and the row of
    three goes ragged. Whatever happens is said on its own line underneath."""
    assert "btnCompass.textContent" not in (APP / "app.js").read_text()
    one_line = app.locator("#btnLocate").bounding_box()["height"]
    button = app.locator("#btnCompass")
    button.click()                                    # the compass this browser has
    expect(button).to_have_text("Compass")
    expect(button).to_have_attribute("aria-pressed", "true")
    assert button.bounding_box()["height"] == one_line, "the pressed label wraps"
    expect(app.locator("#compassNote")).to_be_hidden()


def test_a_device_with_no_compass_is_told_so_and_told_what_it_gets_instead(app):
    """The branch a phone without a magnetometer takes, run for real."""
    one_line = app.locator("#btnLocate").bounding_box()["height"]
    app.add_init_script(
        "Object.defineProperty(window, 'DeviceOrientationEvent',"
        " { configurable: true, value: undefined });")
    app.reload()
    app.wait_for_function(
        "() => document.querySelectorAll('.leaflet-overlay-pane path').length > 0")
    button = app.locator("#btnCompass")
    button.click()
    expect(button).to_have_text("Compass")
    expect(button).to_be_disabled()
    assert button.bounding_box()["height"] == one_line
    expect(app.locator("#compassNote")).to_contain_text("This device has no compass")
    expect(app.locator("#compassNote")).to_contain_text("GPS course")


def test_the_arrow_steers_by_compass_when_there_is_a_heading(app):
    walk_to(app, 8)
    stand_at(app, *AWAY)
    expect(app.locator("#navWhich")).to_contain_text("map is north-up")
    app.locator("#btnCompass").click()
    app.evaluate("""() => {
      const e = new Event('deviceorientationabsolute');
      Object.defineProperties(e, { absolute: { value: true }, alpha: { value: 270 } });
      window.dispatchEvent(e);
    }""")
    # The arrow answers straight away: bearing 48 minus heading 90 puts the plot
    # off to the left.
    assert "rotate(-42deg)" in app.locator("#navArrow").get_attribute("style")
    expect(app.locator("#navWhich")).to_contain_text("follow the arrow")
    # The readout's heading is part of the position line, so it comes with the
    # next fix rather than immediately.
    stand_at(app, *AWAY)
    expect(app.locator("#sub")).to_contain_text("90° E")


def test_stopping_gps_clears_everything_that_looked_live(app):
    """A frozen dot and a frozen distance are worse than none at all."""
    walk_to(app, 8)
    stand_at(app, *AWAY)
    app.locator("#btnLocate").click()
    expect(app.locator("#lGrid")).to_have_text("— no GPS fix —")
    expect(app.locator("#navWhich")).to_contain_text("GPS off")
    expect(app.locator("#navDist")).to_have_text("—")
    expect(app.locator(".gps-dot")).to_have_count(0)
    expect(app.locator("#near")).to_be_hidden()


def test_a_restored_target_does_not_claim_to_be_searching(app):
    walk_to(app, 8)
    app.reload()
    app.wait_for_function(
        "() => document.querySelectorAll('.leaflet-overlay-pane path').length > 0")
    expect(app.locator("#nav")).to_have_class(re.compile("on"))
    expect(app.locator("#navWhich")).to_contain_text("GPS off")


def test_the_walk_can_be_called_off(app):
    walk_to(app, 8)
    app.locator("#navStop").click()
    expect(app.locator("#nav")).not_to_have_class(re.compile("on"))
    assert stored(app)["target"] is None


def test_marking_a_plot_records_where_you_actually_stood(app):
    """The sheet's point may be in a crop; NPMS wants the real position."""
    locate(app, *AT_PLOT8, acc=5)
    open_plot(app, 8)
    expect(app.locator("#pMark")).to_contain_text("(±5 m)")
    app.locator("#pMark").click()
    expect(app.locator("#sheetBody")).to_contain_text("Marked at TL 34502 43333")
    expect(app.locator("#sheetBody")).to_contain_text("2 m from the sheet")
    assert stored(app)["plots"]["8"]["marked"]["e"] == 534502


def test_a_moved_plot_can_be_put_back(app):
    locate(app, *AT_PLOT8, acc=5)
    open_plot(app, 8)
    app.locator("#pMark").click()
    app.locator("#pUnmark").click()
    expect(app.locator("#sheetBody")).to_contain_text("point printed on the NPMS sheet")
    assert stored(app)["plots"]["8"]["marked"] is None


def test_marking_needs_a_fix_at_all(app):
    open_plot(app, 8)
    expect(app.locator("#pMark")).to_be_disabled()
    expect(app.locator("#pMark")).to_contain_text("needs a GPS fix")


def test_the_nearest_plot_is_offered_when_not_walking_anywhere(app):
    locate(app, 534350, 243200)
    expect(app.locator("#near")).to_be_visible()
    expect(app.locator("#near")).to_contain_text("Nearest plot")
    expect(app.locator("#near")).to_contain_text("2")


def test_a_lost_fix_is_reported(app):
    locate(app, *AWAY)
    app.evaluate("() => window.__gps.fail('Position unavailable')")
    expect(app.locator("#lGrid")).to_have_text("— GPS unavailable —")
    expect(app.locator("#sub")).to_have_text("Position unavailable")
