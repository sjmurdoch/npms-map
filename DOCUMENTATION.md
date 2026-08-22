# NPMS TL3443 field map — what it does

A single-page web app for surveying the National Plant Monitoring Scheme square **TL3443**. The scheme's square sheet is georeferenced and laid over OpenStreetMap, the 24 plots are drawn where they really are on the ground, and the whole thing runs on a phone in a field with no signal. Everything below is in the app itself; there is no account, no server and no network call except for base map tiles.

This describes the features. [README.md](README.md) is the short version, and [COGNITIVE-WALKTHROUGHS.md](COGNITIVE-WALKTHROUGHS.md) records why the app works the way it does.

## The square and its plots

TL3443 is an Ordnance Survey National Grid monad: the kilometre square EPSG:27700 E534000–535000, N243000–244000. The scheme places 25 plot points on an exact lattice, a sixth of the square in from each edge and 166.667 m apart. The point in the top row, fourth column carries no plot, so the app draws 24 plots numbered 1–24.

The square's edge is drawn in black, its thirds in dashed grey, and each plot as a numbered marker at its lattice point.

## Installing it on a phone

Open the site in Safari or Chrome and add it to the home screen. It then runs full screen with no browser chrome, keeps working with no signal, and holds the screen awake while GPS is running so the map does not black out mid-field.

## The panel

The panel sits at the top left. Tapping **▾** opens the controls and **▴** collapses them back to the readout; the choice is remembered between sessions. While a plot sheet is open, or a plot is being moved, the panel shrinks to the readout on its own so the map between them stays clear.

### The readout

Always visible, in whatever state the panel is in:

- the **10-figure grid reference** of where you are, to the metre — for example `TL 34502 43333`;
- **outside square** in amber when the fix falls outside TL3443, and the reference in amber with it;
- your **heading** in degrees and as a compass point, from the magnetometer or from GPS course over ground;
- your **GPS accuracy** as ±metres, as the phone reports it.

Before the first fix it says what to tap to get one, naming the button that is actually on screen.

### Walking to a plot

Choosing **Walk to it** in a plot puts a guidance row under the readout, and that row stays visible when the panel is collapsed:

- an **arrow** that points where to walk when a heading is available, and against the north-up map when it is not — the row says which of the two it is doing;
- the **distance** to the plot, in metres or kilometres;
- the **bearing** to it in degrees and as a compass point;
- a dashed orange line on the map from you to the plot.

Inside the greater of 4 m and your own GPS accuracy it changes to **At plot n**, and the phone buzzes if it is a phone that can. A fix worse than ±15 m cannot place a 5 m plot, so it says so — *too rough to place a plot* — instead of claiming you have arrived. With GPS off the row says so rather than leaving the last distance sitting there looking live. Tapping the row opens the plot; **✕** calls the walk off.

### Nearest plot

With a fix and no plot targeted, the panel names the nearest plot with its distance and bearing, and tapping it opens that plot. It stands down while you are walking to a particular plot, so only one distance and bearing is ever on screen.

### Controls

| Control | What it does |
|---|---|
| **Plots for survey — n of 5 chosen** | Opens the list of all 24 plots, and counts the ones you have chosen against a target of five. |
| **NPMS sheet** slider | Fades the sheet against the OpenStreetMap base, 0–100%. |
| **Hide sheet** / **Show sheet** | One tap to take the sheet off and put it back at the opacity you were using — for checking access, tracks and field boundaries underneath. |
| **Locate** / **Stop** | Starts and stops GPS. |
| **Follow** | Keeps the map centred on you; dragging the map turns it off. With a plot open it holds the plot in view instead, so you can see yourself and the outline at once. |
| **Compass** | Turns on the magnetometer, and shows as pressed while it is on. On iOS this needs the tap to grant permission. If the compass is missing, refused or unavailable, a line under the row says which, and says that heading falls back to GPS course over ground while you are moving. |
| **Fit square** | Fits TL3443 to the screen, padded clear of the panel. |
| **Save offline** | Downloads the base tiles for the square and its surroundings. |
| **Sources & licence** | The credits, and the build this copy of the app came from. |

## The map

The sheet is drawn at 85% opacity over OpenStreetMap. The legend under the slider names what the sheet's habitat shading means. Zoom goes to 20, past the base map's own detail, so a plot can be judged against a hedge line.

How much is drawn follows how far apart the plots actually land on screen, not a guessed zoom level, because the fitted view sits at a different zoom on every phone:

- **numbered markers** while there is room for the numbers;
- **plain dots** once the numbers would collide;
- **nothing but the square** once the dots themselves would merge;
- **plot outlines at true size** from about 30 m across the screen, for plots you have chosen, are walking to, have open, or are moving.

