# Cognitive walkthroughs

A record of the cognitive walkthroughs run against this app, the problems they exposed, and what was changed as a result.

Each step of a task is judged against four questions:

1. Will the user try to achieve the right result?
2. Will the user notice that the correct action is available?
3. Will the user associate the correct action with the result they are trying to achieve?
4. After the action is performed, will the user see that progress is made toward the goal?

A step passes only if all four hold. Any "no" is an issue, and the fix has to earn its place without spoiling the app for the other people who use it.

---

## 1. Busy surveyor: choosing plots at home, marking them out on site

*Run 21 August 2026 against the app as of commit 94f720e.*

### Persona

A National Plant Monitoring Scheme volunteer with a full-time job and one free Saturday a month. They have been allocated square TL3443 and have the printed square sheet with 24 numbered plot positions on it. They want to spend twenty minutes at the kitchen table picking which plots to survey, then drive out, find each one, mark it out on the ground, and record what is growing in it. They are not a GIS user. They will not read documentation. If the app does not make the next step obvious in the first few seconds, they will fall back to the paper sheet and a hand-written list.

This is one of several personas. The app is also used as a plain live-position field map, and that use must not get slower or noisier.

### Task A — choose suitable plots at home

| Step | Q1 goal | Q2 action visible | Q3 action associated | Q4 progress visible | Verdict |
|---|---|---|---|---|---|
| Open the app, see the square and its plots | yes | yes | yes | yes | **pass** |
| Judge which plots sit in semi-natural habitat | yes | **no** | **no** | n/a | **fail** |
| Check access — roads, tracks, field boundaries | yes | **no** | **no** | yes | **fail** |
| Record the choice of plot | yes | **no** | **no** | **no** | **fail** |
| Know when enough plots have been picked | yes | **no** | **no** | **no** | **fail** |
| Take the plan out of the app | yes | **no** | **no** | **no** | **fail** |

Issues found:

- **A1 — the habitat shading has no legend.** The sheet's pale green shading is drawn on the overlay, but the build step deliberately strips the sheet's legend along with its title and scale bar. The surveyor sees coloured areas with nothing to say what they mean, so the one piece of habitat information on the map is unreadable. (Q2, Q3)
- **A2 — "Map" did not say what it did.** The opacity slider was labelled "Map", which names neither what it fades nor why anyone would want it faded. The surveyor who wants to see the footpath under the sheet has no reason to associate that slider with the result. (Q3)
- **A3 — plots could not be chosen.** Tapping a plot gave a popup with a grid reference and decimal coordinates. There was no way to say "this one", no place to note the habitat, and nothing to write on. The core goal of the task could not be reached in the app at all. (Q2, Q3, Q4)
- **A4 — no sense of completion.** With no record of what had been chosen, there was no answer to "how many have I picked?". (Q4)
- **A5 — nothing to hand on.** Nothing could be copied into the NPMS form or sent to a phone. (Q2, Q4)
- **A6 — a plot is a dot, not a place.** The plot marker is a fixed-size circle at every zoom, so at any zoom it is impossible to see whether a plot falls in a hedge, a ditch or the middle of a wheat field — exactly the judgement the task requires. (Q1, Q4)
- **A7 — the panel hid the plots.** On a phone the open control panel covered the top half of the map, and the square was fitted to the whole map, so plots 21–24 sat underneath the panel and could not be tapped. The first action of the task was physically unreachable. (Q2)

### Task B — find the plot on site and mark it out

| Step | Q1 goal | Q2 action visible | Q3 action associated | Q4 progress visible | Verdict |
|---|---|---|---|---|---|
| Start GPS | yes | yes | yes | yes | **pass** |
| Walk to a particular chosen plot | yes | **no** | **no** | **no** | **fail** |
| Know when you have arrived | yes | n/a | n/a | **no** | **fail** |
| Lay out the plot on the ground | yes | **no** | **no** | **no** | **fail** |
| Move a plot whose marked point is unusable | yes | **no** | **no** | **no** | **fail** |

Issues found:

