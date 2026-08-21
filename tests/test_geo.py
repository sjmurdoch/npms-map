"""The georeferencing data: the thing every position in the app depends on."""
import json
import math
import re
from pathlib import Path

import pytest

from helpers import SQUARE, bng_to_latlon

APP = Path(__file__).resolve().parent.parent
SPACING = 1000.0 / 6.0          # plots sit on an exact sixth-of-the-square lattice


@pytest.fixture(scope="module")
def geo():
    text = (APP / "geo.js").read_text()
    return json.loads(text[text.index("{"): text.rindex(";")])


def test_the_square_is_the_monad_tl3443(geo):
    assert geo["sq_bng"] == pytest.approx(SQUARE)
    assert geo["name"] == "TL3443"


def test_there_are_twenty_four_plots_numbered_one_to_twenty_four(geo):
    numbers = sorted(p["n"] for p in geo["plots"])
    assert numbers == list(range(1, 25))


def test_plots_sit_on_the_exact_lattice(geo):
    """A sixth in from each edge, 166.667 m apart, 25 points with one unused.

    geo.js stores coordinates to the centimetre, so the tolerance is in metres:
    comparing lattice indices instead would amplify that rounding by 166.
    """
    for p in geo["plots"]:
        col = round((p["e"] - SQUARE["e0"]) / SPACING)
        row = round((p["n_"] - SQUARE["n0"]) / SPACING)
        assert 1 <= col <= 5 and 1 <= row <= 5
        assert p["e"] == pytest.approx(SQUARE["e0"] + col * SPACING, abs=0.01)
        assert p["n_"] == pytest.approx(SQUARE["n0"] + row * SPACING, abs=0.01)


def test_the_missing_lattice_point_is_the_one_the_sheet_leaves_out(geo):
    """Top row, fourth column carries no plot, so 24 plots span 25 points."""
    used = {(round((p["e"] - SQUARE["e0"]) / SPACING),
             round((p["n_"] - SQUARE["n0"]) / SPACING)) for p in geo["plots"]}
    missing = {(c, r) for c in range(1, 6) for r in range(1, 6)} - used
    assert missing == {(4, 5)}


def test_every_plot_is_inside_the_square(geo):
    for p in geo["plots"]:
        assert SQUARE["e0"] < p["e"] < SQUARE["e1"]
        assert SQUARE["n0"] < p["n_"] < SQUARE["n1"]


def test_grid_references_agree_with_the_coordinates(geo):
    for p in geo["plots"]:
        digits = re.fullmatch(r"TL(\d{4})(\d{4})", p["gr"])
        assert digits, p["gr"]
        assert int(digits.group(1)) == int(p["e"] - 500000) // 10
        assert int(digits.group(2)) == int(p["n_"] - 200000) // 10


def test_plot_spacing_is_uniform(geo):
    by_row = {}
    for p in geo["plots"]:
        by_row.setdefault(round(p["n_"], 2), []).append(p["e"])
    for row in by_row.values():
        row.sort()
        for a, b in zip(row, row[1:]):
            assert b - a == pytest.approx(SPACING, abs=0.01) or \
                   b - a == pytest.approx(2 * SPACING, abs=0.01)


def test_square_corners_are_ordered_and_roughly_a_kilometre(geo):
    sq = geo["square"]
    assert sq["sw"][0] < sq["nw"][0]        # north-west is further north
    assert sq["sw"][1] < sq["se"][1]        # south-east is further east
    # A degree of latitude is ~111.3 km; the square should be about 1 km tall.
    height_m = (sq["nw"][0] - sq["sw"][0]) * 111_320
    assert height_m == pytest.approx(1000, abs=15)


def test_the_overlay_bounds_contain_the_square(geo):
    (s, w), (n, e) = geo["overlayBounds"]
    for corner in geo["square"].values():
        assert s <= corner[0] <= n
        assert w <= corner[1] <= e


def test_affine_round_trips_every_plot_to_within_a_metre(app, geo):
    """geo.js carries both lat/lon and BNG for each plot; they must agree."""
    for p in geo["plots"]:
        lat, lon = bng_to_latlon(app, p["e"], p["n_"])
        dlat_m = (lat - p["lat"]) * 111_320
        dlon_m = (lon - p["lon"]) * 111_320 * math.cos(math.radians(lat))
        assert math.hypot(dlat_m, dlon_m) < 1.0, f"plot {p['n']} off by too much"
