import json, math, numpy as np
from PIL import Image
from pyproj import Transformer
from scipy.ndimage import map_coordinates

# ---------- PDF user-space geometry (points) ----------
SQ = dict(x0=61.92295, x1=535.70552, y0=319.43223, y1=793.48733)   # Monads layer = TL3443
FR = dict(x0=15.3607,  x1=582.268,   y0=284.628,   y1=828.291)     # map frame / viewport BBox
E0, E1, N0, N1 = 534000.0, 535000.0, 243000.0, 244000.0            # TL3443 in EPSG:27700

def pdf_to_bng(x, y):
    return (E0 + (x - SQ['x0']) / (SQ['x1'] - SQ['x0']) * (E1 - E0),
            N0 + (y - SQ['y0']) / (SQ['y1'] - SQ['y0']) * (N1 - N0))

def bng_to_pdf(e, n):
    return (SQ['x0'] + (e - E0) / (E1 - E0) * (SQ['x1'] - SQ['x0']),
            SQ['y0'] + (n - N0) / (N1 - N0) * (SQ['y1'] - SQ['y0']))

to4326 = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)
to3857 = Transformer.from_crs("EPSG:27700", "EPSG:3857", always_xy=True)
m3857_to_4326 = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
to27700_from3857 = Transformer.from_crs("EPSG:3857", "EPSG:27700", always_xy=True)

# ---------- source raster ----------
DPI = 600
src = Image.open('page600_map.png').convert('RGB')
# down to ~native content resolution (300 dpi) with a good prefilter
src = src.resize((src.width // 2, src.height // 2), Image.LANCZOS)
SDPI = DPI / 2
PAGE_H_PT = 841.49291
def pdf_to_px(x, y):          # -> source pixel coords (col, row)
    return (x * SDPI / 72.0, (PAGE_H_PT - y) * SDPI / 72.0)

# ---------- output grid: axis-aligned in EPSG:3857 ----------
fr_corners_pdf = [(FR['x0'],FR['y0']),(FR['x0'],FR['y1']),(FR['x1'],FR['y1']),(FR['x1'],FR['y0'])]
fr_bng = [pdf_to_bng(*p) for p in fr_corners_pdf]
fr_merc = [to3857.transform(e, n) for e, n in fr_bng]
mx = [p[0] for p in fr_merc]; my = [p[1] for p in fr_merc]
MINX, MAXX, MINY, MAXY = min(mx), max(mx), min(my), max(my)

lat_mid = to4326.transform(*pdf_to_bng((FR['x0']+FR['x1'])/2, (FR['y0']+FR['y1'])/2))[1]
merc_per_ground = 1.0 / math.cos(math.radians(lat_mid))
GROUND_RES = 0.5                                   # metres/pixel on the ground
res = GROUND_RES * merc_per_ground                 # metres/pixel in EPSG:3857
W = int(round((MAXX - MINX) / res)); H = int(round((MAXY - MINY) / res))
print(f"output {W} x {H} px, {GROUND_RES} m/px ground, {res:.4f} m/px mercator")

cols = MINX + (np.arange(W) + 0.5) * res
rows = MAXY - (np.arange(H) + 0.5) * res
GX, GY = np.meshgrid(cols, rows)
E, N = to27700_from3857.transform(GX.ravel(), GY.ravel())
PX, PY = bng_to_pdf(E, N)
SC, SR = pdf_to_px(PX, PY)
SC = SC.reshape(H, W); SR = SR.reshape(H, W)

# valid = inside the map frame
fx0, fy0 = pdf_to_px(FR['x0'], FR['y1'])           # top-left of frame in px
fx1, fy1 = pdf_to_px(FR['x1'], FR['y0'])           # bottom-right
valid = (SC >= fx0) & (SC <= fx1) & (SR >= fy0) & (SR <= fy1)
print("valid coverage %.1f%%" % (100 * valid.mean()))

a = np.asarray(src, dtype=np.float32)
out = np.zeros((H, W, 4), dtype=np.uint8)
coords = np.stack([SR.ravel(), SC.ravel()])
for ch in range(3):
    out[:, :, ch] = np.clip(
        map_coordinates(a[:, :, ch], coords, order=1, mode='nearest'), 0, 255
    ).reshape(H, W).astype(np.uint8)
out[:, :, 3] = np.where(valid, 255, 0)
img = Image.fromarray(out, 'RGBA')
img.save('tl3443_overlay_rgba.png')
print("rgba png bytes:", __import__('os').path.getsize('tl3443_overlay_rgba.png'))

# ---------- geometry for the web app ----------
def ll(e, n):
    lon, lat = to4326.transform(e, n); return [round(lat, 8), round(lon, 8)]

square = {k: ll(*v) for k, v in
          dict(sw=(E0,N0), nw=(E0,N1), ne=(E1,N1), se=(E1,N0)).items()}

# plots: exact k/6 lattice; 24 plots, lattice cell (col4,row5) omitted
plots = []
num = 0
for r in range(1, 6):
    for c in range(1, 6):
        if r == 5 and c == 4:
            continue
        num += 1
        e = E0 + c * (E1 - E0) / 6.0
        n = N0 + r * (N1 - N0) / 6.0
        lat, lon = ll(e, n)
        plots.append(dict(n=num, e=round(e,2), n_=round(n,2), lat=lat, lon=lon,
                          gr="TL%03d%03d" % (round(e-500000)//1, round(n-200000)//1)))
data = dict(
    square_wgs84=square,
    overlay_bounds_3857=[MINX, MINY, MAXX, MAXY],
    overlay_bounds_wgs84=[list(reversed(m3857_to_4326.transform(MINX, MINY))),
                          list(reversed(m3857_to_4326.transform(MAXX, MAXY)))],
    square_3857={k: list(to3857.transform(*v)) for k, v in
                 dict(sw=(E0,N0), nw=(E0,N1), ne=(E1,N1), se=(E1,N0)).items()},
    grid3x3_bng=[E0 + i*(E1-E0)/3 for i in range(4)],
    plots=plots, size=[W, H], res_3857=res,
)
json.dump(data, open('geo.json','w'), indent=1)

# ---------- verify: affine fit BNG<->3857 over the square ----------
ge, gn = np.meshgrid(np.linspace(E0,E1,11), np.linspace(N0,N1,11))
gx, gy = to3857.transform(ge.ravel(), gn.ravel())
A = np.column_stack([ge.ravel()-E0, gn.ravel()-N0, np.ones(gx.size)])
cx, *_ = np.linalg.lstsq(A, gx, rcond=None)
cy, *_ = np.linalg.lstsq(A, gy, rcond=None)
rx = gx - A@cx; ry = gy - A@cy
resid = np.hypot(rx, ry) / merc_per_ground
print("affine BNG->3857 residual over square: max %.3f m, rms %.3f m" % (resid.max(), resid.std()))
json.dump(dict(cx=list(cx), cy=list(cy)), open('affine.json','w'))