Each plot is tappable well beyond its dot: the number and an invisible finger-sized disc around it open the plot.

## A plot

Tapping a plot — on the map, or in the plots list — opens its sheet.

**Choose for survey** adds it to your list and turns it green on the map, and the panel counts how many you have. A chosen plot offers *Remove plot n from my list* to take it back off, because a pressed button reads as a status rather than as an offer to undo.

**Habitat** is a menu of the eleven NPMS broad habitats: broadleaved woodland, hedges and scrub; native pinewood and juniper scrub; arable field margins; lowland grassland; upland grassland; heathland; bog and wet heath; marsh and fen; freshwater; rock outcrops, cliffs and screes; coast.

**Shape and bearing** describe how the plot is laid out on the ground:

- a **5 × 5 m square**, which straddles the plot's point and turns to the bearing;
- a **25 × 1 m linear** plot, which starts at the plot's point and runs the full 25 m out along the bearing, the way the tape is laid.

The bearing goes the whole way round the compass, 0–359°, so 90° and 270° lay a linear plot opposite ways. **Use heading** stamps in the direction you are facing, for laying a plot along the feature you are standing next to. Zoomed in far enough, the plot is drawn on the map at its true size and orientation.

Under the slider the sheet shows the references to write on the form, and they follow the slider as you turn it: a linear plot's **start and end**, or a square's **south-west corner**, each as a 10-figure (1 m) grid reference, with the direction as a 16-point compass point. While a square sits square to the grid that corner is its south-west one; turned off the grid it is the corner lying furthest south-west. Every export carries the same references.

**Notes** is a free text field — access, landowner, what is growing, why you moved the plot. Everything is saved as you type.

## Where the plot really is

The section names the plot's position as a 10-figure grid reference either way: the sheet's printed point until you move it, and the position you marked out afterwards, with how far that is from the printed point.

The printed point itself can land in a ditch, in a crop, or on the far side of a fence. Two ways to move the plot, and one to undo it:

- **Move plot to where I am standing** records the position you actually put it, and says how accurate the fix was when you did. It needs a GPS fix and says so when there is none.
- **Move plot on the map** hands the map over instead. The sheet gets out of the way, the plot is haloed, and a tap puts it — marker, number and outline together — where your finger went. The bar reports the new grid reference and how far that is from the sheet's point, calls out a tap that lands outside the monad, and writes nothing until you tap **Put plot n here**. Tapping again adjusts; panning the map to look around is not a tap; **Cancel** leaves the plot exactly where it was. No GPS is involved, so a plot can be moved while planning at home.
- **Put it back on the sheet's point** undoes either.

A moved plot counts as chosen, is drawn at its real position, and reports its distance from the sheet's point everywhere it appears — in its own sheet, and in every export.

## Exporting the plan

From the plots list:

**Copy my plot list** hands the whole plan over as plain text, for the NPMS form or a text to yourself — grid reference, habitat, shape and bearing, and notes, plot by plot. On a phone it goes to the share sheet; otherwise it goes to the clipboard.

**Export as a file** writes the same plan in the formats other things read. Files are named for the square and the day — `NPMS-TL3443-plots-2026-08-22.csv`. On a phone they go out through the share sheet, since a downloaded file on iOS is hard to find again; on a desktop they download. The sheet says which file it wrote, and says nothing at all if the share sheet was dismissed.

Only chosen plots are exported. Where a plot has been moved, the files carry the position you marked out; everywhere else, the sheet's printed point.

**Spreadsheet (CSV)** — one row per plot, with a byte order mark and CRLF line ends so a spreadsheet reads it cleanly:

| Column | What it holds |
|---|---|
| `plot` | Plot number, 1–24 |
| `grid_ref` | 10-figure grid reference of the plot's position |
| `easting`, `northing` | OSGB36 / EPSG:27700, to 0.1 m |
| `latitude`, `longitude` | WGS84, to six decimal places |
| `habitat` | The NPMS broad habitat, in full |
| `shape` | `square` or `linear` |
| `bearing_deg` | 0–359 |
| `bearing_point` | The same direction as a 16-point compass point — `WSW` |
| `start_grid_ref`, `end_grid_ref` | A linear plot's two ends; blank for a square |
| `sw_corner_grid_ref` | A square plot's south-west corner; blank for a linear plot |
| `position` | `marked` if you moved the plot, `sheet` if it sits on the printed point |
| `moved_m` | How far the plot is from the sheet's point |
| `notes` | Your notes, quoted so commas and quotation marks survive |

