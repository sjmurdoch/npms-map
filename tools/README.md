# Rebuilding the overlay

`build_overlay.py` turns the NPMS square sheet PDF into the georeferenced Web Mercator PNG used by the app. The source PDF is not committed — it is licensed NPMS/OS material. Put `TL3443.pdf` alongside these scripts to rebuild.

Pipeline:

1. Read the thick black square from the PDF's `Monads` optional-content layer. Its corners are the OS grid square TL3443, i.e. EPSG:27700 E534000–535000, N243000–244000. This is confirmed independently by the sheet's scale bar (473.78 pt = 1 km) and by the PDF's own ESRI `/Measure` `/GEO` dictionary, whose `GPTS` corners agree to 1–2 m once you account for them being OSGB36 (Airy 1830) rather than WGS84 latitudes.
2. Strip every optional-content layer except `Image`, so the overlay carries only the OS raster and habitat shading — no legend, title, scale bar or printed plot markers. Those are redrawn as vectors in the app.
3. Render at 600 dpi, downsample to the raster's native ~0.5 m/px, then warp EPSG:27700 → EPSG:3857 by inverse mapping with bilinear sampling, so it drops straight into a Leaflet `imageOverlay`.
4. Emit `geo.js`: square corners, plot positions, and an affine EPSG:27700 ↔ EPSG:3857 fit (residual < 0.45 m over a 3 km box) that the app inverts to turn a GPS fix into a grid reference without shipping a projection library.

Plot positions are snapped to the exact k/6 lattice (166.667 m spacing, 1/6 in from each edge). The PDF's own coordinates drift up to 0.25 m from this because of rounding in the ArcMap export; the design intent is clearly an even lattice, so the exact values are used.

Requires `uv`, plus `pdftoppm` and `qpdf` from poppler/qpdf.

```
uv run --with pillow --with pyproj --with numpy --with scipy python build_overlay.py
```