- **B1 — "nearest plot" is the wrong plot.** The readout gave distance and bearing to whichever plot was nearest. Walking in from the road to plot 17, the nearest plot is 16 or 12, so the guidance actively points the wrong way. There was no way to say which plot was being walked to. (Q2, Q3, Q4)
- **B2 — no arrival.** The distance number simply got smaller. There is no point at which the app says "you are there", and at ±6 m GPS the surveyor cannot tell a good fix from a stale one. (Q4)
- **B3 — the plot's real size is invisible.** An NPMS plot is 5 × 5 m, or 25 × 1 m in a linear habitat. The app drew none of that, so the surveyor pacing out canes had nothing to place them against and no way to see how the plot sat against a hedge line. (Q2, Q4)
- **B4 — a moved plot could not be recorded.** If the marked point falls in a crop or a pond, the plot has to be moved and its real position written down. There was nowhere to put it. (Q2, Q3, Q4)

### Task C — record which plants are growing there

**Not addressed in this round**, at the user's direction, to keep the change focused on defining plots and on the location problems. Recorded here as a known gap: the app has nothing for species at all, so every question fails at every step, and the surveyor still needs the printed species list and a paper recording sheet. A working extraction of the NPMS *Species Identification Guide* (410 entries with habitat, difficulty class, Wildflower-level flag and flowering months) is parked in `archive/species-extraction.tar.gz` and is deliberately not loaded by the app.

### Changes made

Task A:

- Tapping a plot now opens a **plot sheet**: choose it for survey, set its habitat from the eleven NPMS broad habitats, set its shape, record where it was really marked out, and write a note. (A3)
- The panel carries a **"Plots for survey — n of 5 chosen"** button opening a list of all 24, and a first-run line telling the surveyor to tap a plot. Chosen plots turn green on the map and in the list. (A3, A4)
- **"Copy my plot list"** produces a plain-text plan — grid reference, habitat, plot shape and bearing, notes — for the NPMS form or a text to yourself. (A5)
- A **one-line legend** under the opacity slider names what the shading means, restoring the information the build step strips out of the sheet. (A1)
- The slider is relabelled **"NPMS sheet"** and joined by a **"Hide sheet"** button, so seeing what is underneath is one obvious tap rather than a drag of an unexplained control. (A2)
- Plot **footprints are drawn to scale** from zoom 17, so a plot can be judged against the hedge or field boundary it sits on. (A6)
- **The square is now fitted around the panel**, not behind it, so every plot is reachable on a phone. (A7)
- Opening a sheet **shrinks the panel to its readout** and slides the map so the plot in question sits in the strip of map still visible, ringed by a halo. The sheet is non-modal, so the map can still be panned and zoomed while reading it. (A6, A7)

Task B:

- **"Walk to it"** sets a plot as the target. A guidance row — arrow, distance, bearing — sits directly under the live readout and **stays visible when the panel is collapsed**. The arrow points where to walk when a compass heading is available, and against the north-up map when it is not, and says which of the two it is doing. (B1)
- Arriving inside the greater of 4 m and the current GPS accuracy switches the row to **"At plot 8"** with the accuracy alongside, and buzzes once. (B2)
- The footprint is drawn at true size as a **5 × 5 m square or a 25 × 1 m linear plot**, with a bearing slider and a "Use heading" button so a linear plot can be laid along the hedge the surveyor is standing next to. (B3)
- **"Move plot to where I am standing"** records the real position from the current fix, moves the marker and footprint there, and reports how far it was moved from the sheet's point. It can be put back. (B4)
- While a plot sheet is open, Follow holds **that plot** in view rather than re-centring on the blue dot, so marking out shows both the surveyor and the outline at once.

### Defects found while testing the changes

- Setting `className` on the plot labels stripped Leaflet's own positioning class, detaching every label from its marker.
- `fitSquare()` ran before the panel had been laid out, so it measured a collapsed panel and fitted the square behind the open one.
- A pan issued from `zoomend` lands inside Leaflet's zoom animation and is silently dropped; recentring explicitly fixes it.
- Follow re-centred on the GPS fix on every update, dragging the plot being marked out back underneath the sheet.
- The plot list was rebuilt from scratch on every GPS fix, which reset the reader's scroll position several times a second and wiped the "Copied to clipboard" confirmation. Only the distances are rewritten now.

### Deliberately not changed