**GPS waypoints (GPX)** — GPX 1.1, one `<wpt>` per plot named `TL3443 plot n`, described with its grid reference, habitat, shape and bearing, the references it is laid out from, whether it is marked out, and its notes. Loads into a handheld GPS or a phone mapping app.

**Map data (GeoJSON)** — a `FeatureCollection` in WGS84 carrying two features per plot: the plot's point, and its footprint as a polygon — the 5 m square, or the 25 m line from the point along its bearing. Both carry the same properties as the CSV columns — references and compass point included — plus `feature`, which says which of the two it is. Opens in QGIS and the like.

## Working offline

The app shell, the georeferenced sheet, the plot positions and every GPS feature are cached the first time the app loads, and work with no signal from then on. Only the OpenStreetMap base tiles need the network.

**Save offline** downloads the base tiles for the square and a margin around it, at zoom 14 to 18 — wide context at low zoom, kept tight at 18 so the whole download stays a couple of hundred tiles, in line with OSM's tile usage policy. It fetches gently, two at a time, skips tiles already held, and reports progress and the final count. Tiles already viewed are cached as you go. Where a tile was never cached and there is no signal, the map draws blank rather than failing.

The status line under the controls says what is cached, and whether the app is online.

Cached tiles survive app updates: they live in their own cache, and only the app shell is replaced when a new version is deployed.

## What is kept on the device

Everything you choose is stored in the browser's local storage on that phone, under `tl3443.survey`: which plots are chosen, their habitat, shape, bearing and notes, any position you marked out, and which plot you are walking to. Whether the panel is open is remembered too. It survives closing the app, reloading, and starting up with no signal. Nothing is sent anywhere; clearing the browser's site data clears it, so export anything you would mind losing.

## Accuracy and georeferencing

The georeferencing was derived from the sheet's own vector square and cross-checked three ways: against the sheet's scale bar, against the PDF's embedded ESRI geospatial dictionary (agreeing to 1–2 m, within its coordinate rounding), and against the National Grid lines drawn in the raster itself (agreeing to about 1 m).

Positions are converted between EPSG:27700 and WGS84 with an affine fitted over a 3 km box centred on the square, with a residual under 0.45 m — about 1 m in total, which is well inside typical phone GPS error of 3–10 m. Plot footprints, distances and bearings are computed in eastings and northings, so they are true metres on the ground rather than screen approximations.

## Building and deploying

The working tree is the site; there is no build step to speak of. `tools/build_site.py` copies the files the site needs into a clean directory and stamps two things into them:

- the **build line** in the app's *Sources & licence* section — the commit and the time it was built — so a phone in a field can be asked which version it is running;
- the **service worker's cache version**, named after that commit, so each deploy retires the previous shell instead of relying on someone bumping a number by hand.

Served straight from the working tree, the app says *Working copy — not a build*. A build made from a modified tree marks its commit `-dirty`.

Every setting takes an option, an environment variable, or its default:

| Option | Variable | Default |
|---|---|---|
| `--out` | `NPMS_BUILD_OUT` | `_site` |
| `--rev` | `NPMS_BUILD_REV` | short `git HEAD` |
| `--time` | `NPMS_BUILD_TIME` | now, UTC |

```
python3 tools/build_site.py --out _site
```

`.github/workflows/deploy.yml` runs the whole test suite on every push to `main`, builds the site, and publishes it to GitHub Pages. The deploy waits on the tests: a broken app that a phone has already cached is a bad day out.

## Tests

The suite drives the real app in a headless browser. It serves the working tree, stubs geolocation so accuracy, heading and speed can be set exactly, and covers the georeferencing data, the opening view, choosing plots, plot shapes and bearings drawn to scale, moving a plot by tapping the map, walking to a plot, the exported CSV, GPX and GeoJSON, the build and its stamp, layout on a phone held either way, and a full offline start.

```
uv run playwright install chromium     # once
uv run pytest
```

`-m "not slow"` skips the service-worker tests, which need a real install cycle.

## Sources and licence

Square sheet from the National Plant Monitoring Scheme (BSBI, CEH, JNCC, Plantlife). Base mapping is OS 1:25000 colour raster, printed under licence © Crown copyright 2010, Ordnance Survey licence number 100017572. Habitat shading is derived from the CEH Land Cover Map (LCM2007, © NERC (CEH) 2011), Natural England habitat inventories, and CCW Phase 1 habitat survey data (© Countryside Council for Wales). Crown copyright and database right, all rights reserved, © third party licensors. Base tiles © OpenStreetMap contributors, used under the Open Database Licence.

The site is published `noindex` and is intended for the survey volunteer's own field use, not as a redistribution of Ordnance Survey mapping.
