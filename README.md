# NPMS TL3443 field map

The National Plant Monitoring Scheme square sheet for **TL3443**, georeferenced and overlaid on OpenStreetMap, with live GPS position, heading and accuracy. Built to be used on a phone in the field, including with no signal.

## Using it

- **Locate** starts GPS tracking. The blue dot is your position, the shaded circle is the reported accuracy, and the cone is your heading.
- **Compass** enables the magnetometer for a true heading while standing still. On iOS this needs a tap to grant permission. Without it, heading falls back to GPS course over ground, which only works while you are moving.
- **Follow** keeps the map centred on you. Dragging the map turns it off.
- **Map** fades the OS sheet against the OpenStreetMap base.
- **Save offline** caches the base tiles for the square and its surroundings. The sheet itself, the plot positions and all GPS features are cached automatically on first load and work with no signal regardless.

Add it to your home screen on iOS to get a full-screen app with no browser chrome.

The readout shows your 8-figure grid reference, whether you are inside the square, your accuracy and heading, and the nearest plot with its distance and bearing.

## Accuracy

The square is the OS National Grid monad TL3443: EPSG:27700 E534000–535000, N243000–244000. Georeferencing was derived from the sheet's vector square and cross-checked three ways — against the sheet's scale bar, against the PDF's embedded ESRI geospatial dictionary (agreeing to 1–2 m, within its coordinate rounding), and against the OS National Grid lines drawn in the raster itself (agreeing to ~1 m).

The OSGB36 → WGS84 transformation is accurate to about 1 m, which is well inside typical phone GPS error of 3–10 m. The 24 plot positions sit on an exact 166.667 m lattice, 1/6 in from each edge of the square. Note the lattice position in the top row, fourth column carries no plot, so plots are numbered 1–24 across 25 lattice points.

## Sources and licence

Square sheet from the National Plant Monitoring Scheme (BSBI, CEH, JNCC, Plantlife).

Base mapping is OS 1:25000 colour raster, printed under licence © Crown copyright 2010, Ordnance Survey licence number 100017572. Habitat shading is derived from the CEH Land Cover Map (LCM2007, © NERC (CEH) 2011), Natural England habitat inventories, and CCW Phase 1 habitat survey data (© Countryside Council for Wales). Crown copyright and database right, all rights reserved, © third party licensors.

Base tiles © OpenStreetMap contributors, used under the Open Database Licence.

This site is published `noindex` and is intended for the survey volunteer's own field use, not as a redistribution of Ordnance Survey mapping.
