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

function pueblosWithAge() {
  return DATA.pueblos.filter((p) => !p.is_aggregate && p.sum_check === "ok" && p.demografia && p.demografia.by_age);
}
function cellN(c, k) { return Number.isInteger(c && c[k]) ? c[k] : 0; }

function puebloIndicators(p) {
  const ba = p.demografia.by_age;
  let V = 0, H = 0, num = 0, u16 = 0, a1650 = 0, o50 = 0, casAd = 0, totAd = 0;
  for (const g of AGE_GROUPS) {
    const c = ba[g];
    const v = cellN(c, "cas_var") + cellN(c, "sol_var");
    const h = cellN(c, "cas_hem") + cellN(c, "sol_hem");
    const t = v + h;
    V += v; H += h; num += AGE_MID[g] * t;
    if (g === "0-7" || g === "7-16") u16 += t;
    else if (g === "50+") o50 += t;
    else a1650 += t;
    if (g !== "0-7" && g !== "7-16") {
      casAd += cellN(c, "cas_var") + cellN(c, "cas_hem");
      totAd += t;
    }
  }
  const N = V + H;
  return {
    pop: p.total_animes, name: p.name_catalan || p.name_modern, n: p.pueblo_n,
    sex: H ? (100 * V / H) : null,
    age: N ? (num / N) : null,
    dep: a1650 ? (100 * (u16 + o50) / a1650) : null,
    aging: u16 ? (o50 / u16) : null,
    married: totAd ? (100 * casAd / totAd) : null,
  };
}

function renderDemografia() {
  if (demoDone) return;
  demoDone = true;
  const full = pueblosWithAge();
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

  // sex ratio per pueblo
  const ind = full.map(puebloIndicators).filter((x) => x.sex != null);
  const ranked = ind.slice().sort((a, b) => a.sex - b.sex);
  const maxDev = Math.max(...ranked.map((x) => Math.abs(x.sex - 100)), 20);
  $("#demo-ratio").innerHTML = ranked.map((x) => {
    const dev = x.sex - 100, w = (50 * Math.abs(dev) / maxDev).toFixed(1);
    const side = dev >= 0 ? "right" : "left";
    return `<div class="rt-row" data-n="${x.n}"><span class="rt-name">${esc(x.name)}</span>` +
      `<span class="rt-track"><span class="rt-bar ${side}" style="width:${w}%"></span></span>` +
      `<span class="rt-val">${x.sex.toFixed(0)}</span></div>`;
  }).join("");
  $$("#demo-ratio .rt-row").forEach((row) => row.addEventListener("click", () => {
    const p = DATA.pueblos.find((x) => x.pueblo_n == row.dataset.n); if (p) openDetail(p);
  }));

  // indicators table
  window._demoInd = ind;
  renderIndicators("pop", true);
  $$("#tab-demografia .indicators-table th.sortable").forEach((th) => {
    th.addEventListener("click", () => {
      const k = th.dataset.k;
      const desc = window._demoSort && window._demoSort.k === k ? !window._demoSort.desc : true;
      renderIndicators(k, desc);
    });
  });
}

function renderIndicators(k, desc) {
  window._demoSort = { k, desc };
  const ind = window._demoInd.slice().sort((a, b) => {
    const av = a[k], bv = b[k];
    if (typeof av === "string") return desc ? bv.localeCompare(av, "ca") : av.localeCompare(bv, "ca");
    return desc ? (bv - av) : (av - bv);
  });
  const f1 = (x) => x == null ? "—" : x.toFixed(1);
  const f0 = (x) => x == null ? "—" : x.toFixed(0);
  $("#demo-indicators").innerHTML = ind.map((x) =>
    `<tr data-n="${x.n}"><td>${esc(x.name)}</td>` +
    `<td class="num">${fmt(x.pop)}</td><td class="num">${f0(x.sex)}</td>` +
    `<td class="num">${f1(x.age)}</td><td class="num">${f0(x.dep)}</td>` +
    `<td class="num">${x.aging == null ? "—" : x.aging.toFixed(2)}</td>` +
    `<td class="num">${f0(x.married)}</td></tr>`).join("");
  $$("#demo-indicators tr").forEach((tr) => tr.addEventListener("click", () => {
    const p = DATA.pueblos.find((x) => x.pueblo_n == tr.dataset.n); if (p) openDetail(p);
  }));
}

