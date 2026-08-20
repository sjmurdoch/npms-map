import re
c = open('content.txt').read()

# ---- markers: OC4 = Monad_Plots ----
seg = c.split('/OC /OC4 BDC')[1].split('EMC')[0]
rects = re.findall(
    r'([\d.]+) ([\d.]+) m ([\d.]+) ([\d.]+) l ([\d.]+) ([\d.]+) l ([\d.]+) ([\d.]+) l',
    seg)
markers = []
for r in rects:
    v = [float(x) for x in r]
    xs, ys = v[0::2], v[1::2]
    markers.append(((min(xs)+max(xs))/2, (min(ys)+max(ys))/2))
print("markers:", len(markers))

# ---- labels: OC5 = Labels ----
seg5 = c.split('/OC /OC6 BDC')[1].split('EMC')[0]
labels = []
for m in re.finditer(r'([\d.]+) 0 0 ([\d.]+) ([\d.]+) ([\d.]+) Tm(.*?)ET', seg5, re.S):
    x, y = float(m.group(3)), float(m.group(4))
    txt = ''.join(re.findall(r'\((.)\)Tj', m.group(5)))
    if txt.isdigit():
        labels.append((x, y, txt))
print("labels:", len(labels), sorted(int(t) for _,_,t in labels))

# pair each marker with nearest label below it
out = []
for mx, my in markers:
    best = min(labels, key=lambda L: (abs(L[0]+4-mx)*2 + abs(my-L[1])))
    out.append((int(best[2]), mx, my))
out.sort()
for n, x, y in out:
    print("%2d  x=%9.4f y=%9.4f" % (n, x, y))
import json
json.dump(out, open('plots_pdf.json','w'))
