/* ============================================================
   drawdata — standalone app shell
   Design language: a drafting-table graph-paper notebook.
   The widget itself already draws its own coordinate grid in
   SVG, so the chrome around it borrows the same vocabulary —
   blueprint blue, ruled lines, a spiral-bound "page" for the
   canvas, and the four category colors the tool itself draws
   with (#1f77b4 / #ff7f0e / #2ca02c / #d62728) used sparingly
   as the only accent color extracted straight from the subject.
   ============================================================ */

@import url("https://fonts.googleapis.com/css2?family=Caveat:wght@600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap");

:root {
  /* ---- app tokens: light (default) ---- */
  --paper: #eef2f7;
  --paper-raised: #ffffff;
  --paper-line: #c9d6e4;
  --ink: #16233a;
  --ink-soft: #56698a;
  --ink-faint: #8497b5;
  --accent-lead: #2a4d8f;
  --accent-lead-hover: #1f3c72;
  --accent-mark: #cc5500;
  --danger: #b91c1c;
  --radius: 0.6rem;
  --shadow-card: 0 1px 2px rgba(22, 35, 58, 0.06), 0 8px 24px -12px rgba(22, 35, 58, 0.18);
  --font-display: "Caveat", cursive;
  --font-body: "IBM Plex Sans", ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --font-mono: "IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;

  /* ---- widget (dd-*) tokens, overridden to match the app palette ---- */
  --dd-bg-color: #fdfeff;
  --dd-text-color: #16233a;
  --dd-border-color: #9fb0c6;
  --dd-hover-color: #eef2f7;
  --dd-active-color: #e2e9f2;
  --dd-primary-color: #2a4d8f;
  --dd-primary-hover: #1f3c72;
  --dd-svg-bg: #f8fafc;
  --dd-input-bg: #e9eef5;
  --dd-control-shadow: 0 1px 2px 0 rgba(22, 35, 58, 0.08);
  --dd-shadow-color: rgba(22, 35, 58, 0.15);
  --dd-svg-border: 1px solid #9fb0c6;
  --dd-svg-border-radius: 0.5rem;
  --dd-focus-ring: 0 0 0 2px rgba(42, 77, 143, 0.45);
}

html[data-theme="dark"] {
  --paper: #0e1520;
  --paper-raised: #151f2d;
  --paper-line: #29394f;
  --ink: #eef2f7;
  --ink-soft: #a3b4cc;
  --ink-faint: #6b7d99;
  --accent-lead: #7fa6ea;
  --accent-lead-hover: #9dbcf0;
  --accent-mark: #ff9d4d;
  --danger: #f87171;
  --shadow-card: 0 1px 2px rgba(0, 0, 0, 0.3), 0 12px 28px -14px rgba(0, 0, 0, 0.6);

  --dd-bg-color: #151f2d;
  --dd-text-color: #eef2f7;
  --dd-border-color: #3c4f6b;
  --dd-hover-color: #1c2837;
  --dd-active-color: #24334a;
  --dd-primary-color: #7fa6ea;
  --dd-primary-hover: #9dbcf0;
  --dd-svg-bg: #0e1520;
  --dd-input-bg: #1c2837;
  --dd-control-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.35);
  --dd-shadow-color: rgba(0, 0, 0, 0.5);
  --dd-svg-border: 1px solid #3c4f6b;
  --dd-focus-ring: 0 0 0 2px rgba(127, 166, 234, 0.5);
}

* { box-sizing: border-box; }

html, body {
  height: 100%;
}

body {
  margin: 0;
  color: var(--ink);
  font-family: var(--font-body);
  background:
    linear-gradient(var(--paper-line) 1px, transparent 1px) 0 0 / 100% 28px,
    linear-gradient(90deg, var(--paper-line) 1px, transparent 1px) 0 0 / 28px 100%,
    var(--paper);
  background-attachment: fixed;
  transition: background-color 0.25s ease, color 0.25s ease;
}