// ===== map =====
let mapInstance = null;

function spineVerified(p) {
  const d = p.demografia || {};
  return Number.isInteger(d.var) && Number.isInteger(d.hem) &&
    d.var + d.hem === p.total_animes;
}

function renderMap() {
  if (typeof L === "undefined") return;
  if (mapInstance) { mapInstance.invalidateSize(); return; }

  mapInstance = L.map("map", { scrollWheelZoom: true })
    .setView([39.62, 2.95], 10);
  L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
    attribution: "&copy; OpenStreetMap &copy; CARTO",
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
      const verified = spineVerified(p);
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
  const cls = base === "high" ? "conf-high" : base === "medium" ? "conf-medium" : "conf-low";
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
      `<span class="bar male" style="width:${wv}%"></span><span class="bar-val">${v} ♂</span></div>` +
      `<div class="bar-wrap"><span class="bar-label"></span>` +
      `<span class="bar female" style="width:${wh}%"></span><span class="bar-val">${h} ♀</span></div>`;
  }).join("");
  return `<div class="detail-section"><h3>Estructura per edat i sexe</h3>${rows}</div>`;
}

function proseOmitted() {
  // The rectors' 1768 relations survive only in a badly degraded facsimile that
  // cannot be transcribed reliably; we omit them rather than publish possibly
  // wrong readings. Numbers and identity are unaffected.
  return `<div class="detail-section"><h3>Relació del rector (1768)</h3>` +
    `<p style="font-size:.85em;color:var(--text-muted);margin:.1em 0 .2em">El text lliure de la relació manuscrita (clergat, jutjats, hospitals, sufragànies…) <strong>s'ha omès deliberadament</strong>. L'única font disponible és una fotocòpia molt degradada que no es pot transcriure amb prou fiabilitat, i no volem difondre lectures possiblement errònies. Les <strong>dades numèriques</strong> (validades amb IBESTAT) i la <strong>identificació</strong> del municipi sí que són fiables.</p></div>`;
}

function exentosBlock(ex) {
  if (!ex) return "";
  const labels = { hidalguia: "Hidalguia", real_servic: "Reial Servei",
    real_hacien: "Reial Hisenda", cruzada: "Croada", inquisicion: "Inquisició" };
  const parts = Object.entries(labels)
    .filter(([k]) => ex[k] != null)
    .map(([k, l]) => `${l}: <strong>${ex[k]}</strong>`);
  if (!parts.length) return "";
  return `<div class="detail-section"><h3>Exempts per</h3>` +
    `<div class="val">${parts.join(" · ")}</div></div>`;
}

function openDetail(p) {
  const dem = p.demografia || {};
  const conf = p.confidence || {};
  const reconciled = (p.sum_check === "ok");
  const checkLine = dem.by_age
    ? (reconciled
        ? `<p class="warn-line" style="color:#2c5e2c">✓ Σ de cel·les = total d'ànimes (${fmt(p.total_animes)}): lectura reconciliada amb els totals manuscrits.</p>`
        : (p.cifras_stamp
            ? `<p class="warn-line">⚠ El facsímil porta el segell <strong>«ERROR EN CIFRAS»</strong> de l'INE: ja el 1768 els números d'aquesta taula no quadraven entre ells. El <strong>total i el repartiment per sexe estan validats</strong>; la distribució per grups d'edat pot no sumar el total (${esc(p.sum_check)}).</p>`
            : `<p class="warn-line">⚠ Millor lectura (2 passades de visió): les cel·les per edat no quadren amb el total (${esc(p.sum_check)}) — dígit ambigu o possible error aritmètic del manuscrit. El total i el repartiment per sexe sí estan validats.</p>`))
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
    exentosBlock(p.exentos) +
    proseOmitted() +
    (p.notes ? `<div class="detail-section"><h3>Nota editorial</h3><div class="val">${esc(p.notes)}</div></div>` : "") +
    `<p class="detail-sub" style="margin-top:1.2rem">Font: facsímil INE 2013, ${esc(p.source_page || "")}, full R.A.H. ${esc(p.rah_page ?? "")}.</p>`;

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
