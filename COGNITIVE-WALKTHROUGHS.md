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

**Not addressed in this round**, at the user's direction, to keep the change focused on defining plots and on the location problems. Recorded here as a known gap: the app has nothing for species at all, so every question fails at every step, and the surveyor still needs the printed species list and a paper recording sheet. A working extraction of the NPMS *Species Identification Guide* (410 entries with habitat, difficulty class, Wildflower-level flag and flowering months) exists on disk as `species.js` and `tools/extract_species.py` but is deliberately not wired into the app.

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