.page {
  max-width: 1240px;
  margin: 0 auto;
  padding: 1.5rem 1.5rem 3rem;
  min-height: 100%;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* ---------- header ---------- */

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
  padding-bottom: 0.75rem;
  border-bottom: 2px solid var(--paper-line);
}

.brand {
  display: flex;
  align-items: baseline;
  gap: 0.65rem;
}

.brand-mark {
  font-size: 1.5rem;
  color: var(--accent-mark);
  transform: rotate(-8deg);
  display: inline-block;
}

.brand h1 {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 2.4rem;
  line-height: 1;
  margin: 0;
  letter-spacing: 0.5px;
}

.tagline {
  margin: 0.1rem 0 0;
  color: var(--ink-soft);
  font-size: 0.85rem;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.mode-tabs {
  display: inline-flex;
  gap: 0.35rem;
  background: var(--paper-raised);
  border: 1px solid var(--paper-line);
  border-radius: 999px;
  padding: 0.25rem;
  box-shadow: var(--shadow-card);
}

.mode-tab {
  font-family: var(--font-body);
  font-weight: 500;
  font-size: 0.85rem;
  border: none;
  background: transparent;
  color: var(--ink-soft);
  padding: 0.45rem 1rem;
  border-radius: 999px;
  cursor: pointer;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.mode-tab:hover { color: var(--ink); }

.mode-tab[aria-selected="true"] {
  background: var(--accent-lead);
  color: #fff;
}

.theme-toggle {
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 50%;
  border: 1px solid var(--paper-line);
  background: var(--paper-raised);
  color: var(--ink);
  cursor: pointer;
  font-size: 1rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow-card);
}

.theme-toggle:hover { border-color: var(--accent-lead); }

/* ---------- session banner ---------- */

.session-banner {
  display: none;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  background: var(--paper-raised);
  border: 1px dashed var(--accent-lead);
  border-radius: var(--radius);
  padding: 0.75rem 1rem;
  font-size: 0.875rem;
  flex-wrap: wrap;
}

.session-banner.visible { display: flex; }

.session-banner .btn { padding: 0.35rem 0.85rem; font-size: 0.8rem; }

/* ---------- layout ---------- */

.layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 22rem;
  gap: 1.5rem;
  align-items: start;
}

@media (max-width: 900px) {
  .layout { grid-template-columns: 1fr; }
}

/* ---------- canvas card (the "notebook page") ---------- */

.canvas-card {
  position: relative;
  background: var(--paper-raised);
  border-radius: var(--radius);
  box-shadow: var(--shadow-card);
  border: 1px solid var(--paper-line);
  padding: 1.25rem 1.25rem 1.25rem 2.5rem;
  overflow: hidden;
}

.canvas-card-spine {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 1.6rem;
  background:
    radial-gradient(circle at 50% 12px, var(--paper) 4px, transparent 4.5px),
    var(--accent-lead);
  background-size: 100% 26px, 100% 100%;
  background-repeat: repeat-y, no-repeat;
  opacity: 0.9;
}

html[data-theme="dark"] .canvas-card-spine { opacity: 0.75; }

.canvas-card-inner { min-height: 200px; }

.mode-caption {
  font-size: 0.8rem;
  color: var(--ink-soft);
  margin: 0 0 0.75rem;
}

.mode-caption strong { color: var(--ink); }

/* ---------- sidebar / panels ---------- */

