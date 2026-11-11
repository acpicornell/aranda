"use strict";

let DATA = null;

const AGE_GROUPS = ["0-7", "7-16", "16-25", "25-40", "40-50", "50+"];
const AGE_LABELS = {
  "0-7": "0–7", "7-16": "7–16", "16-25": "16–25",
  "25-40": "25–40", "40-50": "40–50", "50+": "50+",
};

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
const fmt = (n) => (n == null ? "—" : n.toLocaleString("ca-ES"));

function esc(s) {
  return String(s ?? "").replace(/[&<>"]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

// ===== tabs =====
function initTabs() {
  $$(".tab").forEach((btn) => {
    btn.addEventListener("click", () => {
      $$(".tab").forEach((b) => b.classList.remove("active"));
      $$(".tab-content").forEach((c) => c.classList.remove("active"));
      btn.classList.add("active");
      $(`#tab-${btn.dataset.tab}`).classList.add("active");
      if (btn.dataset.tab === "mapa") renderMap();
      if (btn.dataset.tab === "demografia") renderDemografia();
    });
  });
}

// ===== demografia =====
const AGE_MID = { "0-7": 3.5, "7-16": 11.5, "16-25": 20.5, "25-40": 32.5, "40-50": 45, "50+": 60 };
let demoDone = false;

// Palma was censused as its 6 historic parishes; label them so they're distinct.
const PALMA_PARR = {
  "Santa Eulalia": "Santa Eulàlia", "Santa Cruz": "Santa Creu",
  "San Jaime": "Sant Jaume", "San Miguel": "Sant Miquel",
  "San Nicolás": "Sant Nicolau", "Nuestra Señora de la Asunción": "l'Assumpció",
};
function palmaParrLabel(s) { return PALMA_PARR[s] || s || "—"; }
function displayName(p) {
  const base = p.name_catalan || p.name_modern;
  return (base === "Palma" && p.parroquia) ? "Palma · " + palmaParrLabel(p.parroquia) : base;
}

function reconciledSC(p) {
  const sc = p.sum_check;
  return sc === "ok" || (sc && typeof sc === "object" && sc.ok === true);
}
// Aggregate distributions (pyramid, marital) need cells that sum to the total.
function pueblosReconciled() {
  return DATA.pueblos.filter((p) => !p.is_aggregate && reconciledSC(p) && p.demografia && p.demografia.by_age);
}
// Per-pueblo indicators: every pueblo with verified var/hem and an age table.
function pueblosPerPueblo() {
  return DATA.pueblos.filter((p) => !p.is_aggregate && p.demografia && p.demografia.by_age &&
    Number.isInteger(p.demografia.var) && Number.isInteger(p.demografia.hem));
}
function cellN(c, k) { return Number.isInteger(c && c[k]) ? c[k] : 0; }

function puebloIndicators(p) {
  const dem = p.demografia, ba = dem.by_age;
  let num = 0, u16 = 0, a1650 = 0, o50 = 0, casAd = 0, totAd = 0, N = 0;
  for (const g of AGE_GROUPS) {
    const c = ba[g];
    const t = cellN(c, "cas_var") + cellN(c, "sol_var") + cellN(c, "cas_hem") + cellN(c, "sol_hem");
    N += t; num += AGE_MID[g] * t;
    if (g === "0-7" || g === "7-16") u16 += t;
    else if (g === "50+") o50 += t;
    else a1650 += t;
    if (g !== "0-7" && g !== "7-16") {
      casAd += cellN(c, "cas_var") + cellN(c, "cas_hem");
      totAd += t;
    }
  }
  // Sex ratio from the verified var/hem spine (exact for all pueblos), not the cells.
  const V = dem.var, H = dem.hem;
  return {
    pop: p.total_animes, name: displayName(p), n: p.pueblo_n,
    sex: H ? (100 * V / H) : null,
    age: N ? (num / N) : null,
    dep: a1650 ? (100 * (u16 + o50) / a1650) : null,
    aging: u16 ? (o50 / u16) : null,
    married: totAd ? (100 * casAd / totAd) : null,
    reconciled: reconciledSC(p),
  };
}

function renderDemografia() {
  if (demoDone) return;
  demoDone = true;
  const full = pueblosReconciled();
  $("#demo-n").textContent = full.length;
  const counted = DATA.pueblos.filter((p) => !p.is_aggregate);

  // aggregate by age group
  const agg = {};
  AGE_GROUPS.forEach((g) => agg[g] = { V: 0, H: 0, casV: 0, casH: 0, solV: 0, solH: 0 });
  full.forEach((p) => {
    const ba = p.demografia.by_age;
    AGE_GROUPS.forEach((g) => {
      const c = ba[g];
      agg[g].V += cellN(c, "cas_var") + cellN(c, "sol_var");
      agg[g].H += cellN(c, "cas_hem") + cellN(c, "sol_hem");
      agg[g].casV += cellN(c, "cas_var"); agg[g].casH += cellN(c, "cas_hem");
      agg[g].solV += cellN(c, "sol_var"); agg[g].solH += cellN(c, "sol_hem");
    });
  });
  const Nrec = AGE_GROUPS.reduce((s, g) => s + agg[g].V + agg[g].H, 0);
  const totV = AGE_GROUPS.reduce((s, g) => s + agg[g].V, 0);
  const totH = AGE_GROUPS.reduce((s, g) => s + agg[g].H, 0);
  const totPop = counted.reduce((s, p) => s + (p.total_animes || 0), 0);
  const meanAge = AGE_GROUPS.reduce((s, g) => s + AGE_MID[g] * (agg[g].V + agg[g].H), 0) / Nrec;
  const u16 = agg["0-7"].V + agg["0-7"].H + agg["7-16"].V + agg["7-16"].H;
  const o50 = agg["50+"].V + agg["50+"].H;

  // KPIs
  const kpis = [
    [fmt(totPop), "ànimes (54 pobles)"],
    [(100 * totV / totH).toFixed(1), "homes / 100 dones"],
    [meanAge.toFixed(1), "edat mitjana"],
    [(100 * u16 / Nrec).toFixed(0) + "%", "menors de 16"],
    [(o50 / u16).toFixed(2), "índex d'envelliment"],
  ];
  $("#demo-kpis").innerHTML = kpis.map(([v, k]) =>
    `<div class="kpi"><span class="v">${v}</span><span class="k">${k}</span></div>`).join("");

  // pyramid
  const maxCell = Math.max(...AGE_GROUPS.map((g) => Math.max(agg[g].V, agg[g].H)));
  $("#demo-pyramid").innerHTML = AGE_GROUPS.slice().reverse().map((g) => {
    const wv = (100 * agg[g].V / maxCell).toFixed(1), wh = (100 * agg[g].H / maxCell).toFixed(1);
    return `<div class="pyr-row">` +
      `<span class="pyr-val r">${fmt(agg[g].V)}</span>` +
      `<span class="pyr-bar-l"><span class="pyr-bar male" style="width:${wv}%"></span></span>` +
      `<span class="pyr-age">${AGE_LABELS[g]}</span>` +
      `<span class="pyr-bar-r"><span class="pyr-bar female" style="width:${wh}%"></span></span>` +
      `<span class="pyr-val">${fmt(agg[g].H)}</span></div>`;
  }).join("") +
    `<div class="pyr-row pyr-head"><span class="pyr-val r">♂ homes</span><span class="pyr-bar-l"></span><span class="pyr-age"></span><span class="pyr-bar-r"></span><span class="pyr-val">dones ♀</span></div>`;

  // marital by age (adults only meaningful, but show all)
  $("#demo-marital").innerHTML = AGE_GROUPS.map((g) => {
    const mv = agg[g].casV, sv = agg[g].solV, mh = agg[g].casH, sh = agg[g].solH;
    const tv = mv + sv || 1, th = mh + sh || 1;
    const bar = (cas, tot, lbl) => {
      const pc = (100 * cas / tot).toFixed(0);
      return `<div class="ms-row"><span class="ms-lbl">${lbl}</span>` +
        `<span class="ms-bar"><span class="ms-cas" style="width:${pc}%"></span><span class="ms-sol" style="width:${100 - pc}%"></span></span>` +
        `<span class="ms-pc">${pc}% cas.</span></div>`;
    };
    return `<div class="ms-group"><div class="ms-g-title">${AGE_LABELS[g]}</div>` +
      bar(mv, tv, "♂") + bar(mh, th, "♀") + `</div>`;
  }).join("");

  // per-pueblo indicators — all 54 (sex ratio from the verified var/hem spine)
  window._demoInd = pueblosPerPueblo().map(puebloIndicators);
  renderSexRatio();
  renderPopRank();
  renderPalma();
  renderExentos();
  renderIndicators("pop", true);

  $("#ratio-topn").addEventListener("change", renderSexRatio);
  $("#poprank-topn").addEventListener("change", renderPopRank);
  $("#ind-topn").addEventListener("change", () => {
    const s = window._demoSort || { k: "pop", desc: true };
    renderIndicators(s.k, s.desc);
  });
  $$("#tab-demografia .indicators-table th.sortable").forEach((th) => {
    th.addEventListener("click", () => {
      const k = th.dataset.k;
      const desc = window._demoSort && window._demoSort.k === k ? !window._demoSort.desc : true;
      renderIndicators(k, desc);
    });
  });
}

function attachRowClicks(sel) {
  $$(sel).forEach((row) => row.addEventListener("click", () => {
    const p = DATA.pueblos.find((x) => x.pueblo_n == row.dataset.n); if (p) openDetail(p);
  }));
}

function topN(id) { return parseInt($(id).value, 10) || 0; }

function renderSexRatio() {
  const n = topN("#ratio-topn");
  const all = window._demoInd.filter((x) => x.sex != null);
  // pick the N most imbalanced, then order by ratio for a readable diverging chart
  let rows = all.slice().sort((a, b) => Math.abs(b.sex - 100) - Math.abs(a.sex - 100));
  if (n > 0) rows = rows.slice(0, n);
  rows.sort((a, b) => a.sex - b.sex);
  const maxDev = Math.max(...all.map((x) => Math.abs(x.sex - 100)), 20);
  $("#demo-ratio").innerHTML = rows.map((x) => {
    const dev = x.sex - 100, w = (50 * Math.abs(dev) / maxDev).toFixed(1);
    const side = dev >= 0 ? "right" : "left";
    return `<div class="rt-row" data-n="${x.n}"><span class="rt-name" title="${esc(x.name)}">${esc(x.name)}</span>` +
      `<span class="rt-track"><span class="rt-bar ${side}" style="width:${w}%"></span></span>` +
      `<span class="rt-val">${x.sex.toFixed(0)}</span></div>`;
  }).join("");
  attachRowClicks("#demo-ratio .rt-row");
}

function renderPopRank() {
  const n = topN("#poprank-topn");
  let rows = window._demoInd.slice().sort((a, b) => b.pop - a.pop);
  if (n > 0) rows = rows.slice(0, n);
  const max = Math.max(...window._demoInd.map((x) => x.pop), 1);
  $("#demo-poprank").innerHTML = rows.map((x) => {
    const w = (100 * x.pop / max).toFixed(1);
    const sex = x.sex != null ? Math.round(x.sex) : "—";
    return `<div class="pr-row" data-n="${x.n}"><span class="rt-name" title="${esc(x.name)}">${esc(x.name)}</span>` +
      `<span class="pr-track"><span class="pr-bar" style="width:${w}%"></span></span>` +
      `<span class="rt-val">${fmt(x.pop)} · ♂${sex}</span></div>`;
  }).join("");
  attachRowClicks("#demo-poprank .pr-row");
}

// The city of Palma, broken down into its 6 historic parishes.
function renderPalma() {
  const par = DATA.pueblos.filter((p) => !p.is_aggregate &&
    (p.name_catalan || p.name_modern) === "Palma" && p.demografia &&
    Number.isInteger(p.total_animes));
  if (!par.length) return;
  const rows = par.slice().sort((a, b) => b.total_animes - a.total_animes);
  const total = rows.reduce((s, p) => s + p.total_animes, 0);
  const totMallorca = DATA.pueblos
    .filter((p) => !p.is_aggregate)
    .reduce((s, p) => s + (p.total_animes || 0), 0);
  const max = Math.max(...rows.map((p) => p.total_animes), 1);
  $("#palma-total").textContent = fmt(total);
  $("#palma-share").textContent = (100 * total / totMallorca).toFixed(0);
  $("#demo-palma").innerHTML = rows.map((p) => {
    const w = (100 * p.total_animes / max).toFixed(1);
    const dem = p.demografia;
    const sex = dem.hem ? Math.round(100 * dem.var / dem.hem) : "—";
    const lbl = palmaParrLabel(p.parroquia);
    return `<div class="pr-row" data-n="${p.pueblo_n}"><span class="rt-name" title="${esc(p.parroquia || lbl)}">${esc(lbl)}</span>` +
      `<span class="pr-track"><span class="pr-bar" style="width:${w}%"></span></span>` +
      `<span class="rt-val">${fmt(p.total_animes)} · ♂${sex}</span></div>`;
  }).join("");
  attachRowClicks("#demo-palma .pr-row");
}

// Exempts from ordinary jurisdiction: what the rectors recorded parish by parish
// (our hand reading of the 1768 facsimile) vs the diocese totals in the official
// Floridablanca 1787 resumen (IBESTAT/INE table I101001_7602). The gap between the
// two bars is the under-registration of the 1768 parish returns. Category labels
// match those used in the per-pueblo detail (exentosBlock), ordered by official total.
const EXENTOS_CATS = [
  { k: "real_servic", label: "Reial Servei", official: 4894 },
  { k: "real_hacien", label: "Reial Hisenda", official: 194 },
  { k: "inquisicion", label: "Inquisició", official: 100 },
  { k: "hidalguia", label: "Hidalguia", official: 62 },
  { k: "cruzada", label: "Croada", official: 51 },
];
function renderExentos() {
  const counted = DATA.pueblos.filter((p) => !p.is_aggregate);
  const rec = {};
  EXENTOS_CATS.forEach((c) => (rec[c.k] = 0));
  counted.forEach((p) => {
    const ex = p.exentos || {};
    EXENTOS_CATS.forEach((c) => (rec[c.k] += ex[c.k] || 0));
  });
  const maxV = Math.max(...EXENTOS_CATS.map((c) => c.official));
  const totRec = EXENTOS_CATS.reduce((s, c) => s + rec[c.k], 0);
  const totOff = EXENTOS_CATS.reduce((s, c) => s + c.official, 0);
  const rows = EXENTOS_CATS.map((c) => {
    const r = rec[c.k], o = c.official;
    const recW = (100 * r / maxV).toFixed(1), offW = (100 * o / maxV).toFixed(1);
    return `<div class="ex-row"><span class="ex-name" title="${esc(c.label)}">${esc(c.label)}</span>` +
      `<span class="ex-scale"><span class="ex-bar off" style="width:${offW}%"></span>` +
      `<span class="ex-bar rec" style="width:${recW}%"></span></span>` +
      `<span class="ex-val">${fmt(r)} / ${fmt(o)}</span></div>`;
  }).join("");
  $("#demo-exentos").innerHTML = rows +
    `<div class="ex-row ex-total"><span class="ex-name">Total</span>` +
    `<span class="ex-scale"></span>` +
    `<span class="ex-val">${fmt(totRec)} / ${fmt(totOff)}</span></div>`;
}

function renderIndicators(k, desc) {
  window._demoSort = { k, desc };
  const n = topN("#ind-topn");
  let ind = window._demoInd.slice().sort((a, b) => {
    const av = a[k], bv = b[k];
    if (typeof av === "string") return desc ? bv.localeCompare(av, "ca") : av.localeCompare(bv, "ca");
    return desc ? (bv - av) : (av - bv);
  });
  if (n > 0) ind = ind.slice(0, n);
  const f1 = (x) => x == null ? "—" : x.toFixed(1);
  const f0 = (x) => x == null ? "—" : x.toFixed(0);
  const mark = ' <span class="approx-mark" title="Les cel·les per edat no quadren; els indicadors d\'edat hi són aproximats">≈</span>';
  $("#demo-indicators").innerHTML = ind.map((x) =>
    `<tr data-n="${x.n}"${x.reconciled ? "" : ' class="ind-approx"'}><td title="${esc(x.name)}">${esc(x.name)}${x.reconciled ? "" : mark}</td>` +
    `<td class="num">${fmt(x.pop)}</td><td class="num">${f0(x.sex)}</td>` +
    `<td class="num">${f1(x.age)}</td><td class="num">${f0(x.dep)}</td>` +
    `<td class="num">${x.aging == null ? "—" : x.aging.toFixed(2)}</td>` +
    `<td class="num">${f0(x.married)}</td></tr>`).join("");
  attachRowClicks("#demo-indicators tr");
}

// ===== map =====
let mapInstance = null;

function renderMap() {
  if (typeof L === "undefined") return;
  if (mapInstance) { mapInstance.invalidateSize(); return; }

  mapInstance = L.map("map", { scrollWheelZoom: true })
    .setView([39.62, 2.95], 10);
  // OpenStreetMap's standard tiles. CARTO's basemaps, used until 2026, now
  // answer "API KEY REQUIRED" without a key.
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 18,
  }).addTo(mapInstance);

  const pts = DATA.pueblos.filter(
    (p) => !p.is_aggregate && typeof p.lat === "number" && typeof p.lon === "number");

  // Spread markers that share a coordinate (e.g. Palma's 6 parishes) in a ring.
  const groups = {};
  pts.forEach((p) => {
    const key = `${p.lat.toFixed(4)},${p.lon.toFixed(4)}`;
    (groups[key] ||= []).push(p);
  });
  const maxPop = Math.max(...pts.map((p) => p.total_animes || 0), 1);

  Object.values(groups).forEach((grp) => {
    grp.forEach((p, i) => {
      let lat = p.lat, lon = p.lon;
      if (grp.length > 1) {
        const ang = (2 * Math.PI * i) / grp.length;
        lat += 0.012 * Math.cos(ang);
        lon += 0.015 * Math.sin(ang);
      }
      const r = 5 + 22 * Math.sqrt((p.total_animes || 0) / maxPop);
      const verified = reconciledSC(p);
      const m = L.circleMarker([lat, lon], {
        radius: r,
        color: verified ? "#7a2e22" : "#b08a2a",
        weight: 1.5,
        fillColor: verified ? "#a85a4e" : "#e0c46a",
        fillOpacity: 0.6,
      }).addTo(mapInstance);
      const name = esc(p.name_catalan || p.name_modern);
      m.bindPopup(
        `<div class="map-popup"><b>${name}</b>` +
        (p.name_1768 ? ` <span class="pp-1768">(${esc(p.name_1768)})</span>` : "") +
        `<br>${fmt(p.total_animes)} ànimes` +
        (p.parroquia ? `<br><small>${esc(p.parroquia)}</small>` : "") +
        `<div class="pp-open" data-n="${p.pueblo_n}">Obrir la fitxa →</div></div>`);
      m.on("popupopen", (e) => {
        const link = e.popup.getElement().querySelector(".pp-open");
        if (link) link.addEventListener("click", () => { mapInstance.closePopup(); openDetail(p); });
      });
    });
  });
}

// ===== home stats =====
function renderHome() {
  const t = DATA.meta.totals;
  $("#stat-pueblos").textContent = fmt(t.pueblos_extracted);
  $("#stat-pop").textContent = fmt(t.total_animes);
  if (t.biggest) {
    $("#stat-top").textContent = fmt(t.biggest.pop);
    $("#stat-top-label").textContent = `màx · ${t.biggest.name}`;
  }
  $("#source-line").textContent = DATA.meta.source;
}

// ===== pobles table =====
function currentRows() {
  const q = $("#f-text").value.trim().toLowerCase();
  let rows = DATA.pueblos.filter((p) => {
    if (p.is_aggregate) return false;   // skip the "Palma. Resumen" aggregate row
    if (!q) return true;
    return [p.name_catalan, p.name_modern, p.name_1768]
      .some((n) => (n || "").toLowerCase().includes(q));
  });
  const sort = $("#f-sort").value;
  rows = rows.slice();
  if (sort === "name_catalan") {
    rows.sort((a, b) => (a.name_catalan || "").localeCompare(b.name_catalan || "", "ca"));
  } else if (sort === "total_animes_desc") {
    rows.sort((a, b) => (b.total_animes || 0) - (a.total_animes || 0));
  } else {
    rows.sort((a, b) => (a.pueblo_n || 0) - (b.pueblo_n || 0));
  }
  return rows;
}

function renderTable() {
  const rows = currentRows();
  const tb = $("#pobles-tbody");
  tb.innerHTML = "";
  rows.forEach((p) => {
    const tr = document.createElement("tr");
    tr.innerHTML =
      `<td class="num">${p.pueblo_n ?? ""}</td>` +
      `<td>${esc(p.name_catalan || p.name_modern)}</td>` +
      `<td class="name-1768">${esc(p.name_1768 || "")}</td>` +
      `<td class="code-cell">${esc(p.cod_mun_ine || "")}</td>` +
      `<td>${esc(p.parroquia || "")}</td>` +
      `<td class="num">${fmt(p.total_animes)}</td>`;
    tr.addEventListener("click", () => openDetail(p));
    tb.appendChild(tr);
  });
  $("#filter-count").textContent =
    `${rows.length} ${rows.length === 1 ? "poble" : "pobles"}`;
}

// ===== detail overlay =====
function confBadge(level) {
  if (!level) return "";
  const base = String(level).split(" ")[0];
  const cls = (base === "high" || base === "gold") ? "conf-high" : base === "medium" ? "conf-medium" : "conf-low";
  return `<span class="conf-flag ${cls}">${esc(level)}</span>`;
}

function ageStructure(dem) {
  const ba = dem.by_age;
  if (!ba) return "";
  // max cell for bar scaling
  let max = 0;
  AGE_GROUPS.forEach((g) => {
    const c = ba[g] || {};
    const v = (c.cas_var || 0) + (c.sol_var || 0);
    const h = (c.cas_hem || 0) + (c.sol_hem || 0);
    max = Math.max(max, v, h);
  });
  if (!max) return "";
  const rows = AGE_GROUPS.map((g) => {
    const c = ba[g] || {};
    const v = (c.cas_var || 0) + (c.sol_var || 0);
    const h = (c.cas_hem || 0) + (c.sol_hem || 0);
    const wv = ((v / max) * 100).toFixed(1);
    const wh = ((h / max) * 100).toFixed(1);
    return `<div class="bar-wrap"><span class="bar-label">${AGE_LABELS[g]}</span>` +
      `<span class="bar-track"><span class="bar male" style="width:${wv}%"></span></span><span class="bar-val">${v} ♂</span></div>` +
      `<div class="bar-wrap"><span class="bar-label"></span>` +
      `<span class="bar-track"><span class="bar female" style="width:${wh}%"></span></span><span class="bar-val">${h} ♀</span></div>`;
  }).join("");
  return `<div class="detail-section"><h3>Estructura per edat i sexe</h3>${rows}</div>`;
}

function proseOmitted() {
  // The rectors' 1768 relations survive only in a badly degraded facsimile that
  // cannot be transcribed reliably; we omit them rather than publish possibly
  // wrong readings. Numbers and identity are unaffected.
  return `<div class="detail-section"><h3>Relació del rector (1768)</h3>` +
    `<p style="font-size:.85em;color:var(--text-muted);margin:.1em 0 .2em">El text lliure de la relació manuscrita (clergat, jutjats, hospitals, sufragànies…) <strong>s'ha omès deliberadament</strong>. L'única font disponible és el facsímil escanejat de l'INE, de qualitat molt degradada, que no es pot transcriure amb prou fiabilitat, i no volem difondre lectures possiblement errònies. Les <strong>dades numèriques</strong> (facsímil INE + IBESTAT) i la <strong>identificació</strong> del municipi sí que són fiables.</p></div>`;
}

function exentosBlock(ex, uncertain) {
  if (!ex) return "";
  const unc = new Set(uncertain || []);
  const labels = { hidalguia: "Hidalguia", real_servic: "Reial Servei",
    real_hacien: "Reial Hisenda", cruzada: "Croada", inquisicion: "Inquisició" };
  const mark = ' <span class="approx-mark" title="dígit dubtós: no es llegeix amb prou claredat al facsímil">?</span>';
  const parts = Object.entries(labels)
    .filter(([k]) => ex[k] != null)
    .map(([k, l]) => `${l}: <strong>${ex[k]}</strong>${unc.has(k) ? mark : ""}`);
  if (!parts.length) return "";
  const note = uncertain && uncertain.length
    ? " Els valors amb «?» no es llegeixen amb prou claredat."
    : "";
  return `<div class="detail-section"><h3>Exempts per</h3>` +
    `<div class="val">${parts.join(" · ")}</div>` +
    `<p style="font-size:.8em;color:var(--text-muted);margin:.25em 0 0">Persones exemptes de la jurisdicció ordinària, tal com consten a la taula parroquial de 1768 (lectura verificada a mà sobre el facsímil).${note}</p></div>`;
}

function openDetail(p) {
  const dem = p.demografia || {};
  const conf = p.confidence || {};
  const sc = p.sum_check;
  const reconciled = sc === "ok" || (sc && typeof sc === "object" && sc.ok === true);
  const scDetail = (sc && typeof sc === "object") ? `Σ ${fmt(sc.sum)} ≠ total ${fmt(sc.total)}` : esc(sc);
  const checkLine = dem.by_age
    ? (reconciled
        ? `<p class="warn-line" style="color:var(--ok)">✓ Σ de cel·les per edat = total d'ànimes (${fmt(p.total_animes)}).</p>`
        : (p.cifras_stamp
            ? `<p class="warn-line">⚠ El facsímil porta el segell <strong>«ERROR EN CIFRAS»</strong> de l'INE: ja el 1768 els números d'aquesta taula no quadraven entre ells. El <strong>total i el repartiment per sexe estan validats</strong>; la distribució per grups d'edat pot no sumar el total (${scDetail}).</p>`
            : `<p class="warn-line">⚠ Les cel·les per edat no sumen el total (${scDetail}) — possible error aritmètic del manuscrit original. El total i el repartiment per sexe sí estan validats.</p>`))
    : "";

  const html =
    `<h2>${esc(p.name_catalan || p.name_modern)} ` +
    `<span style="font-size:.7em;color:var(--text-muted)">#${p.pueblo_n}</span></h2>` +
    `<p class="detail-sub">Nom al manuscrit: <span class="name-1768">${esc(p.name_1768 || "—")}</span>` +
    ` · Codi INE ${esc(p.cod_mun_ine || "—")}` +
    (p.parroquia ? ` · Parròquia de ${esc(p.parroquia)}` : "") + `</p>` +

    `<div class="kpi-row">` +
      `<div class="kpi"><span class="v">${fmt(p.total_animes)}</span><span class="k">ànimes ${confBadge(conf.total_animes)}</span></div>` +
      `<div class="kpi"><span class="v">${fmt(dem.var)}</span><span class="k">varons</span></div>` +
      `<div class="kpi"><span class="v">${fmt(dem.hem)}</span><span class="k">dones</span></div>` +
      (dem.casados ? `<div class="kpi"><span class="v">${fmt((dem.casados.var||0)+(dem.casados.hem||0))}</span><span class="k">casats</span></div>` : "") +
      (dem.solteros ? `<div class="kpi"><span class="v">${fmt((dem.solteros.var||0)+(dem.solteros.hem||0))}</span><span class="k">solters</span></div>` : "") +
    `</div>` +
    checkLine +
    ageStructure(dem) +
    exentosBlock(p.exentos, p.exentos_uncertain) +
    proseOmitted() +
    (p.notes ? `<div class="detail-section"><h3>Nota editorial</h3><div class="val">${esc(p.notes)}</div></div>` : "") +
    `<p class="detail-sub" style="margin-top:1.2rem">Xifres: <strong>IBESTAT</strong> (tabulació del cens d'Aranda 1768) · Identificació i imatge: facsímil INE 2013, ${esc(p.source_page || "")}, full R.A.H. ${esc(p.rah_page ?? "")}.</p>`;

  $("#detail-content").innerHTML = html;
  $("#detail-overlay").classList.add("open");
}

function closeDetail() {
  $("#detail-overlay").classList.remove("open");
}

// ===== boot =====
async function boot() {
  initTabs();
  $("#detail-close").addEventListener("click", closeDetail);
  $("#detail-overlay").addEventListener("click", (e) => {
    if (e.target.id === "detail-overlay") closeDetail();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeDetail();
  });
  $("#f-text").addEventListener("input", renderTable);
  $("#f-sort").addEventListener("change", renderTable);

  try {
    const res = await fetch("data.json", { cache: "no-store" });
    DATA = await res.json();
  } catch (err) {
    $("#pobles-tbody").innerHTML =
      `<tr><td colspan="6">Error carregant data.json: ${esc(err.message)}</td></tr>`;
    return;
  }
  renderHome();
  renderTable();
}

boot();
