// js/app.js
//
// Ties the two (unmodified) widget render functions to a plain HTML page:
// tabs to switch mode, a settings panel that maps to each widget's traitlets
// (n_classes / width / height / brushsize for scatter; n_bins / y_min / y_max
// / collection_names for bar), a live data table, CSV/JSON export, a manual
// dark-mode toggle, and a localStorage-backed "restore last session" banner.

(function () {
  "use strict";

  const SESSION_KEY = "drawdata:session:v1";
  const THEME_KEY = "drawdata:theme";

  const CLASS_COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"];
  const CLASS_NAMES = ["a", "b", "c", "d"];
  const BAR_COLORS = ["#36A2EB", "#FFCE56", "#4BC0C0", "#FF6384"];

  const DEFAULTS = {
    scatterConfig: { n_classes: 4, width: 760, height: 420, brushsize: 40 },
    barConfig: {
      n_bins: 24,
      y_min: 0,
      y_max: 1,
      width: 760,
      height: 480,
      collection_names: ["collection1", "collection2"],
    },
  };

  const state = {
    mode: "scatter",
    scatterConfig: { ...DEFAULTS.scatterConfig },
    barConfig: { ...DEFAULTS.barConfig, collection_names: [...DEFAULTS.barConfig.collection_names] },
    scatterData: [],
    barData: [],
  };

  let currentModel = null;
  let currentCleanup = null;
  let toastTimer = null;

  // ---------------------------------------------------------------
  // small helpers
  // ---------------------------------------------------------------

  const $ = (id) => document.getElementById(id);
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
  const fmtNum = (v) => (typeof v === "number" ? (Number.isInteger(v) ? v : v.toFixed(2)) : v);
  const escapeHtml = (s) =>
    String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  function showToast(msg) {
    const t = $("toast");
    t.textContent = msg;
    t.classList.add("visible");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.remove("visible"), 2400);
  }

  function timestamp() {
    const d = new Date();
    const pad = (n) => String(n).padStart(2, "0");
    return `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}-${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`;
  }

  // ---------------------------------------------------------------
  // session persistence (this browser only -- nothing leaves the machine)
  // ---------------------------------------------------------------

  function saveSession() {
    try {
      localStorage.setItem(
        SESSION_KEY,
        JSON.stringify({
          mode: state.mode,
          scatterConfig: state.scatterConfig,
          barConfig: state.barConfig,
          scatterData: state.scatterData,
          barData: state.barData,
        })
      );
    } catch (e) {
      /* storage unavailable / full — drawing still works, just isn't persisted */
    }
  }

  function loadSessionRaw() {
    try {
      const raw = localStorage.getItem(SESSION_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  }

  // ---------------------------------------------------------------
  // mounting the widgets
  // ---------------------------------------------------------------

  function mountWidget(mode) {
    if (currentCleanup) {
      try {
        currentCleanup();
      } catch (e) {
        /* ignore */
      }
      currentCleanup = null;
    }
    const mountEl = $("widgetMount");
    mountEl.innerHTML = "";

    const config = mode === "scatter" ? state.scatterConfig : state.barConfig;
    const data = mode === "scatter" ? state.scatterData : state.barData;

    const initial =
      mode === "scatter"
        ? { data, brushsize: config.brushsize, width: config.width, height: config.height, n_classes: config.n_classes }
        : {
            data,
            y_min: config.y_min,
            y_max: config.y_max,
            n_bins: config.n_bins,
            width: config.width,
            height: config.height,
            collection_names: config.collection_names,
          };

    currentModel = new LocalModel(initial);
    currentModel.on("change:data", (newData) => {
      state[mode + "Data"] = newData;
      updateDataPanel(mode, newData);
      saveSession();
    });

    currentCleanup =
      mode === "scatter"
        ? renderScatterWidget({ model: currentModel, el: mountEl })
        : renderBarWidget({ model: currentModel, el: mountEl });

    state.mode = mode;
    updateDataPanel(mode, currentModel.get("data") || []);
  }

  // ---------------------------------------------------------------
  // mode tabs
  // ---------------------------------------------------------------

  function setActiveModeUI(mode) {
    $("tabScatter").setAttribute("aria-selected", String(mode === "scatter"));
    $("tabBar").setAttribute("aria-selected", String(mode === "bar"));
    $("scatterSettings").classList.toggle("hidden", mode !== "scatter");
    $("barSettings").classList.toggle("hidden", mode !== "bar");
    $("modeCaption").innerHTML =
      mode === "scatter"
        ? "<strong>Scatter mode</strong> \u2014 pick a class, then click or click-and-drag on the grid to paint points."
        : "<strong>Bar mode</strong> \u2014 click and drag across a bin to set its value. Switch collections above the chart.";
  }

  function switchMode(mode) {
    if (mode === state.mode) return;
    setActiveModeUI(mode);
    mountWidget(mode);
    saveSession();
  }

  // ---------------------------------------------------------------
  // settings: scatter
  // ---------------------------------------------------------------

  function wireScatterSettings() {
    $("scatterWidth").addEventListener("change", (e) => {
      const v = clamp(parseInt(e.target.value, 10) || DEFAULTS.scatterConfig.width, 360, 1400);
      e.target.value = v;
      state.scatterConfig.width = v;
      if (state.mode === "scatter" && currentModel) currentModel.set("width", v);
      saveSession();
    });

    $("scatterHeight").addEventListener("change", (e) => {
      const v = clamp(parseInt(e.target.value, 10) || DEFAULTS.scatterConfig.height, 240, 900);
      e.target.value = v;
      state.scatterConfig.height = v;
      if (state.mode === "scatter" && currentModel) currentModel.set("height", v);
      saveSession();
    });

    $("applyScatterClasses").addEventListener("click", () => {
      const n = parseInt($("scatterClasses").value, 10);
      if (state.scatterData.length && !confirm("Changing the number of classes clears your current scatter drawing. Continue?")) {
        $("scatterClasses").value = String(state.scatterConfig.n_classes);
        return;
      }
      state.scatterConfig.n_classes = n;
      state.scatterData = [];
      if (state.mode === "scatter") mountWidget("scatter");
      saveSession();
      showToast(`Scatter canvas reset with ${n} class${n === 1 ? "" : "es"}.`);
    });
  }

  // ---------------------------------------------------------------
  // settings: bar
  // ---------------------------------------------------------------

  function renderCollectionNameFields(count, names) {
    const wrap = $("collectionNameFields");
    wrap.innerHTML = "";
    for (let i = 0; i < count; i++) {
      const row = document.createElement("div");
      row.className = "collection-name-row";

      const swatch = document.createElement("span");
      swatch.className = "collection-swatch";
      swatch.style.background = BAR_COLORS[i];

      const input = document.createElement("input");
      input.type = "text";
      input.maxLength = 24;
      input.value = (names && names[i]) || `collection${i + 1}`;
      input.setAttribute("aria-label", `Name for collection ${i + 1}`);
      input.dataset.collectionIndex = String(i);

      row.appendChild(swatch);
      row.appendChild(input);
      wrap.appendChild(row);
    }
  }

  function wireBarSettings() {
    $("barCollections").addEventListener("change", (e) => {
      renderCollectionNameFields(parseInt(e.target.value, 10), state.barConfig.collection_names);
    });

    $("applyBarSettings").addEventListener("click", () => {
      const bins = clamp(parseInt($("barBins").value, 10) || DEFAULTS.barConfig.n_bins, 4, 60);
      const width = clamp(parseInt($("barWidth").value, 10) || DEFAULTS.barConfig.width, 360, 1400);
      const height = clamp(parseInt($("barHeight").value, 10) || DEFAULTS.barConfig.height, 240, 900);
      const yMin = parseFloat($("barYMin").value);
      const yMax = parseFloat($("barYMax").value);

      if (!Number.isFinite(yMin) || !Number.isFinite(yMax) || yMax <= yMin) {
        alert("Y maximum must be a number greater than Y minimum.");
        return;
      }

      const seen = new Set();
      const names = [...document.querySelectorAll("#collectionNameFields input")].map((inp, i) => {
        let candidate = inp.value.trim() || `collection${i + 1}`;
        let suffix = 2;
        while (seen.has(candidate)) candidate = `${candidate}-${suffix++}`;
        seen.add(candidate);
        return candidate;
      });

      if (state.barData.length && !confirm("Applying these settings clears your current bar drawing. Continue?")) {
        return;
      }

      state.barConfig = { n_bins: bins, y_min: yMin, y_max: yMax, width, height, collection_names: names };
      state.barData = [];
      if (state.mode === "bar") mountWidget("bar");
      saveSession();
      showToast("Bar canvas reset.");
    });
  }

  function refreshSettingsFormFromState() {
    $("scatterClasses").value = String(state.scatterConfig.n_classes);
    $("scatterWidth").value = state.scatterConfig.width;
    $("scatterHeight").value = state.scatterConfig.height;
    $("barBins").value = state.barConfig.n_bins;
    $("barCollections").value = String(state.barConfig.collection_names.length);
    $("barYMin").value = state.barConfig.y_min;
    $("barYMax").value = state.barConfig.y_max;
    $("barWidth").value = state.barConfig.width;
    $("barHeight").value = state.barConfig.height;
    renderCollectionNameFields(state.barConfig.collection_names.length, state.barConfig.collection_names);
  }

  // ---------------------------------------------------------------
  // live data panel
  // ---------------------------------------------------------------

  function updateDataPanel(mode, data) {
    data = data || [];
    const statRow = $("statRow");
    const thead = $("dataTableHead");
    const tbody = $("dataTableBody");
    thead.innerHTML = "";
    tbody.innerHTML = "";

    if (mode === "scatter") {
      renderScatterStats(data, statRow);
      renderScatterTable(data, thead, tbody);
    } else {
      renderBarStats(data, statRow);
      renderBarTable(data, thead, tbody);
    }
  }

  function renderScatterStats(data, statRow) {
    if (!data.length) {
      statRow.textContent = "No points drawn yet.";
      return;
    }
    const counts = {};
    data.forEach((d) => {
      counts[d.label] = (counts[d.label] || 0) + 1;
    });
    const n = state.scatterConfig.n_classes;
    let html = `<span class="stat-chip"><strong>${data.length}</strong>&nbsp;points</span>`;
    for (let i = 0; i < n; i++) {
      html += `<span class="stat-chip"><span class="stat-dot" style="background:${CLASS_COLORS[i]}"></span>${CLASS_NAMES[i]}: ${counts[CLASS_NAMES[i]] || 0}</span>`;
    }
    statRow.innerHTML = html;
  }

  function renderScatterTable(data, thead, tbody) {
    ["#", "x", "y", "class", "batch"].forEach((col) => {
      const th = document.createElement("th");
      th.textContent = col;
      thead.appendChild(th);
    });
    if (!data.length) {
      tbody.appendChild(emptyRow(5, "Draw on the canvas to see rows here."));
      return;
    }
    const shown = data.slice(-200);
    for (let i = shown.length - 1; i >= 0; i--) {
      const d = shown[i];
      const rowNum = data.length - (shown.length - 1 - i);
      const tr = document.createElement("tr");
      tr.innerHTML = `<td>${rowNum}</td><td>${fmtNum(d.x)}</td><td>${fmtNum(d.y)}</td><td><span class="swatch-inline" style="background:${d.color}"></span>${d.label}</td><td>${d.batch ?? 0}</td>`;
      tbody.appendChild(tr);
    }
    if (data.length > 200) {
      tbody.appendChild(emptyRow(5, `Showing the most recent 200 of ${data.length} points \u2014 download to get all of them.`));
    }
  }

  function renderBarStats(data, statRow) {
    const collections = state.barConfig.collection_names;
    let html = `<span class="stat-chip"><strong>${state.barConfig.n_bins}</strong>&nbsp;bins</span>`;
    collections.forEach((name, i) => {
      html += `<span class="stat-chip"><span class="stat-dot" style="background:${BAR_COLORS[i]}"></span>${escapeHtml(name)}</span>`;
    });
    statRow.innerHTML = html;
  }

  function renderBarTable(data, thead, tbody) {
    ["collection", "bin", "value"].forEach((col) => {
      const th = document.createElement("th");
      th.textContent = col;
      thead.appendChild(th);
    });
    if (!data.length) {
      tbody.appendChild(emptyRow(3, "Draw on the chart to see rows here."));
      return;
    }
    const sorted = [...data].sort((a, b) => (a.collection === b.collection ? a.bin - b.bin : a.collection.localeCompare(b.collection)));
    sorted.forEach((d) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `<td><span class="swatch-inline" style="background:${d.color}"></span>${escapeHtml(d.collection)}</td><td>${d.bin}</td><td>${fmtNum(d.value)}</td>`;
      tbody.appendChild(tr);
    });
  }

  function emptyRow(colspan, text) {
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = colspan;
    td.className = "table-empty";
    td.textContent = text;
    tr.appendChild(td);
    return tr;
  }

  // ---------------------------------------------------------------
  // export
  // ---------------------------------------------------------------

  function currentData() {
    return state.mode === "scatter" ? state.scatterData : state.barData;
  }

  function exportRows() {
    const data = currentData();
    return state.mode === "scatter"
      ? data.map((d) => ({ x: d.x, y: d.y, color: d.color, label: d.label, batch: d.batch ?? 0 }))
      : data.map((d) => ({ collection: d.collection, bin: d.bin, value: d.value, color: d.color }));
  }

  function toCsv(rows) {
    if (!rows.length) return "";
    const cols = Object.keys(rows[0]);
    const esc = (v) => {
      const s = String(v);
      return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
    };
    const lines = [cols.join(",")];
    rows.forEach((r) => lines.push(cols.map((c) => esc(r[c])).join(",")));
    return lines.join("\n");
  }

  function triggerDownload(filename, content, mime) {
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function wireExport() {
    $("downloadCsv").addEventListener("click", () => {
      const rows = exportRows();
      if (!rows.length) return showToast("Nothing to export yet \u2014 draw something first.");
      triggerDownload(`drawdata-${state.mode}-${timestamp()}.csv`, toCsv(rows), "text/csv;charset=utf-8");
      showToast("CSV downloaded.");
    });

    $("downloadJson").addEventListener("click", () => {
      const rows = exportRows();
      if (!rows.length) return showToast("Nothing to export yet \u2014 draw something first.");
      triggerDownload(`drawdata-${state.mode}-${timestamp()}.json`, JSON.stringify(rows, null, 2), "application/json");
      showToast("JSON downloaded.");
    });

    $("copyJson").addEventListener("click", async () => {
      const rows = exportRows();
      if (!rows.length) return showToast("Nothing to export yet \u2014 draw something first.");
      const text = JSON.stringify(rows, null, 2);
      try {
        if (!navigator.clipboard) throw new Error("no clipboard api");
        await navigator.clipboard.writeText(text);
        showToast("Copied JSON to clipboard.");
      } catch (e) {
        const ta = document.createElement("textarea");
        ta.value = text;
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.select();
        try {
          document.execCommand("copy");
          showToast("Copied JSON to clipboard.");
        } catch (e2) {
          showToast("Couldn't copy automatically \u2014 use Download JSON instead.");
        }
        ta.remove();
      }
    });
  }

  // ---------------------------------------------------------------
  // theme
  // ---------------------------------------------------------------

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    $("themeToggle").textContent = theme === "dark" ? "\u2600" : "\u25D1";
  }

  function wireTheme() {
    let theme = "light";
    try {
      theme = localStorage.getItem(THEME_KEY) || "light";
    } catch (e) {
      /* ignore */
    }
    applyTheme(theme);

    $("themeToggle").addEventListener("click", () => {
      const next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
      applyTheme(next);
      try {
        localStorage.setItem(THEME_KEY, next);
      } catch (e) {
        /* ignore */
      }
    });
  }

  // ---------------------------------------------------------------
  // session restore banner
  // ---------------------------------------------------------------

  function wireSessionBanner() {
    const saved = loadSessionRaw();
    const hasSavedData = saved && (((saved.scatterData || []).length) || ((saved.barData || []).length));
    if (!hasSavedData) return;

    $("sessionBanner").classList.add("visible");

    $("restoreSession").addEventListener(
      "click",
      () => {
        state.mode = saved.mode === "bar" ? "bar" : "scatter";
        state.scatterConfig = { ...state.scatterConfig, ...(saved.scatterConfig || {}) };
        state.barConfig = { ...state.barConfig, ...(saved.barConfig || {}) };
        state.scatterData = Array.isArray(saved.scatterData) ? saved.scatterData : [];
        state.barData = Array.isArray(saved.barData) ? saved.barData : [];

        $("sessionBanner").classList.remove("visible");
        refreshSettingsFormFromState();
        setActiveModeUI(state.mode);
        mountWidget(state.mode);
        showToast("Restored your last drawing.");
      },
      { once: true }
    );

    $("discardSession").addEventListener(
      "click",
      () => {
        try {
          localStorage.removeItem(SESSION_KEY);
        } catch (e) {
          /* ignore */
        }
        $("sessionBanner").classList.remove("visible");
      },
      { once: true }
    );
  }

  // ---------------------------------------------------------------
  // boot
  // ---------------------------------------------------------------

  function init() {
    wireTheme();
    wireScatterSettings();
    wireBarSettings();
    wireExport();

    $("tabScatter").addEventListener("click", () => switchMode("scatter"));
    $("tabBar").addEventListener("click", () => switchMode("bar"));

    renderCollectionNameFields(state.barConfig.collection_names.length, state.barConfig.collection_names);
    setActiveModeUI(state.mode);
    mountWidget(state.mode);

    wireSessionBanner();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
