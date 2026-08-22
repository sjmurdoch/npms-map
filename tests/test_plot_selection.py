"""Choosing plots at home: the first of the surveyor's tasks."""
import re

from playwright.sync_api import expect

from helpers import (PLOT8, choose, close_sheet, locate, open_plot,
                     set_bearing, stored, tap_plot_on_map)


def test_tapping_the_number_opens_that_plot(app):
    """The number is the biggest part of a plot and the part a hand reaches for."""
    tap_plot_on_map(app, 8)
    expect(app.locator("#sheetTitle")).to_contain_text("Plot 8")
    expect(app.locator("#sheetTitle")).to_contain_text("TL 34500 43333")


def test_tapping_near_the_dot_still_opens_the_plot(app):
    """The dot is 16 px across; the tap target has to be finger-sized."""
    box = app.locator(".plot-lbl", has_text=re.compile(r"^8$")).first.bounding_box()
    app.mouse.click(box["x"] + box["width"] / 2, box["y"] - 24)   # above the number
    expect(app.locator("#sheet")).to_have_class(re.compile("open"))
    expect(app.locator("#sheetTitle")).to_contain_text("Plot 8")


def test_choosing_a_plot_counts_it_and_colours_it(app):
    choose(app, 8)
    expect(app.locator("#btnPlots")).to_contain_text("1 of 5 chosen")
    expect(app.locator(".plot-lbl", has_text=re.compile(r"^8$")).first) \
        .to_have_class(re.compile("chosen"))


def test_the_hint_retires_once_a_plot_is_chosen(app):
    choose(app, 8)
    expect(app.locator("#hint")).to_be_hidden()


def test_a_chosen_plot_offers_an_explicit_way_off_the_list(app):
    """A pressed toggle reads as status, not as an offer to undo."""
    open_plot(app, 8)
    expect(app.locator("#pDrop")).to_have_count(0)
    app.locator("#pChoose").click()
    expect(app.locator("#pDrop")).to_contain_text("Remove plot 8")
    app.locator("#pDrop").click()
    expect(app.locator("#pChoose")).to_have_text("Choose for survey")
    expect(app.locator("#pDrop")).to_have_count(0)
    close_sheet(app)
    expect(app.locator("#btnPlots")).to_contain_text("0 of 5 chosen")


def test_the_primary_button_still_toggles_both_ways(app):
    open_plot(app, 8)
    app.locator("#pChoose").click()
    expect(app.locator("#pChoose")).to_have_attribute("aria-pressed", "true")
    app.locator("#pChoose").click()
    expect(app.locator("#pChoose")).to_have_attribute("aria-pressed", "false")


def test_habitat_shape_bearing_and_notes_are_recorded(app):
    open_plot(app, 7)
    app.locator("#pChoose").click()
    app.locator("#pHab").select_option("woodland")
    app.locator("#pLin").click()
    set_bearing(app, 70)
    app.locator("#pNote").fill("Hedge along the field edge")
    close_sheet(app)
    rec = stored(app)["plots"]["7"]
    assert rec["chosen"] and rec["habitat"] == "woodland"
    assert rec["shape"] == "linear" and rec["bearing"] == 70
    assert rec["note"] == "Hedge along the field edge"


def test_a_bearing_can_point_anywhere_round_the_compass(app):
    """A linear plot runs one way out of its point, so half a circle is not enough."""
    open_plot(app, 7)
    app.locator("#pLin").click()
    set_bearing(app, 250)
    close_sheet(app)
    assert stored(app)["plots"]["7"]["bearing"] == 250


def test_use_heading_takes_the_direction_you_are_facing(app):
    """Facing south-west and folding that onto 20 degrees would lay the tape backwards."""
    locate(app, *PLOT8, heading=200, speed=2)
    open_plot(app, 7)
    app.locator("#pLin").click()
    app.locator("#pBrgHead").click()
    close_sheet(app)
    assert stored(app)["plots"]["7"]["bearing"] == 200


def test_the_next_plot_stays_tappable_after_choosing_one(app):
    """Closing the sheet lets the panel grow back; it must not bury the map."""
    choose(app, 8)
    app.wait_for_timeout(600)
    box = app.locator(".plot-lbl", has_text=re.compile(r"^8$")).first.bounding_box()
    panel = app.locator("#panel").bounding_box()
    assert box["y"] > panel["y"] + panel["height"], "the plot ended up behind the panel"


def test_choices_survive_closing_the_app(app):
    choose(app, 8, habitat="arable")
    choose(app, 13, habitat="lowland-grass")
    app.reload()
    app.wait_for_function(
        "() => document.querySelectorAll('.leaflet-overlay-pane path').length > 0")
    expect(app.locator("#btnPlots")).to_contain_text("2 of 5 chosen")
    assert stored(app)["plots"]["8"]["habitat"] == "arable"


def test_tapping_another_plot_switches_the_open_sheet(app):
    tap_plot_on_map(app, 7)
    tap_plot_on_map(app, 13)
    expect(app.locator("#sheetTitle")).to_contain_text("Plot 13")


def test_the_plot_list_shows_every_plot_and_marks_the_chosen_ones(app):
    choose(app, 8, habitat="arable")
    app.locator("#btnPlots").click()
    app.wait_for_selector("#sheet.open")
    rows = app.locator(".plot-row")
    expect(rows).to_have_count(24)
    chosen = app.locator(".plot-row.chosen")
    expect(chosen).to_have_count(1)
    expect(chosen).to_contain_text("Arable field margins")


def test_the_list_shows_how_far_away_each_plot_is(app):
    locate(app, 534350, 243200)
    app.locator("#btnPlots").click()
    app.wait_for_selector("#sheet.open")
    expect(app.locator('[data-plot="8"] .far')).to_have_text("201 m")


def test_the_plan_can_be_copied_out_for_the_npms_form(app):
    choose(app, 8, habitat="arable")
    app.locator("#btnPlots").click()
    app.wait_for_selector("#sheet.open")
    copied = app.evaluate("""async () => {
      let text = null;
      Object.defineProperty(navigator, 'share', { configurable: true, value: undefined });
      navigator.clipboard.writeText = async (t) => { text = t; };
      document.getElementById('btnExport').click();
      await new Promise(r => setTimeout(r, 100));
      return text;
    }""")
    assert "NPMS TL3443" in copied
    assert "Plot 8  TL 34500 43333" in copied
    assert "Arable field margins" in copied
    assert "5 × 5 m square" in copied