- The collapsed readout is untouched: grid reference, heading, accuracy, and nothing else. The walk-to row only appears once a plot has been chosen to walk to.
- Locate, Follow, Compass, Fit square and Save offline keep their positions and behaviour.
- Everything new is local to the device and works with no signal; nothing added needs a network.

### Follow-ups

- Task C is untouched. The species data is extracted and verified but not in the app.
- "n of 5 chosen" takes five as the NPMS target for a square. Worth confirming against the square's own instructions before this is relied on.
- The footprint is drawn centred on the plot point and aligned to grid north unless a bearing is set. That is a placement guide, not a statement of NPMS protocol; whether the scheme wants the point as the centre or a corner should be checked.

---

## 2. The same surveyor, second pass over the whole journey

*Run 21 August 2026 against commit 57e8ac2, walking the same persona through both tasks from a clean install and exercising the controls that were already there.*

The first walkthrough asked whether the tasks were possible at all. This one assumes they are and asks whether they are smooth: whether the actions are big enough to hit, whether the app ever says one thing and shows another, and whether the older controls still behave now that there is more on screen.

### Task A — choose suitable plots at home

| Step | Q1 goal | Q2 action visible | Q3 action associated | Q4 progress visible | Verdict |
|---|---|---|---|---|---|
| Open the app, read what to do first | yes | yes | **no** | yes | **fail** |
| Tap a plot to open it | yes | yes | yes | **no** | **fail** |
| Choose it, set its habitat, note it | yes | yes | yes | yes | **pass** |
| Move on to the next plot | yes | yes | yes | yes | **pass** |
| See how many are chosen | yes | yes | yes | yes | **pass** |
| Copy the plan out | yes | yes | yes | yes | **pass** |

Issues found:

- **A8 — the app opened by telling the user to do something already done.** The readout's standing instruction was *"Tap ▾ then Locate"*, but the panel opens expanded, so the toggle showing was ▴ and Locate was already on screen. The first sentence the surveyor reads contradicts the first thing they see. (Q3)
- **A9 — the plot dot was not a finger.** The tappable dot measured 16 × 16 px, and a tap landing 10 px off centre fell through to the map and panned it instead. Choosing plots is the entire task and its target was a fifth of a comfortable touch target. (Q4)
- **A10 — the number could not be tapped.** The white numbered label is the largest and most obvious part of a plot, and it is what a hand reaches for, but it was drawn `interactive: false` and taps went straight through it to the map. (Q2, Q4)
- **A11 — the first-run hint outlived its usefulness.** *"Tap a numbered plot on the map to choose it"* stayed on screen while the surveyor was demonstrably already working with a plot, contradicting what they had just done. (Q3)

### Task B — find the plot on site and mark it out

| Step | Q1 goal | Q2 action visible | Q3 action associated | Q4 progress visible | Verdict |
|---|---|---|---|---|---|
| Start walking to a chosen plot | yes | yes | yes | **no** | **fail** |
| Read the guidance while walking | yes | yes | **no** | yes | **fail** |
| Watch yourself close on the plot | yes | yes | yes | **no** | **fail** |
| Arrive, mark out, record the position | yes | yes | yes | yes | **pass** |

Issues found:

- **B5 — "Walk to it" did nothing without GPS.** Tapping it set the target and then said *"walking to plot 7 · start Locate"* — but Locate lives in the panel, which the open sheet has just collapsed, so the app asked for an action whose control was not on screen. Nothing moved until the surveyor found their own way back to a hidden button. (Q4)
- **B6 — two plots, two distances, two bearings.** With a target set, the walk-to row (*"201 m to plot 8 · 48° NE"*) sat directly above the nearest-plot row (*"Nearest plot 2 · 37 m · 207° SSW"*). Two different plots with two different bearings, stacked, in the readout someone glances at while walking across a field. (Q3)
- **B7 — Follow put you under the panel.** Follow centred the blue dot in the map container, but the open panel covers the top 384 px of a 844 px phone screen, leaving the dot 7 px clear of its edge. On a shorter phone, following yourself hid you. (Q4)

### Also checked, and working

