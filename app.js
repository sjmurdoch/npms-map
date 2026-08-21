/* NPMS TL3443 field map.
   Overlays the georeferenced NPMS square sheet on OpenStreetMap and shows live
   GPS position, heading and accuracy. Plots can be chosen at home, walked to on
   site and marked out to scale. Works offline once "Save offline" has run. */
(function () {
  "use strict";

  var TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png";
  // Zoom -> margin around the square, as a fraction of its size. Wide context is
  // cheap at low zoom; at z18 it is kept tight so the whole download stays a
  // couple of hundred tiles, in line with OSM's tile usage policy.
  var PREFETCH = { 14: 0.5, 15: 0.5, 16: 0.4, 17: 0.25, 18: 0.08 };

  var PLOT_GOAL = 5;              // plots the NPMS asks for in a square
  var FOOT_ZOOM = 17;             // below this the plot outline is too small to read
  // Detail follows how far apart the plots actually land on screen, not a guessed
  // zoom: the fitted view sits at a different zoom on every phone and depends on
  // how tall the panel is, and at 15 the numbers were vanishing from the opening
  // view while the hint still said to tap one.
  var LABEL_GAP = 34;             // px between plots needed to fit a number label
  var DOT_GAP = 9;                // below this the dots themselves merge
  var POOR_FIX = 15;              // metres: past this a fix cannot place a 5 m plot
  var SQUARE_M = 5;               // NPMS square plot: 5 x 5 m
  var LINEAR_M = [25, 1];         // NPMS linear plot: 25 x 1 m

  // The eleven NPMS broad habitats, as named in the scheme's guidance.
  var HABITATS = [
    ["", "— habitat not set —"],
    ["woodland", "Broadleaved woodland, hedges & scrub"],
    ["pinewood", "Native pinewood & juniper scrub"],
    ["arable", "Arable field margins"],
    ["lowland-grass", "Lowland grassland"],
    ["upland-grass", "Upland grassland"],
    ["heath", "Heathland"],
    ["bog", "Bog & wet heath"],
    ["marsh", "Marsh & fen"],
    ["freshwater", "Freshwater"],
    ["rock", "Rock outcrops, cliffs & screes"],
    ["coast", "Coast"]
  ];

  // ---------------------------------------------------------------- helpers
  var A = GEO.affine, cx = A.cx, cy = A.cy;
  var det = cx[0] * cy[1] - cx[1] * cy[0];

  // EPSG:3857 -> EPSG:27700, inverting the affine fitted in the build step
  // (residual < 0.45 m over a 3 km box centred on the square).
  function llToBng(lat, lon) {
    var p = L.CRS.EPSG3857.project(L.latLng(lat, lon));
    var dx = p.x - cx[2], dy = p.y - cy[2];
    return {
      e: A.E0 + (cy[1] * dx - cx[1] * dy) / det,
      n: A.N0 + (-cy[0] * dx + cx[0] * dy) / det
    };
  }

  // ...and back the other way, for drawing metre-accurate shapes on the ground.
  function bngToLL(e, n) {
    var de = e - A.E0, dn = n - A.N0;
    return L.CRS.EPSG3857.unproject(L.point(
      cx[0] * de + cx[1] * dn + cx[2],
      cy[0] * de + cy[1] * dn + cy[2]));
  }

  function gridRef(e, n, figs) {
    if (e < 500000 || e >= 600000 || n < 200000 || n >= 300000) {
      return "E" + Math.round(e) + " N" + Math.round(n);
    }
    var d = (figs || 8) / 2, div = Math.pow(10, 5 - d);
    var ei = Math.floor((e - 500000) / div), ni = Math.floor((n - 200000) / div);
    return "TL " + String(ei).padStart(d, "0") + " " + String(ni).padStart(d, "0");
  }

  function compassPoint(d) {
    return ["N","NNE","NE","ENE","E","ESE","SE","SSE",
            "S","SSW","SW","WSW","W","WNW","NW","NNW"][Math.round(d / 22.5) % 16];
  }

  // bilinear interpolation across the square's four exact corners
  function fracToLatLng(fe, fn) {
    var s = GEO.square, c = [s.sw, s.nw, s.ne, s.se];
    var w = [(1 - fe) * (1 - fn), (1 - fe) * fn, fe * fn, fe * (1 - fn)];
    var lat = 0, lng = 0;
    for (var i = 0; i < 4; i++) { lat += w[i] * c[i][0]; lng += w[i] * c[i][1]; }
    return L.latLng(lat, lng);
  }

  var $ = function (id) { return document.getElementById(id); };

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  function habitatName(key) {
    for (var i = 0; i < HABITATS.length; i++) if (HABITATS[i][0] === key) return HABITATS[i][1];
    return HABITATS[0][1];
  }

  // ------------------------------------------------------------ survey notes
  // One record per plot the surveyor has taken an interest in. Kept in
  // localStorage so a square planned on the sofa is still there in the field.
  var STORE = "tl3443.survey";
  var survey = { plots: {}, target: null };
  try {
    var raw = localStorage.getItem(STORE);
    if (raw) survey = JSON.parse(raw);
  } catch (e) {}
  survey.plots = survey.plots || {};

  function save() {
    try { localStorage.setItem(STORE, JSON.stringify(survey)); } catch (e) {}
  }
  function rec(n, make) {
    var r = survey.plots[n];
    if (!r && make) { r = survey.plots[n] = { chosen: false, habitat: "", shape: "square",
                                              bearing: 0, marked: null, note: "" }; }
    return r || null;
  }
  function isChosen(n) { var r = rec(n); return !!(r && r.chosen); }
  function chosenCount() {
    return Object.keys(survey.plots).filter(function (n) { return survey.plots[n].chosen; }).length;
  }
  function plotByNum(n) {
    for (var i = 0; i < GEO.plots.length; i++) if (GEO.plots[i].n === n) return GEO.plots[i];
    return null;
  }
  // Where the plot actually is: the sheet's lattice point, or where it was marked out.
  function plotPos(p) {
    var r = rec(p.n);
    return (r && r.marked) ? r.marked : { e: p.e, n: p.n_ };
  }

  // ------------------------------------------------------------------- map
  var map = L.map("map", { zoomControl: true, maxZoom: 20, zoomSnap: 0.5, tap: false });
  map.zoomControl.setPosition("topright");

  // Layers added before the map has a view are queued: hasLayer already reports
  // them, but they have no projected point until the map loads, and the first
  // zoomend fires ahead of that. Styling one in between throws inside Leaflet.
  var mapReady = false;
  map.whenReady(function () { mapReady = true; });

  L.tileLayer(TILE_URL, {
    maxZoom: 20, maxNativeZoom: 19, crossOrigin: true,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map);

  var overlay = L.imageOverlay("tl3443_overlay.png", GEO.overlayBounds, {
    opacity: 0.85, interactive: false
  }).addTo(map);

  L.control.scale({ imperial: false, position: "bottomright" }).addTo(map);

  var sq = GEO.square;
  L.polygon([sq.sw, sq.nw, sq.ne, sq.se],
            { color: "#000", weight: 2.5, fill: false, interactive: false }).addTo(map);
  for (var i = 1; i <= 2; i++) {
    var f = i / 3;
    L.polyline([fracToLatLng(f, 0), fracToLatLng(f, 1)],
      { color: "#555", weight: 1, dashArray: "5,5", interactive: false }).addTo(map);
    L.polyline([fracToLatLng(0, f), fracToLatLng(1, f)],
      { color: "#555", weight: 1, dashArray: "5,5", interactive: false }).addTo(map);
  }

  // ------------------------------------------------------------- plot layers
  var footGroup = L.layerGroup().addTo(map);
  var plotLayers = {};
  var halo = L.circleMarker([0, 0], { radius: 17, color: "#4da3ff", weight: 3,
                                      fill: false, interactive: false });
  // "full" numbered plots, "dots" plain markers once the numbers would collide,
  // "none" once the whole lattice is smaller than the markers drawn on it.
  var detail = "full";

  // Corners of a plot's ground footprint, in the order they would be walked.
  function footCorners(p) {
    var r = rec(p.n), pos = plotPos(p);
    var linear = !!(r && r.shape === "linear");
    var a = ((r && r.bearing) || 0) * Math.PI / 180;
    var along = linear ? LINEAR_M[0] / 2 : SQUARE_M / 2;
    var across = linear ? LINEAR_M[1] / 2 : SQUARE_M / 2;
    var ue = Math.sin(a), un = Math.cos(a);            // unit vector along the plot
    var out = [];
    [[1, 1], [1, -1], [-1, -1], [-1, 1]].forEach(function (s) {
      out.push(bngToLL(pos.e + s[0] * along * ue + s[1] * across * un,
                       pos.n + s[0] * along * un - s[1] * across * ue));
    });
    return out;
  }

  GEO.plots.forEach(function (p) {
    var open = function () { showPlot(p.n, false); };
    // The dot is 16 px across, which is not a finger. An invisible disc around
    // it, and the number itself, are the actual tap target.
    var hit = L.circleMarker([p.lat, p.lon], {
      radius: 22, stroke: false, fillColor: "#000", fillOpacity: 0
    }).addTo(map);
    hit.on("click", open);
    var marker = L.circleMarker([p.lat, p.lon], {
      radius: 8, color: "#000", weight: 2, fillColor: "#fff", fillOpacity: 1
    }).addTo(map);
    marker.on("click", open);
    var label = L.marker([p.lat, p.lon], {
      icon: L.divIcon({ className: "plot-lbl", html: p.n, iconSize: [24, 16], iconAnchor: [12, -10] })
    }).addTo(map);
    label.on("click", open);
    var foot = L.polygon(footCorners(p), {
      className: "plot-foot", color: "#000", weight: 1.5,
      fillOpacity: .12, interactive: false
    });
    plotLayers[p.n] = { p: p, hit: hit, marker: marker, label: label, foot: foot };
  });

  function refreshPlot(n) {
    var l = plotLayers[n];
    if (!l) return;
    var chosen = isChosen(n), target = survey.target === n;
    var full = detail === "full";
    var pos = plotPos(l.p), ll = bngToLL(pos.e, pos.n);
    l.hit.setLatLng(ll);
    l.marker.setLatLng(ll);
    l.label.setLatLng(ll);
    // Styling a circle that is not attached and projected throws inside Leaflet:
    // it has no point to recompute its bounds from.
    if (mapReady && map.hasLayer(l.marker)) {
      l.hit.setRadius(full ? 22 : 10);
      l.marker.setRadius(full ? 8 : 4);
      l.marker.setStyle({
        fillColor: chosen ? "#5fd18b" : "#fff",
        color: target ? "#ff8c00" : "#000",
        weight: target ? (full ? 4 : 3) : (full ? 2 : 1.5)
      });
    }
    var el = l.label.getElement();
    if (el) {          // toggle only: Leaflet's own classes position the label
      el.classList.toggle("chosen", chosen && !target);
      el.classList.toggle("target", target);
    }
    l.foot.setLatLngs(footCorners(l.p));
    l.foot.setStyle({ color: target ? "#ff8c00" : chosen ? "#1d7a49" : "#000",
                      weight: target || chosen ? 2 : 1.5,
                      fillColor: chosen ? "#5fd18b" : "#fff" });

    // An outline belongs to a plot the surveyor is actually working with. Drawn
    // for all twenty-four it is clutter that unchoosing the plot cannot clear.
    var open = sheetView && sheetView.kind === "plot" && sheetView.n === n;
    var showFoot = map.getZoom() >= FOOT_ZOOM && (chosen || target || open);
    if (showFoot !== footGroup.hasLayer(l.foot)) {
      showFoot ? footGroup.addLayer(l.foot) : footGroup.removeLayer(l.foot);
    }
  }

  // Zoomed out, twenty-four numbered labels overlap into an unreadable brick, so
  // the plots drop to plain dots and then out altogether, leaving the square.
  // Screen distance between neighbouring lattice points, i.e. how much room a
  // plot has to itself.
  function latticeGap() {
    var p = GEO.plots[0];
    var a = map.latLngToContainerPoint(bngToLL(p.e, p.n_));
    var b = map.latLngToContainerPoint(bngToLL(p.e, p.n_ + 166.667));
    return Math.abs(a.y - b.y);
  }

  function syncDetail() {
    var gap = latticeGap();
    var want = gap >= LABEL_GAP ? "full" : gap >= DOT_GAP ? "dots" : "none";
    if (want === detail) return;
    detail = want;
    GEO.plots.forEach(function (p) {
      var l = plotLayers[p.n];
      var showLabel = detail === "full", showDot = detail !== "none";
      if (showLabel !== map.hasLayer(l.label)) {
        showLabel ? l.label.addTo(map) : map.removeLayer(l.label);
      }
      if (showDot !== map.hasLayer(l.marker)) {
        showDot ? l.marker.addTo(map) : map.removeLayer(l.marker);
        showDot ? l.hit.addTo(map) : map.removeLayer(l.hit);
      }
    });
  }

  function refreshAllPlots() {
    GEO.plots.forEach(function (p) { refreshPlot(p.n); });
  }
  map.on("zoomend", function () {
    syncDetail();
    refreshAllPlots();
    // Zooming keeps the map centre, which sits behind the sheet: hold the plot
    // being looked at in the strip of map that is still visible.
    if (sheetView && sheetView.kind === "plot") reveal(sheetView.n);
  });

  var squareBounds = L.latLngBounds([sq.sw, sq.nw, sq.ne, sq.se]);

  // The panel covers the top-left of the map. Held upright there is no room
  // beside it, so the map has to start below it; held sideways the panel is a
  // column and the map should start to its right instead of being squeezed
  // into the strip underneath.
  function panelClear() {
    var panel = $("panel").getBoundingClientRect(), size = map.getSize();
    return (size.x - panel.right > 240)
      ? { left: panel.right + 12, top: 20 }
      : { left: 20, top: Math.min(panel.height + 12, size.y * 0.55) };
  }

  function fitSquare() {
    var pad = panelClear();
    map.fitBounds(squareBounds, {
      paddingTopLeft: [pad.left, pad.top],
      paddingBottomRight: [20, 30]
    });
  }

  // --------------------------------------------------------------- overlay
  var op = $("op"), opv = $("opv"), btnSheet = $("btnSheet");
  var lastOpacity = 85;
  function syncOpacity() {
    overlay.setOpacity(op.value / 100);
    opv.textContent = op.value + "%";
    var on = +op.value > 0;
    if (on) lastOpacity = +op.value;
    btnSheet.textContent = on ? "Hide sheet" : "Show sheet";
  }
  op.addEventListener("input", syncOpacity);
  syncOpacity();                       // browsers restore slider state on reload
  // One tap to see the roads, tracks and field boundaries the sheet is covering.
  btnSheet.addEventListener("click", function () {
    op.value = +op.value > 0 ? 0 : lastOpacity;
    syncOpacity();
  });

  var moreEl = $("more"), toggleEl = $("toggle");
  // Until there is a fix the readout doubles as the opening instruction, so it
  // has to name the button the user can actually see.
  function hintOpening(open) {
    if (!subEl || watchId != null || gpsMarker) return;
    subEl.textContent = open ? "Tap Locate to start GPS" : "Tap \u25be then Locate";
  }
  function setOpen(open) {
    moreEl.classList.toggle("open", open);
    hintOpening(open);
    toggleEl.textContent = open ? "▴" : "▾";
    toggleEl.setAttribute("aria-expanded", String(open));
    toggleEl.setAttribute("aria-label", open ? "Hide controls" : "Show controls");
    try { localStorage.setItem("tl3443.open", open ? "1" : "0"); } catch (e) {}
  }
  toggleEl.addEventListener("click", function () { setOpen(!moreEl.classList.contains("open")); });
  var wasOpen = "1";
  try { wasOpen = localStorage.getItem("tl3443.open") || "1"; } catch (e) {}
  setOpen(wasOpen === "1");
  fitSquare();                         // needs the panel laid out to pad around it
  $("btnFit").addEventListener("click", fitSquare);

  // ------------------------------------------------------------------- GPS
  var gpsMarker = null, accCircle = null, watchId = null;
  var following = false, heading = null, headingSrc = "";
  var here = null;                     // latest fix as BNG easting/northing
  var lGrid = $("lGrid"), subEl = $("sub"), nearEl = $("near");
  var btnLocate = $("btnLocate"), btnFollow = $("btnFollow"), btnCompass = $("btnCompass");
  hintOpening(moreEl.classList.contains("open"));

  var gpsIcon = L.divIcon({
    className: "", iconSize: [0, 0],
    html: '<div class="gps-wrap">' +
            '<div class="gps-rot" id="gpsRot">' +
              '<svg width="68" height="68" viewBox="0 0 68 68">' +
                '<defs><radialGradient id="cg" cx="50%" cy="100%" r="100%">' +
                  '<stop offset="0%" stop-color="#4da3ff" stop-opacity=".8"/>' +
                  '<stop offset="100%" stop-color="#4da3ff" stop-opacity="0"/>' +
                '</radialGradient></defs>' +
                '<path id="cone" d="M34 34 L18 4 A34 34 0 0 1 50 4 Z" fill="url(#cg)" opacity="0"/>' +
              '</svg>' +
            '</div><div class="gps-dot"></div></div>'
  });

  function applyHeading() {
    var rot = $("gpsRot");
    if (rot) {
      var cone = rot.querySelector("#cone");
      if (heading == null) { cone.setAttribute("opacity", "0"); }
      else {
        cone.setAttribute("opacity", "1");
        rot.style.transform = "rotate(" + heading.toFixed(1) + "deg)";
      }
    }
    syncNav();
  }

  function onPosition(pos) {
    var c = pos.coords, ll = L.latLng(c.latitude, c.longitude);

    if (!gpsMarker) {
      accCircle = L.circle(ll, { radius: c.accuracy, color: "#4da3ff", weight: 1,
        fillColor: "#4da3ff", fillOpacity: .15, interactive: false }).addTo(map);
      gpsMarker = L.marker(ll, { icon: gpsIcon, interactive: false, zIndexOffset: 1000 }).addTo(map);
    } else {
      gpsMarker.setLatLng(ll);
      accCircle.setLatLng(ll).setRadius(c.accuracy);
    }

    // course over ground is a usable heading when moving, if there is no compass
    if (headingSrc !== "compass" && c.heading != null && !isNaN(c.heading) && c.speed > 0.5) {
      heading = c.heading; headingSrc = "GPS";
    }
    applyHeading();
    // Following normally centres on you; with a plot open it holds that plot in
    // the visible strip instead, so marking out shows both you and the outline.
    if (following) {
      if (sheetView && sheetView.kind === "plot") reveal(sheetView.n);
      else centreInView(ll, true);
    }

    var b = llToBng(c.latitude, c.longitude);
    here = { e: b.e, n: b.n, acc: c.accuracy };
    var s = GEO.sq_bng;
    var inSq = b.e >= s.e0 && b.e <= s.e1 && b.n >= s.n0 && b.n <= s.n1;

    // Collapsed view shows only what matters in the field:
    // 10-figure (1 m) grid reference, heading, and GPS accuracy.
    lGrid.textContent = gridRef(b.e, b.n, 10);
    lGrid.className = inSq ? "" : "out";
    subEl.innerHTML =
      (heading == null ? "<b>—</b>° " : "<b>" + Math.round(heading) + "</b>° " + compassPoint(heading)) +
      " · <b>±" + Math.round(c.accuracy) + "</b> m" +
      (inSq ? "" : ' · <span class="bad">outside square</span>');

    var best = null;
    GEO.plots.forEach(function (p) {
      var q = plotPos(p), d = Math.hypot(q.e - b.e, q.n - b.n);
      if (!best || d < best.d) best = { p: p, d: d };
    });
    if (best) {
      nearest = best.p.n;
      nearEl.style.display = survey.target ? "none" : "block";
      var brg = bearingTo(best.p);
      nearEl.innerHTML = "<span>Nearest plot</span> <b>" + best.p.n + "</b> · " +
        Math.round(best.d) + " m · " + Math.round(brg) + "° " + compassPoint(brg) +
        ' <span>— tap to open</span>';
    }
    syncNav();
    updateDistances();
  }

  function onPosError(err) {
    stopLocate();
    lGrid.className = "none"; lGrid.textContent = "— GPS unavailable —";
    subEl.textContent = err.message;
  }

  function startLocate() {
    if (!navigator.geolocation || !window.isSecureContext) {
      lGrid.className = "none"; lGrid.textContent = "— GPS unavailable —";
      subEl.textContent = "Needs https:// or localhost";
      return;
    }
    watchId = navigator.geolocation.watchPosition(onPosition, onPosError,
      { enableHighAccuracy: true, maximumAge: 1000, timeout: 20000 });
    btnLocate.setAttribute("aria-pressed", "true");
    btnLocate.textContent = "Stop";
    subEl.textContent = "Acquiring fix…";
    btnFollow.disabled = false;
    following = true; btnFollow.setAttribute("aria-pressed", "true");
    requestWakeLock();
  }

  function stopLocate() {
    if (watchId != null) navigator.geolocation.clearWatch(watchId);
    watchId = null;
    btnLocate.setAttribute("aria-pressed", "false");
    btnLocate.textContent = "Locate";
    btnFollow.disabled = true; following = false;
    btnFollow.setAttribute("aria-pressed", "false");
    releaseWakeLock();
    // Once fixes stop arriving nothing may go on looking live: a frozen dot and
    // a frozen distance are worse than no dot and no distance.
    if (gpsMarker) { map.removeLayer(gpsMarker); gpsMarker = null; }
    if (accCircle) { map.removeLayer(accCircle); accCircle = null; }
    here = null;
    lGrid.className = "none"; lGrid.textContent = "— no GPS fix —";
    nearEl.style.display = "none";
    hintOpening(moreEl.classList.contains("open"));
    syncNav();
  }

  btnLocate.addEventListener("click", function () { watchId == null ? startLocate() : stopLocate(); });
  btnFollow.addEventListener("click", function () {
    following = !following;
    btnFollow.setAttribute("aria-pressed", String(following));
    if (following && gpsMarker) centreInView(gpsMarker.getLatLng(), true);
  });
  map.on("dragstart", function () {
    if (following) { following = false; btnFollow.setAttribute("aria-pressed", "false"); }
  });

  // ------------------------------------------------- walking to a chosen plot
  var navEl = $("nav"), navArrow = $("navArrow"), navDist = $("navDist"),
      navWhich = $("navWhich"), navStop = $("navStop");
  var nearest = null, arrived = false, navLine = null;

  function bearingTo(p) {
    if (!here) return 0;
    var q = plotPos(p);
    return (Math.atan2(q.e - here.e, q.n - here.n) * 180 / Math.PI + 360) % 360;
  }
  function distanceTo(p) {
    if (!here) return null;
    var q = plotPos(p);
    return Math.hypot(q.e - here.e, q.n - here.n);
  }

  function setTarget(n) {
    var was = survey.target;
    survey.target = (survey.target === n) ? null : n;
    arrived = false;
    save();
    // You cannot be guided anywhere without a fix, and the Locate button is
    // behind the sheet at this point, so asking to walk there starts it.
    if (survey.target && watchId == null) startLocate();
    if (was) refreshPlot(was);
    if (survey.target) refreshPlot(survey.target);
    if (nearest) nearEl.style.display = survey.target ? "none" : "block";
    syncPanel();
    syncNav();
    if (sheetView) renderSheet();
  }
  navStop.addEventListener("click", function (e) { e.stopPropagation(); setTarget(survey.target); });
  navEl.addEventListener("click", function () { if (survey.target) showPlot(survey.target, false); });

  function syncNav() {
    var n = survey.target, p = n && plotByNum(n);
    navEl.classList.toggle("on", !!p);
    if (!p) {
      if (navLine) { map.removeLayer(navLine); navLine = null; }
      return;
    }
    var d = distanceTo(p);
    if (d == null) {
      navDist.textContent = "—";
      navWhich.textContent = "walking to plot " + n +
        (watchId == null ? " · GPS off" : " · finding you…");
      navArrow.style.transform = "";
      return;
    }
    var brg = bearingTo(p);
    // With a heading the arrow points where to walk; without one it is drawn
    // against the map, which is north-up.
    navArrow.style.transform = "rotate(" + (brg - (heading == null ? 0 : heading)).toFixed(0) + "deg)";

    // A +-50 m fix would otherwise announce arrival anywhere in the field, and
    // a plot marked out on the strength of it is in the wrong place for good.
    var usable = (here.acc || 0) <= POOR_FIX;
    var close = usable && d <= Math.max(4, here.acc || 0);
    navEl.classList.toggle("here", close);
    if (close) {
      navDist.textContent = "At plot " + n;
      navWhich.textContent = "±" + Math.round(here.acc) + " m GPS · mark the plot out from here";
      if (!arrived) {
        arrived = true;
        if (navigator.vibrate) { try { navigator.vibrate(120); } catch (e) {} }
      }
    } else {
      arrived = false;
      navDist.textContent = (d < 1000 ? Math.round(d) + " m" : (d / 1000).toFixed(2) + " km") +
                            " to plot " + n;
      navWhich.textContent = Math.round(brg) + "° " + compassPoint(brg) +
        (!usable ? " · ±" + Math.round(here.acc) + " m, too rough to place a plot"
                 : heading == null ? " · map is north-up" : " · follow the arrow");
    }

    var q = plotPos(p), ll = bngToLL(q.e, q.n);
    var pts = [gpsMarker ? gpsMarker.getLatLng() : ll, ll];
    if (!navLine) {
      navLine = L.polyline(pts, { color: "#ff8c00", weight: 2.5, dashArray: "7,6",
                                  interactive: false }).addTo(map);
    } else navLine.setLatLngs(pts);
  }

  nearEl.addEventListener("click", function () { if (nearest) showPlot(nearest, false); });

  // --------------------------------------------------------------- compass
  function headingFromEvent(e) {
    if (typeof e.webkitCompassHeading === "number" && !isNaN(e.webkitCompassHeading)) {
      return e.webkitCompassHeading;                 // iOS: true-north, clockwise
    }
    if (e.absolute && e.alpha != null) {
      var scr = (screen.orientation && screen.orientation.angle) || 0;
      return (360 - e.alpha + scr) % 360;
    }
    return null;
  }
  function onOrientation(e) {
    var h = headingFromEvent(e);
    if (h == null || isNaN(h)) return;
    heading = h; headingSrc = "compass"; applyHeading();
  }
  function attachCompass() {
    window.addEventListener("deviceorientationabsolute", onOrientation, true);
    window.addEventListener("deviceorientation", onOrientation, true);
    btnCompass.setAttribute("aria-pressed", "true");
    btnCompass.textContent = "Compass on";
  }
  btnCompass.addEventListener("click", function () {
    var D = window.DeviceOrientationEvent;
    if (D && typeof D.requestPermission === "function") {      // iOS 13+
      D.requestPermission().then(function (s) {
        if (s === "granted") attachCompass(); else btnCompass.textContent = "Denied";
      }).catch(function () { btnCompass.textContent = "Unavailable"; });
    } else if (D) { attachCompass(); }
    else { btnCompass.textContent = "No compass"; btnCompass.disabled = true; }
  });

  // -------------------------------------------------------------- wake lock
  var wakeLock = null;
  function requestWakeLock() {
    if (!navigator.wakeLock) return;
    navigator.wakeLock.request("screen").then(function (l) { wakeLock = l; }).catch(function () {});
  }
  function releaseWakeLock() {
    if (wakeLock) { wakeLock.release().catch(function () {}); wakeLock = null; }
  }
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "visible" && watchId != null) requestWakeLock();
  });

  // ------------------------------------------------------------ plot sheets
  var sheet = $("sheet"), sheetTitle = $("sheetTitle"),
      sheetBody = $("sheetBody"), sheetBack = $("sheetBack"), sheetClose = $("sheetClose");
  var sheetView = null;

  function closeSheet() {
    var was = sheetView && sheetView.kind === "plot" ? sheetView.n : null;
    sheetView = null;
    sheet.classList.remove("open");
    document.body.classList.remove("sheeting");
    toggleEl.hidden = false;
    map.removeLayer(halo);
    if (was) refreshPlot(was);          // its outline was on loan while open
  }
  sheetClose.addEventListener("click", closeSheet);
  sheetBack.addEventListener("click", function () { showPlots(); });

  function openSheet(view) {
    var was = sheetView && sheetView.kind === "plot" ? sheetView.n : null;
    sheetView = view;
    sheet.classList.add("open");
    document.body.classList.add("sheeting");
    toggleEl.hidden = true;
    sheetBack.hidden = !view.back;
    renderSheet();
    sheetBody.scrollTop = 0;
    if (was && was !== view.n) refreshPlot(was);
    if (view.kind === "plot") { refreshPlot(view.n); reveal(view.n, true); }
    else map.removeLayer(halo);
  }

  // The panel covers the top of the map and a sheet covers the bottom, so
  // "centred" has to mean centred in what is left, or the thing being centred
  // ends up underneath one of them.
  function centreInView(ll, animate) {
    var size = map.getSize(), pad = panelClear();
    var bottom = sheet.classList.contains("open")
      ? sheet.getBoundingClientRect().top : size.y;
    var wantX = (pad.left + size.x) / 2;
    var wantY = (pad.top + bottom) / 2;
    var at = map.latLngToContainerPoint(ll);
    // Recentre rather than pan by an offset: a pan issued from zoomend lands in
    // the middle of Leaflet's zoom animation and is dropped.
    map.setView(map.containerPointToLatLng(
      size.divideBy(2).add(L.point(at.x - wantX, at.y - wantY))),
      map.getZoom(), { animate: !!animate, duration: .3 });
  }

  // Slide the map so the plot being looked at sits in the strip of map left
  // between the readout and the sheet.
  function reveal(n, animate) {
    var p = plotByNum(n);
    if (!p) return;
    var pos = plotPos(p), ll = bngToLL(pos.e, pos.n);
    halo.setLatLng(ll).addTo(map).bringToFront();
    centreInView(ll, animate);
  }
  function renderSheet() {
    if (!sheetView) return;
    if (sheetView.kind === "plots") renderPlots(); else renderPlot();
  }
  function showPlots() { openSheet({ kind: "plots" }); }
  function showPlot(n, back) { openSheet({ kind: "plot", n: n, back: !!back }); }

  // ---- the list of all 24 plots
  function renderPlots() {
    sheetTitle.innerHTML = "Plots for survey<small>" + chosenCount() + " of " + PLOT_GOAL +
      " chosen · tap a plot to see it and choose it</small>";
    var html = ['<p class="sub">Pick plots in semi-natural habitat you can reach. ' +
                'Fade the NPMS sheet to check access and field boundaries underneath.</p>'];
    GEO.plots.forEach(function (p) {
      var r = rec(p.n), d = distanceTo(p);
      var cls = "plot-row" + (isChosen(p.n) ? " chosen" : "") +
                (survey.target === p.n ? " target" : "");
      html.push('<button class="' + cls + '" data-plot="' + p.n + '">' +
        '<span class="num">' + p.n + "</span>" +
        '<span class="who">' + gridRef(p.e, p.n_, 8) +
          "<i>" + esc(!isChosen(p.n) ? "" :
            (r.habitat ? habitatName(r.habitat) : "habitat not set")) +
          (r && r.marked ? " · marked out" : "") + "</i></span>" +
        '<span class="far">' + (d == null ? "" : Math.round(d) + " m") + "</span></button>");
    });
    html.push('<div class="stack"><button id="btnExport">Copy my plot list</button></div>');
    sheetBody.innerHTML = html.join("");
    sheetBody.querySelectorAll("[data-plot]").forEach(function (b) {
      b.addEventListener("click", function () { showPlot(+b.dataset.plot, true); });
    });
    $("btnExport").addEventListener("click", exportPlots);
  }

  // Each new fix only rewrites the distances: re-rendering the whole list would
  // throw away the reader's scroll position a few times a second.
  function updateDistances() {
    if (!sheetView || sheetView.kind !== "plots") return;
    sheetBody.querySelectorAll("[data-plot]").forEach(function (b) {
      var d = distanceTo(plotByNum(+b.dataset.plot));
      b.querySelector(".far").textContent = d == null ? "" : Math.round(d) + " m";
    });
  }

  // ---- one plot: choose it, walk to it, mark it out
  function renderPlot() {
    var n = sheetView.n, p = plotByNum(n), r = rec(n, true);
    var pos = plotPos(p), d = distanceTo(p);
    var moved = r.marked ? Math.hypot(r.marked.e - p.e, r.marked.n - p.n_) : 0;

    sheetTitle.innerHTML = "Plot " + n + "<small>" + gridRef(pos.e, pos.n, 10) +
      (d == null ? "" : " · " + Math.round(d) + " m away") + "</small>";

    var h = [];
    h.push('<div class="row" style="margin-top:0">' +
      '<button id="pChoose" aria-pressed="' + (r.chosen ? "true" : "false") + '">' +
        (r.chosen ? "✓ Chosen for survey" : "Choose for survey") + "</button>" +
      '<button id="pGo" aria-pressed="' + (survey.target === n ? "true" : "false") + '">' +
        (survey.target === n ? "Walking here" : "Walk to it") + "</button></div>");
    // A pressed button reads as a status, not as something to press again, so
    // taking a plot back off the list needs saying out loud.
    if (r.chosen) {
      h.push('<div class="stack"><button id="pDrop" class="quiet">' +
             "Remove plot " + n + " from my list</button></div>");
    }

    h.push('<p class="sub">Habitat</p><select id="pHab">' +
      HABITATS.map(function (o) {
        return '<option value="' + o[0] + '"' + (o[0] === r.habitat ? " selected" : "") +
               ">" + esc(o[1]) + "</option>";
      }).join("") + "</select>");

    h.push('<p class="sub">Plot shape — drawn to scale once you zoom in</p>' +
      '<div class="row" style="margin-top:8px">' +
      '<button id="pSq" aria-pressed="' + (r.shape !== "linear") + '">Square 5 × 5 m</button>' +
      '<button id="pLin" aria-pressed="' + (r.shape === "linear") + '">Linear 25 × 1 m</button></div>' +
      '<div class="row"><label for="pBrg">Bearing</label>' +
      '<input type="range" id="pBrg" min="0" max="179" value="' + (r.bearing || 0) + '">' +
      '<span id="pBrgV" style="width:3.2em;text-align:right;color:var(--muted);font-size:12px">' +
      (r.bearing || 0) + '°</span>' +
      '<button id="pBrgHead" style="flex:0 0 auto;min-height:34px;padding:6px 8px">Use heading</button></div>');

    h.push('<p class="sub">Where the plot really is</p>');
    if (r.marked) {
      h.push('<p class="sub" style="color:var(--ok)">Marked at ' + gridRef(r.marked.e, r.marked.n, 10) +
        " · " + moved.toFixed(0) + " m from the sheet's point</p>");
    } else {
      h.push('<p class="sub">Using the point printed on the NPMS sheet. If that spot is ' +
        'unsuitable, move the plot and record where you actually put it.</p>');
    }
    h.push('<div class="stack"><button id="pMark"' + (here ? "" : " disabled") + '>' +
      (here ? "Move plot to where I am standing (±" + Math.round(here.acc) + " m)"
            : "Move plot here — needs a GPS fix") + "</button>" +
      (r.marked ? '<button id="pUnmark">Put it back on the sheet’s point</button>' : "") +
      "</div>");

    h.push('<p class="sub">Notes</p><textarea id="pNote" placeholder="Access, landowner, what is growing, why you moved it…">' +
      esc(r.note || "") + "</textarea>");

    sheetBody.innerHTML = h.join("");

    function setChosen(v) {
      r.chosen = v; save(); refreshPlot(n); syncPanel(); renderPlot();
    }
    $("pChoose").addEventListener("click", function () { setChosen(!r.chosen); });
    if ($("pDrop")) $("pDrop").addEventListener("click", function () { setChosen(false); });
    $("pGo").addEventListener("click", function () { setTarget(n); });
    $("pHab").addEventListener("change", function () {
      r.habitat = this.value; save(); syncPanel();
    });
    $("pSq").addEventListener("click", function () { r.shape = "square"; save(); refreshPlot(n); renderPlot(); });
    $("pLin").addEventListener("click", function () { r.shape = "linear"; save(); refreshPlot(n); renderPlot(); });
    var brg = $("pBrg"), brgV = $("pBrgV");
    brg.addEventListener("input", function () {
      r.bearing = +brg.value; brgV.textContent = brg.value + "°"; refreshPlot(n);
    });
    brg.addEventListener("change", save);
    $("pBrgHead").addEventListener("click", function () {
      if (heading == null) { brgV.textContent = "no compass"; return; }
      r.bearing = Math.round(heading) % 180;
      brg.value = r.bearing; brgV.textContent = r.bearing + "°";
      save(); refreshPlot(n);
    });
    $("pMark").addEventListener("click", function () {
      if (!here) return;
      r.marked = { e: here.e, n: here.n }; r.chosen = true;
      save(); refreshPlot(n); syncPanel(); syncNav(); renderPlot();
    });
    if ($("pUnmark")) $("pUnmark").addEventListener("click", function () {
      r.marked = null; save(); refreshPlot(n); syncNav(); renderPlot();
    });
    $("pNote").addEventListener("input", function () { r.note = this.value; save(); });
  }

  // ---- hand the plan over to the NPMS form, or to a text to yourself
  function exportPlots() {
    var lines = ["NPMS " + GEO.name + " — plots chosen"];
    GEO.plots.forEach(function (p) {
      var r = rec(p.n);
      if (!r || !r.chosen) return;
      var pos = plotPos(p);
      lines.push("");
      lines.push("Plot " + p.n + "  " + gridRef(pos.e, pos.n, 10) +
                 (r.marked ? " (marked out)" : " (sheet point)"));
      lines.push("  Habitat: " + (r.habitat ? habitatName(r.habitat) : "not set"));
      lines.push("  Plot: " + (r.shape === "linear" ? "25 × 1 m linear" : "5 × 5 m square") +
                 ", bearing " + (r.bearing || 0) + "°");
      if (r.note) lines.push("  Notes: " + r.note);
    });
    if (lines.length === 1) lines.push("", "(none chosen yet)");
    var text = lines.join("\n");
    if (navigator.share) {
      navigator.share({ title: "NPMS " + GEO.name + " plots", text: text }).catch(function () {});
    } else if (navigator.clipboard) {
      navigator.clipboard.writeText(text).then(function () {
        var b = $("btnExport");
        b.textContent = "Copied to clipboard";
        setTimeout(function () { if (b.isConnected) b.textContent = "Copy my plot list"; }, 4000);
      }).catch(function () { window.prompt("Copy your plot list", text); });
    } else {
      window.prompt("Copy your plot list", text);
    }
  }

  // ---------------------------------------------------------- panel summary
  var btnPlots = $("btnPlots"), hintEl = $("hint");
  function syncPanel() {
    var c = chosenCount();
    btnPlots.innerHTML = "Plots for survey — <b>" + c + " of " + PLOT_GOAL + " chosen</b>";
    // The hint has done its job once the surveyor has engaged with any plot.
    hintEl.style.display = (c || survey.target) ? "none" : "block";
  }
  btnPlots.addEventListener("click", showPlots);

  syncDetail();
  refreshAllPlots();
  syncPanel();
  syncNav();

  // ---------------------------------------------------------------- offline
  var statusEl = $("status"), barEl = $("prog"), barFill = barEl.firstElementChild;
  var btnOffline = $("btnOffline");

  function tileUrls() {
    var b = squareBounds, urls = [];
    Object.keys(PREFETCH).forEach(function (zs) {
      var z = +zs, pad = PREFETCH[zs];
      var dLat = (b.getNorth() - b.getSouth()) * pad,
          dLon = (b.getEast() - b.getWest()) * pad;
      var p1 = map.project(L.latLng(b.getNorth() + dLat, b.getWest() - dLon), z).divideBy(256).floor();
      var p2 = map.project(L.latLng(b.getSouth() - dLat, b.getEast() + dLon), z).divideBy(256).floor();
      for (var x = p1.x; x <= p2.x; x++)
        for (var y = p1.y; y <= p2.y; y++)
          urls.push(TILE_URL.replace("{z}", z).replace("{x}", x).replace("{y}", y));
    });
    return urls;
  }

  function setStatus(html, cls) { statusEl.innerHTML = cls ? '<span class="' + cls + '">' + html + "</span>" : html; }

  btnOffline.addEventListener("click", function () {
    if (!navigator.serviceWorker || !navigator.serviceWorker.controller) {
      setStatus("Offline cache unavailable (needs https).", "bad"); return;
    }
    var urls = tileUrls();
    btnOffline.disabled = true;
    barEl.style.display = "block";
    setStatus("Downloading " + urls.length + " map tiles…");
    navigator.serviceWorker.controller.postMessage({ type: "PREFETCH", urls: urls });
  });

  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("sw.js").then(function () {
      return navigator.serviceWorker.ready;
    }).then(function () {
      if (!navigator.serviceWorker.controller) { setStatus("Offline cache ready after reload."); return; }
      navigator.serviceWorker.controller.postMessage({ type: "STATUS" });
    }).catch(function (e) { setStatus("No offline cache: " + e.message, "bad"); });

    navigator.serviceWorker.addEventListener("message", function (ev) {
      var d = ev.data || {};
      if (d.type === "PROGRESS") {
        barFill.style.width = (100 * d.done / d.total).toFixed(1) + "%";
        setStatus("Downloading tiles… " + d.done + " / " + d.total);
      } else if (d.type === "DONE") {
        barEl.style.display = "none"; barFill.style.width = "0";
        btnOffline.disabled = false;
        setStatus("Offline ready · " + d.tiles + " tiles cached" +
                  (d.failed ? " (" + d.failed + " failed)" : ""), "good");
      } else if (d.type === "STATUS") {
        setStatus(d.tiles
          ? "Offline ready · " + d.tiles + " tiles cached"
          : "Map sheet cached. Tap “Save offline” for base tiles.", d.tiles ? "good" : null);
      }
    });
  } else {
    setStatus("Offline cache not supported.", "bad");
  }

  window.addEventListener("online",  function () { setStatus("Back online."); });
  window.addEventListener("offline", function () { setStatus("Offline — using cached map.", "bad"); });
})();
