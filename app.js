/* NPMS TL3443 field map.
   Overlays the georeferenced NPMS square sheet on OpenStreetMap and shows live
   GPS position, heading and accuracy. Works offline once "Save offline" has run. */
(function () {
  "use strict";

  var TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png";
  // Zoom -> margin around the square, as a fraction of its size. Wide context is
  // cheap at low zoom; at z18 it is kept tight so the whole download stays a
  // couple of hundred tiles, in line with OSM's tile usage policy.
  var PREFETCH = { 14: 0.5, 15: 0.5, 16: 0.4, 17: 0.25, 18: 0.08 };

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

  // ------------------------------------------------------------------- map
  var map = L.map("map", { zoomControl: true, maxZoom: 20, zoomSnap: 0.5, tap: false });
  map.zoomControl.setPosition("topright");

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

  GEO.plots.forEach(function (p) {
    L.circleMarker([p.lat, p.lon], {
      radius: 6, color: "#000", weight: 2, fillColor: "#fff", fillOpacity: 1
    }).addTo(map).bindPopup(
      "<b>Plot " + p.n + "</b><br>" + gridRef(p.e, p.n_, 8) +
      "<br>E " + p.e.toFixed(1) + " &nbsp; N " + p.n_.toFixed(1) +
      "<br>" + p.lat.toFixed(6) + ", " + p.lon.toFixed(6));
    L.marker([p.lat, p.lon], {
      interactive: false,
      icon: L.divIcon({ className: "plot-lbl", html: p.n, iconSize: [24, 16], iconAnchor: [12, -8] })
    }).addTo(map);
  });

  var squareBounds = L.latLngBounds([sq.sw, sq.nw, sq.ne, sq.se]);
  function fitSquare() { map.fitBounds(squareBounds, { padding: [20, 20] }); }
  fitSquare();

  // --------------------------------------------------------------- overlay
  var op = $("op"), opv = $("opv");
  function syncOpacity() { overlay.setOpacity(op.value / 100); opv.textContent = op.value + "%"; }
  op.addEventListener("input", syncOpacity);
  syncOpacity();                       // browsers restore slider state on reload

  $("toggle").addEventListener("click", function () {
    var b = $("body"), hidden = b.classList.toggle("collapsed");
    this.textContent = hidden ? "+" : "–";
    this.setAttribute("aria-expanded", String(!hidden));
  });
  $("btnFit").addEventListener("click", fitSquare);

  // ------------------------------------------------------------------- GPS
  var gpsMarker = null, accCircle = null, watchId = null;
  var following = false, heading = null, headingSrc = "";
  var rGrid = $("rGrid"), rAcc = $("rAcc"), rNear = $("rNear");
  var btnLocate = $("btnLocate"), btnFollow = $("btnFollow"), btnCompass = $("btnCompass");

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
    if (!rot) return;
    var cone = rot.querySelector("#cone");
    if (heading == null) { cone.setAttribute("opacity", "0"); return; }
    cone.setAttribute("opacity", "1");
    rot.style.transform = "rotate(" + heading.toFixed(1) + "deg)";
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
    if (following) map.panTo(ll, { animate: true, duration: .5 });

    var b = llToBng(c.latitude, c.longitude);
    var s = GEO.sq_bng;
    var inSq = b.e >= s.e0 && b.e <= s.e1 && b.n >= s.n0 && b.n <= s.n1;
    rGrid.innerHTML = gridRef(b.e, b.n, 8) +
      '<div class="k" style="margin-top:2px">' +
      (inSq ? '<span class="good">inside TL3443</span>' : '<span class="bad">outside TL3443</span>') +
      "</div>";

    rAcc.textContent = "±" + Math.round(c.accuracy) + " m" +
      (heading == null ? " · no heading"
        : " · " + Math.round(heading) + "° " + compassPoint(heading) + " (" + headingSrc + ")");

    var best = null;
    GEO.plots.forEach(function (p) {
      var d = Math.hypot(p.e - b.e, p.n_ - b.n);
      if (!best || d < best.d) best = { p: p, d: d };
    });
    if (best) {
      var brg = (Math.atan2(best.p.e - b.e, best.p.n_ - b.n) * 180 / Math.PI + 360) % 360;
      rNear.textContent = "Plot " + best.p.n + " · " + Math.round(best.d) + " m · " +
                          Math.round(brg) + "° " + compassPoint(brg);
    }
  }

  function onPosError(err) {
    rGrid.innerHTML = '<span class="bad">GPS: ' + err.message + "</span>";
    stopLocate();
  }

  function startLocate() {
    if (!navigator.geolocation) { rGrid.innerHTML = '<span class="bad">No geolocation</span>'; return; }
    if (!window.isSecureContext) {
      rGrid.innerHTML = '<span class="bad">Needs https:// or localhost</span>'; return;
    }
    watchId = navigator.geolocation.watchPosition(onPosition, onPosError,
      { enableHighAccuracy: true, maximumAge: 1000, timeout: 20000 });
    btnLocate.setAttribute("aria-pressed", "true");
    btnLocate.textContent = "Stop";
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
  }

  btnLocate.addEventListener("click", function () { watchId == null ? startLocate() : stopLocate(); });
  btnFollow.addEventListener("click", function () {
    following = !following;
    btnFollow.setAttribute("aria-pressed", String(following));
    if (following && gpsMarker) map.panTo(gpsMarker.getLatLng());
  });
  map.on("dragstart", function () {
    if (following) { following = false; btnFollow.setAttribute("aria-pressed", "false"); }
  });

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

  // ---------------------------------------------------------------- offline
  var statusEl = $("status"), barEl = $("bar"), barFill = barEl.firstElementChild;
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