- **Save offline** downloaded 317 tiles with a live count, cleared its progress bar and re-enabled itself; a reload with the network cut served the shell, the georeferenced sheet, the base tiles and every chosen plot from cache.
- Chosen plots, habitats, shapes, bearings, notes and marked positions all survived a reload and an offline restart.
- Locate, Stop, Follow, Compass, Fit square, the opacity slider and the collapse toggle behave as before, and the collapsed readout is still grid reference, heading and accuracy only.
- Tapping a second plot while a sheet is open switches the sheet to it rather than stacking or closing.

### Changes made

- The opening instruction is generated from the panel the user can actually see — *"Tap Locate to start GPS"* when the panel is open, *"Tap ▾ then Locate"* when it is collapsed — and stops as soon as there is a fix. (A8)
- Every plot carries an invisible 44 px disc as its tap target, so a tap now lands from 22 px out instead of 8, and the number label is tappable and opens the plot. (A9, A10)
- The first-run hint retires once a plot has been chosen or targeted. (A11)
- **"Walk to it" starts GPS itself** if it is not already running, since being guided somewhere requires a fix and the button that provides one is behind the sheet at that moment. Before a fix arrives it says *"finding you…"* rather than naming a hidden control. (B5)
- The nearest-plot row stands down while a plot is targeted, so only one distance and bearing is on screen at a time. (B6)
- Centring — Follow, and revealing a plot — now means centring in the strip of map between the panel and any open sheet, rather than in the map container that both are covering. (B7)
- The panel's collapse toggle is hidden while a sheet is open. It previously did nothing visible but still flipped the stored state, so the controls silently vanished later when the sheet was closed.

### Defect found while testing the changes

- Deriving the opening instruction inside `setOpen` crashed the whole app: `setOpen` runs during the overlay setup, before the GPS section declares `subEl`, so the hoisted `var` was still `undefined`. Nothing rendered. It is now a guarded helper called again once the GPS elements exist.

### Still open

- Task C, species recording, remains untouched.
- Following yourself while walking to a target still centres on you, so a distant target can be off screen. The arrow and distance carry the guidance, which seems enough on foot, but a "show both" framing is worth trying if it does not.

---

## 3. The same surveyor, checking the machinery underneath

*Run 21 August 2026 against commit a933f5b, driving the parts the first two passes had not exercised: the compass, the Locate/Stop cycle, a restored session, a bad GPS fix, and the phone held sideways.*

The first pass asked whether the tasks were possible, the second whether they were smooth. This one asks whether the app ever tells the surveyor something untrue — because in the field there is nothing to check it against, and a plot marked out in the wrong place stays wrong for years.

### Task B — the guidance you are trusting

| Step | Q1 goal | Q2 action visible | Q3 action associated | Q4 progress visible | Verdict |
|---|---|---|---|---|---|
| Pick the app up again with a plot already targeted | yes | yes | **no** | **no** | **fail** |
| Walk in with a poor fix under tree cover | yes | yes | yes | **no** | **fail** |
| Stop GPS to save battery, walk on, glance down | yes | yes | yes | **no** | **fail** |
| Record where the plot was actually marked | yes | yes | **no** | yes | **fail** |
| Steer by the compass | yes | yes | yes | yes | **pass** |

Issues found:

- **C1 — a rough fix announced arrival anywhere.** Arrival was "within the greater of 4 m and the GPS accuracy", so a ±55 m fix declared *"At plot 8 · mark the plot out from here"* while the surveyor stood 50 m away in the next field. Sharpening the fix then flipped it back to *"50 m to plot 8"*. This is the one failure in three walkthroughs that corrupts data rather than wasting time: a 5 m plot pegged out on the strength of it is in the wrong place permanently. (Q4)
- **C2 — Stop froze the display and said nothing.** Stopping GPS left the grid reference, the accuracy, the blue dot, its accuracy circle and the walk-to distance exactly as they were. Walk 200 m with GPS off, glance down, and the phone still reads *"201 m to plot 8"* over a blue dot that has not moved. Nothing marked any of it as stale. (Q4)
- **C3 — a restored session claimed to be looking for you.** Opening the app with a target saved from last time showed *"walking to plot 8 · finding you…"* while GPS was off and nothing was looking, directly above a readout correctly saying *"Tap Locate to start GPS"*. The app contradicted itself in two adjacent lines. (Q3, Q4)
- **C4 — the position being written down did not say how good it was.** *"Move plot to where I am standing"* recorded the current fix as the plot's real position with no indication of whether that fix was worth ±5 m or ±55 m. (Q3)
- **C5 — the phone held sideways was unusable.** On a 844 × 390 landscape screen the expanded panel was 399 px tall — taller than the screen — and did not scroll, so Save offline, the cache status and the credits were simply unreachable. The square was fitted into the strip below a panel that overflowed past it, putting plots off screen, and opening a plot sheet left a 21 px sliver of visible map. (Q2)
- **C6 — the fit ignored the room beside the panel.** Both fitting the square and centring on a point assumed the panel covers the top of the map. Held sideways the panel is a narrow column with two thirds of the map free to its right, and none of that space was used.