.sidebar {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.panel {
  background: var(--paper-raised);
  border: 1px solid var(--paper-line);
  border-radius: var(--radius);
  box-shadow: var(--shadow-card);
  padding: 1.1rem 1.2rem 1.25rem;
}

.panel h2 {
  font-family: var(--font-display);
  font-size: 1.5rem;
  margin: 0 0 0.15rem;
  font-weight: 700;
}

.panel-hint {
  font-size: 0.78rem;
  color: var(--ink-soft);
  margin: 0 0 0.9rem;
  line-height: 1.4;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  margin-bottom: 0.75rem;
}

.field label {
  font-size: 0.78rem;
  font-weight: 500;
  color: var(--ink-soft);
}

.field input[type="number"],
.field input[type="text"],
.field select {
  font-family: var(--font-mono);
  font-size: 0.85rem;
  padding: 0.4rem 0.55rem;
  border-radius: 0.4rem;
  border: 1px solid var(--paper-line);
  background: var(--dd-input-bg);
  color: var(--ink);
}

.field input:focus, .field select:focus {
  outline: none;
  box-shadow: var(--dd-focus-ring);
  border-color: var(--accent-lead);
}

.field-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.6rem;
}

.collection-names {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  margin-bottom: 0.75rem;
}

.collection-name-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.collection-swatch {
  width: 0.7rem;
  height: 0.7rem;
  border-radius: 50%;
  flex: none;
}

.btn {
  font-family: var(--font-body);
  font-weight: 500;
  font-size: 0.82rem;
  padding: 0.5rem 0.9rem;
  border-radius: 0.45rem;
  border: 1px solid var(--paper-line);
  background: var(--paper);
  color: var(--ink);
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn:hover {
  border-color: var(--accent-lead);
  background: var(--dd-hover-color);
}

.btn-primary {
  width: 100%;
  margin-top: 0.25rem;
  background: var(--accent-lead);
  border-color: var(--accent-lead);
  color: #fff;
}

.btn-primary:hover { background: var(--accent-lead-hover); }

.btn-small { font-size: 0.75rem; padding: 0.3rem 0.6rem; }

/* ---------- data / export panel ---------- */

.stat-row {
  font-family: var(--font-mono);
  font-size: 0.8rem;
  color: var(--ink);
  background: var(--dd-input-bg);
  border-radius: 0.4rem;
  padding: 0.55rem 0.7rem;
  margin-bottom: 0.75rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 0.9rem;
  align-items: center;
}

.stat-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.stat-dot {
  width: 0.55rem;
  height: 0.55rem;
  border-radius: 50%;
  flex: none;
}

.table-wrap {
  max-height: 14rem;
  overflow: auto;
  border: 1px solid var(--paper-line);
  border-radius: 0.4rem;
  margin-bottom: 0.85rem;
}

table#dataTable {
  border-collapse: collapse;
  width: 100%;
  font-family: var(--font-mono);
  font-size: 0.74rem;
}

table#dataTable thead th {
  position: sticky;
  top: 0;
  background: var(--dd-input-bg);
  text-align: left;
  padding: 0.4rem 0.55rem;
  border-bottom: 1px solid var(--paper-line);
  font-weight: 600;
}

table#dataTable tbody td {
  padding: 0.3rem 0.55rem;
  border-bottom: 1px solid var(--paper-line);
  white-space: nowrap;
}

table#dataTable tbody tr:last-child td { border-bottom: none; }

.table-empty {
  padding: 1rem;
  text-align: center;
  color: var(--ink-faint);
  font-size: 0.8rem;
}

.swatch-inline {
  display: inline-block;
  width: 0.6rem;
  height: 0.6rem;
  border-radius: 50%;
  margin-right: 0.35rem;
  vertical-align: middle;
}

.export-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.export-actions .btn { flex: 1 1 auto; }

.toast {
  position: fixed;
  bottom: 1.25rem;
  left: 50%;
  transform: translateX(-50%) translateY(0.5rem);
  background: var(--ink);
  color: var(--paper);
  font-size: 0.82rem;
  padding: 0.55rem 1rem;
  border-radius: 999px;
  box-shadow: var(--shadow-card);
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease, transform 0.2s ease;
  z-index: 50;
}

.toast.visible {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}

/* ---------- footer ---------- */

.footer {
  text-align: center;
  font-size: 0.78rem;
  color: var(--ink-faint);
  line-height: 1.5;
  padding-top: 0.5rem;
}

.footer a { color: var(--accent-lead); }

.hidden { display: none !important; }
