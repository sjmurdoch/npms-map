# NPMS TL3443 field map

The National Plant Monitoring Scheme square sheet for **TL3443**, georeferenced and overlaid on OpenStreetMap, with live GPS position, heading and accuracy. Built to be used on a phone in the field, including with no signal.

## Choosing and marking out plots

- Tap a numbered plot to open it. **Choose for survey** adds it to your list; the panel counts how many you have. Chosen plots turn green, and *Remove plot n from my list* takes one back off. Zoomed out the numbers drop away and the plots become plain dots, so the lattice stays readable.
- Each plot carries its **habitat**, its **shape** — a 5 × 5 m square or a 25 × 1 m linear plot — the **bearing** it lies along, and a free note. Zoomed in past about 30 m across, the plot is drawn on the map at its true size, so you can see how it sits against a hedge or a field edge. Only plots you have chosen, are walking to, or have open are outlined — the rest stay as plain markers. **Use heading** sets the bearing from the compass, for laying a linear plot along the feature you are standing next to.
- **Walk to it** puts a guidance row under the readout — arrow, distance, bearing — that stays visible with the panel collapsed. The arrow points where to walk if the compass is on, and against the north-up map if it is not. Inside the greater of 4 m and your GPS accuracy it changes to *At plot n* — but only once the fix is good enough to place a plot at all. A fix worse than ±15 m says so instead of claiming you have arrived, and stopping GPS clears the readout rather than leaving the last position looking live.
- If the printed point is unusable, **Move plot to where I am standing** records where you actually put the plot and reports how far that is from the sheet's point.
- **Copy my plot list** hands the whole plan over as plain text for the NPMS form.

Everything you choose is kept on the device and works with no signal.

## Using the map

- **Locate** starts GPS tracking. The blue dot is your position, the shaded circle is the reported accuracy, and the cone is your heading.
- **Compass** enables the magnetometer for a true heading while standing still. On iOS this needs a tap to grant permission. Without it, heading falls back to GPS course over ground, which only works while you are moving.
- **Follow** keeps the map centred on you. Dragging the map turns it off.
- **NPMS sheet** fades the OS sheet against the OpenStreetMap base; **Hide sheet** does it in one tap, for checking access and field boundaries underneath. The legend under the slider names what the sheet's habitat shading means.
- **Save offline** caches the base tiles for the square and its surroundings. The sheet itself, the plot positions and all GPS features are cached automatically on first load and work with no signal regardless.

Add it to your home screen on iOS to get a full-screen app with no browser chrome.

The readout shows your grid reference, whether you are inside the square, your accuracy and heading, and the nearest plot with its distance and bearing.

## Tests

The suite drives the real app in a headless browser: it serves the working tree, stubs geolocation so accuracy and heading can be set exactly, and checks the georeferencing data, the plot workflow, the walk-to guidance, marker detail, layout on a phone held either way, and a full offline start.

```
uv run playwright install chromium     # once
uv run pytest
```

`-m "not slow"` skips the service-worker tests, which need a real install cycle. Run the whole suite before committing.

## Accuracy

The square is the OS National Grid monad TL3443: EPSG:27700 E534000–535000, N243000–244000. Georeferencing was derived from the sheet's vector square and cross-checked three ways — against the sheet's scale bar, against the PDF's embedded ESRI geospatial dictionary (agreeing to 1–2 m, within its coordinate rounding), and against the OS National Grid lines drawn in the raster itself (agreeing to ~1 m).

The OSGB36 → WGS84 transformation is accurate to about 1 m, which is well inside typical phone GPS error of 3–10 m. The 24 plot positions sit on an exact 166.667 m lattice, 1/6 in from each edge of the square. Note the lattice position in the top row, fourth column carries no plot, so plots are numbered 1–24 across 25 lattice points.

## Sources and licence

Square sheet from the National Plant Monitoring Scheme (BSBI, CEH, JNCC, Plantlife).

Base mapping is OS 1:25000 colour raster, printed under licence © Crown copyright 2010, Ordnance Survey licence number 100017572. Habitat shading is derived from the CEH Land Cover Map (LCM2007, © NERC (CEH) 2011), Natural England habitat inventories, and CCW Phase 1 habitat survey data (© Countryside Council for Wales). Crown copyright and database right, all rights reserved, © third party licensors.

Base tiles © OpenStreetMap contributors, used under the Open Database Licence.

This site is published `noindex` and is intended for the survey volunteer's own field use, not as a redistribution of Ordnance Survey mapping.