### Task A — the plot list, revisited

Raised by the user while this pass was running:

- **C9 — a plot outline could not be got rid of.** Once the map was zoomed in past 17 every one of the twenty-four plots drew its 5 × 5 m outline, whether or not the surveyor had chosen it. So the square filled with outlines for plots nobody intended to survey, and unchoosing a plot — or never choosing it — did nothing to clear its outline. There was no control anywhere that removed one. (Q2, Q4)
- **C7 — zoomed out, the plots became an unreadable brick.** Every plot carried its number at every zoom. Two steps out from the fitted view the rows were 14 px apart against a 16 px label, so twenty-four numbers overlapped into a solid block that hid the lattice underneath and the chosen plots within it. (Q4)
- **C8 — a chosen plot could not obviously be unchosen.** It *could* — the primary button is a toggle — but once pressed it reads *"✓ Chosen for survey"*, which is a statement of status, not an offer to undo. Nothing on screen said pressing it again would take the plot back off the list, so the choice looked permanent. A function that exists but that nobody can find fails question 3 exactly as if it were missing. (Q2, Q3)

### Checked and working

- **Compass**: granting it and feeding an absolute orientation of alpha 270 produced a heading of 90° E in the readout, rotated the walk-to arrow to −51° for a plot bearing 39° (correctly pointing left of straight ahead), switched the guidance from *"map is north-up"* to *"follow the arrow"*, and turned on the heading cone. **Use heading** stamped 90° into the plot's bearing and persisted it.
- **Locate → Stop → Locate** restarts cleanly and picks the target guidance back up.
- **Save offline** and a full offline reload, again, from a clean cache.
- Plot outlines appear only from zoom 17 and disappear below it; chosen-plot markers stay put either way. After the C9 fix they also come and go with the plot's own state.
- The plot list holds its scroll position while distances update, and the export still copies.

### Changes made

- Arrival now requires a fix good enough to place a 5 m plot: better than ±15 m **and** within the greater of 4 m and the accuracy. A rougher fix reports the true distance and says *"±55 m, too rough to place a plot"* instead of claiming arrival. (C1)
- Stopping GPS removes the position marker and accuracy circle, blanks the grid reference back to *"— no GPS fix —"*, hides the nearest-plot line, and the walk-to row says *"GPS off"*. Nothing is left looking live. (C2, C3)
- The walk-to row distinguishes *"GPS off"* from *"finding you…"*, so it never claims to be searching when it is not. (C3)
- The mark button carries the accuracy of the fix it would record: *"Move plot to where I am standing (±5 m)"*. (C4)
- The panel is capped to the screen and its lower section scrolls, so no control can be pushed out of reach on any screen. (C5)
- Plot markers now follow the zoom: numbered dots while the numbers fit, plain dots once they would collide, and nothing below the point where the whole lattice is smaller than the markers drawn on it — the square outline carries that scale on its own. Chosen and target plots keep their colours at every level, so the plan stays readable zoomed out. (C7)
- A chosen plot's sheet carries an explicit **"Remove plot n from my list"** action, shown only when there is something to remove. The primary button still toggles both ways for anyone who expects that. (C8)
- Fitting and centring now ask whether there is room beside the panel. Held sideways they use it — the whole square sits clear to the right of the panel with every plot on screen — and held upright they behave as before. (C6)
- An outline is drawn only for a plot the surveyor is working with: one that is chosen, one being walked to, or the one whose sheet is open at that moment. Unchoosing a plot takes its outline away, and a plot that was only looked at leaves nothing behind. (C9)

### Defects found while testing the changes

- The arrival guard was applied to a line that did not quite match, so the *message* about a rough fix went in while the *check* it depended on did not. The result was `ReferenceError: usable is not defined` nine times over and a walk-to row frozen on a stale distance — a worse failure than the one being fixed. It only surfaced because the fix was re-tested rather than assumed; a passing syntax check said nothing about it.
- Fixing C7 with a fixed zoom threshold was wrong. The fitted view sits at a different zoom on every screen and moves with the height of the panel, so on a phone with the panel expanded the opening view landed below the threshold and **every plot number disappeared** — while the hint underneath still read *"Tap a numbered plot on the map to choose it"*. The rule now measures how far apart the plots actually land on screen and shows the numbers when there is room for them, which is what the threshold was standing in for.
- Guarding the marker styling with `map.hasLayer` was not enough. Leaflet queues layers added before the map has a view: `hasLayer` reports them immediately, but they have no projected point until the map loads, and the map's first `zoomend` fires ahead of that. Styling one in that window threw inside Leaflet and left the map with no plots at all. The guard now waits for the map to be ready.

### Still open

- Task C, species recording, remains untouched; the extraction is parked in `archive/species-extraction.tar.gz`.
- On a 375 × 667 phone with the panel expanded, the square is squeezed into about 160 px and the plot rows sit 40 px apart. Everything is reachable and tapping the numbers still works, but choosing plots is easier through the Plots list than off the map at that size.
- Following yourself while walking to a target still centres on you, so a distant target can be off screen.

---

## Found by building the test suite

*21 August 2026. Automating the three walkthroughs above turned two of their assumptions into failing tests.*

- **Choosing a plot buried the next one.** Opening a plot slides it into the strip of map left visible while the sheet is up, which is a narrow band because the panel has shrunk to its readout. Closing the sheet lets the panel grow back over exactly that band, so the plot just chosen — and the neighbours the surveyor wants next — ended up behind it and could not be tapped. Closing now slides the plot clear, but only when it actually needs it.
- **Two recentres in quick succession cancelled each other.** A pan already in flight finishes on its own target, so a second one issued before it lands is undone. Tapping a plot and immediately choosing and closing it hit this: the map was measured where the plot was passing through rather than where it was going to land. Both paths now settle any pan in flight first. This is the same class of failure as the `zoomend` pan dropped inside Leaflet's zoom animation, found in the second walkthrough.

Neither was visible by hand at normal speed, and both were reproducible the moment the steps ran without pauses between them.

---

## Answered by the surveyor

*22 August 2026.*

- **The plan could only leave the phone as text.** "Copy my plot list" is right for the NPMS form and no use at all to anything that reads coordinates — the spreadsheet the records live in, the GPS or phone app that will navigate to the plots, QGIS. **Export as a file** now writes the same plan as CSV, GPX or GeoJSON, the GeoJSON carrying each plot's outline as well as its point so a linear plot's 25 m shows where it actually lies. The files are named for the square and the day, and the sheet says which file it wrote rather than leaving the surveyor guessing; on a phone they go out through the share sheet, since a downloaded file on iOS is hard to find again, and a dismissed share sheet claims nothing.

- **A plot could only be moved by standing on it.** "Move plot to where I am standing" is the honest answer on site and the only one the app had, so a plot printed in a ditch could not be shifted at the kitchen table, where the aerial view shows the hedge and the GPS is forty miles away — nor on site when the spot is one you can see but not stand in. **Move plot on the map** now hands the map over: the sheet gets out of the way, a tap puts the plot — marker, number and outline — where the finger went, the bar reports the grid reference and how far that is from the sheet's point, and nothing is written until *Put plot n here*. A tap outside the monad is allowed but called out, panning to look around is not a tap, and *Cancel* leaves the plot exactly where it was.

- **Which end of the plot the point is.** The first walkthrough left open whether the scheme puts the sheet's point at the centre of the plot or at one end, and the app had guessed the centre for both shapes. For the linear plot it is the end: the 25 m starts at the monad point and runs out along the bearing. That makes the bearing a direction rather than an alignment, so it now goes the whole way round the compass — 0–359°, where before it stopped at 179° — and **Use heading** stamps the direction being faced instead of folding a southerly one onto the northern half. The square is unchanged and still straddles the point.
