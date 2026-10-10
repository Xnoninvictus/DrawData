# drawdata — Standalone Browser Build

A single-page, offline web app version of the [drawdata](https://github.com/koaning/drawdata) widget engine. Draw a scatter or bar dataset by hand — click or drag on a grid — then export it as CSV or JSON for use in pandas, polars, scikit-learn, or anywhere else.

No Python, no Jupyter, no notebook, no internet connection required. Everything runs in the browser, and every drawing you make is saved locally.

---

## Table of Contents

1. [What It Does](#what-it-does)
2. [Quick Start](#quick-start)
3. [How It Works](#how-it-works)
4. [Project Structure](#project-structure)
5. [The Widget Model Shim](#the-widget-model-shim)
6. [Usage](#usage)
7. [Customization](#customization)
8. [Saving & Restoring](#saving--restoring)
9. [Export Formats](#export-formats)
10. [Running It Locally](#running-it-locally)
11. [Deploying It](#deploying-it)
12. [Browser Support](#browser-support)
13. [Troubleshooting](#troubleshooting)
14. [Known Limitations](#known-limitations)
15. [Extending the App](#extending-the-app)
16. [Credits](#credits)
17. [License](#license)

---

## What It Does

`drawdata` is a Jupyter widget that lets you hand-draw a dataset instead of generating one synthetically. This build takes that widget engine out of the notebook and puts it on a plain HTML page:

- **Scatter mode** — paint points on a grid with a click or a drag. Choose from 1 to 4 classes, each with its own color.
- **Bar mode** — drag across bins in a bar chart to set values. Switch between up to 4 collections, each with a named series.
- **Live data panel** — every point or bar you draw shows up in a table in real time, with summary stats.
- **CSV / JSON export** — download the drawing, or copy the JSON straight to the clipboard.
- **Autosave** — your drawing is stored in `localStorage` so you can close the tab and come back to it.
- **Dark mode** — a manual toggle that respects the widget's original CSS and applies a matching dark palette.
- **Zero backend** — the whole thing is a static site. Open `index.html` and it works.

---

## Quick Start

```bash
# Option 1: Just open it
open index.html          # macOS
start index.html         # Windows
xdg-open index.html      # Linux

# Option 2: Serve it (recommended — some browsers restrict file://)
python3 -m http.server 8000
# then visit http://localhost:8000
```

Draw something. Click **Download CSV** or **Download JSON** to get the data out. That's the whole workflow.

---

## How It Works

The original `drawdata` is an **anywidget** — a Jupyter widget that pairs a Python traitlets object with a JavaScript `render({ model, el })` function. The Python side owns the state; the JS side renders it into a DOM element and calls `model.set(...)` / `model.save_changes()` to sync back over a `comm` channel.

Outside of a notebook there is no Python kernel, no `comm`, and no traitlets. This build replaces that machinery with two small pieces:

```
┌──────────────────────────────────────────────────────────────────┐
│                        BEFORE (notebook)                          │
│                                                                   │
│  Python DrawdataWidget  ──comm──▶  anywidget runtime  ──▶  render │
│      (traitlets)                    (JS bridge)                   │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                        AFTER (this build)                         │
│                                                                   │
│  LocalModel (js/model.js)  ──▶  renderScatterWidget / renderBarWidget │
│    • get / set / on / save_changes   (js/scatter_render.js,          │
│    • pure JS, no comm needed          js/bar_render.js)               │
└──────────────────────────────────────────────────────────────────┘
```

The two `render*Widget` functions — which contain all of the drawing, brush math, drag handling, undo, and axis code — are **unmodified** from the original library. They call the same `model.get(...)` / `model.on(...)` / `model.set(...)` / `model.save_changes()` surface they always did. Only the object behind `model` is different.

Everything *around* the widget — the tab bar, the settings sidebar, the data table, the export buttons, the theme toggle, the session autosave — is new code in `js/app.js` and `css/app.css`.

---

## Project Structure

```
index.html                  the app shell
css/
  scatter_widget.css        original widget stylesheet, verbatim
  bar_widget.css            original widget stylesheet, verbatim
  bar_widget_theme.css      small additive dark-mode patch for bar_widget.css
  app.css                   the app's own layout & design tokens
js/
  model.js                  anywidget-compatible model shim (new)
  scatter_render.js         original ScatterWidget render() logic, unmodified
  bar_render.js             original BarWidget render() logic, unmodified*
  app.js                    tabs, settings, export, theme, autosave (new)
vendor/
  d3.v7.bundle.js           D3 v7, extracted from the original bundle for offline use
```

### `index.html`

The app shell. Loads the four stylesheets, sets up the topbar (brand, tabs, theme toggle), the session-restore banner, the canvas card, the sidebar (settings + data), and the footer. Loads the scripts in dependency order at the bottom of `<body>`:

```
vendor/d3.v7.bundle.js   →  js/model.js  →  js/scatter_render.js
                                          →  js/bar_render.js
                                          →  js/app.js
```

### `css/scatter_widget.css`

The original stylesheet for the scatter widget, copied **verbatim** from `drawdata/static/`. Handles the grid, buttons, radio selectors, brush slider, and the SVG container. Its colors are defined as CSS custom properties (`--dd-*`) so they can be overridden.

### `css/bar_widget.css`

The original stylesheet for the bar widget, also copied **verbatim**. Unlike `scatter_widget.css`, its colors are hard-coded — it was written for a notebook cell that was always light.

### `css/bar_widget_theme.css`

A small additive patch that layers higher-specificity rules on top of `bar_widget.css` when the app's manual dark-mode toggle is set to `html[data-theme="dark"]`. It only overrides the handful of properties the bar widget hard-codes (button backgrounds, borders, chart container, SVG background, grid lines, domain lines, and the number input). No widget code is touched.

### `css/app.css`

The app's own design tokens and layout. Defines a graph-paper aesthetic — a light, drafting-table background with faint ruled lines, `Caveat` for display type, `IBM Plex Sans` / `IBM Plex Mono` for body and data. Uses CSS custom properties for both the app palette and the `--dd-*` widget tokens, so the widget inherits the app's theme automatically (see [Customization](#customization)).

Includes:

- A `:root` block for light theme
- An `html[data-theme="dark"]` block for dark theme
- Layout styles for the header, sidebar, panels, table, footer, and toast
- A `@media (max-width: 900px)` breakpoint that stacks the sidebar under the canvas

### `js/model.js`

The **LocalModel** shim. Implements the exact slice of the anywidget/traitlets API the widgets actually use:

| Method | Behavior |
|--------|----------|
| `get(key)` | Return the current value. |
| `set(key, value)` | Store the value and synchronously emit `change:<key>`. |
| `on(event, handler)` | Subscribe to an event (e.g. `"change:data"`). |
| `off(event, handler)` | Unsubscribe. |
| `save_changes()` | Emit `"save_changes"` — a no-op for persistence, but kept for compatibility. |

Listeners are called synchronously, matching Backbone's behavior in the original anywidget runtime. There is no comm, no serialization, no async — just a plain JS object with an event bus.

### `js/scatter_render.js`

The original `renderScatterWidget({ model, el })` function, copied **verbatim** from the drawdata source. Contains:

- Class buttons and brush size slider
- Undo and reset
- The grid, drag handling, and per-point drawing
- The `change:data`, `change:brushsize`, `change:width`, `change:height` listeners

The only thing that changed is where `model` comes from — `app.js` constructs a `LocalModel` and passes it in.

### `js/bar_render.js`

The original `renderBarWidget({ model, el })` function, copied **verbatim***. Contains:

- Collection buttons (one per named series)
- The bar chart, x/y axes, and grid
- Mouse-drag value painting
- The Clear button

> **\*One deliberate change:** the original notebook widget only shows the Clear button when there's more than one collection. In a notebook, if you want to reset a single-collection chart you just re-run the cell. There is no cell to re-run here, so the Clear button is shown unconditionally. This is the only line of the file that differs from upstream, and it's marked with a comment in the source.

### `js/app.js`

The orchestrator. Ties everything together:

- **Mode tabs** — switches between scatter and bar, unmounting one widget and mounting the other.
- **Settings panels** — Scatter (class count, width, height) and Bar (bins, collections, Y min/max, width, height, collection names). Changing a setting updates the active widget's model (or remounts it, if the change requires a reset).
- **Data panel** — live table of the current widget's data, updated via the `change:data` listener. Shows summary stats (point counts per class, or bin count and collection names).
- **Export** — CSV, JSON download, and copy-JSON-to-clipboard (with a `document.execCommand` fallback for older browsers or non-secure contexts).
- **Theme toggle** — flips `data-theme` on `<html>` and persists the choice to `localStorage`.
- **Session autosave** — writes `{mode, scatterConfig, barConfig, scatterData, barData}` to `localStorage` on every change, and shows a restore banner on load if a previous session was found.

### `vendor/d3.v7.bundle.js`

D3 v7.8.5, extracted from the original drawdata bundle so the app can work fully offline. Exposes the global `d3` object that the two render functions expect. Nothing in this file was modified.

---

## The Widget Model Shim

If you're familiar with anywidget or traitlets, this is the interesting part. The render functions were written against a `model` that:

1. Is created by a Python kernel and synced over a `comm` channel.
2. Emits events synchronously when `set()` is called.
3. Has a `save_changes()` method that tells the kernel to flush queued updates.

`LocalModel` provides (1) as a plain object, (2) exactly, and (3) as a no-op that still fires an event in case any subscriber cares. The result: the render functions behave identically, but there's no kernel.

The trick that makes this work cleanly is that the widgets **never wait for the model to update**. They call `model.set(...)` and then immediately re-read from their own local state. So a synchronous in-memory model is a perfect drop-in — no need to simulate async round-trips.

`save_changes()` is emitted as a `"save_changes"` event even though nothing is being synced. `app.js` hooks it to trigger the `localStorage` write, so the autosave piggybacks on the widget's natural "a batch just finished" signal.

---

## Usage

### Scatter mode

1. Pick a class from the buttons at the top of the canvas (each has a color dot).
2. Set the brush size with the slider.
3. **Click** on the grid to place a single point, or **click and drag** to paint a cloud of points.
4. Points are drawn with the currently selected class color. Switch classes to draw a second (or third, or fourth) cluster.
5. Use **Undo** (the ↩ button) to remove the last batch, or **Reset** to clear everything.

### Bar mode

1. Pick a collection from the buttons above the chart (each has a color dot). Collections are named in the Settings panel.
2. **Click and drag** across a bin to set its value. The value is read from the Y position of the cursor.
3. Repeat for each collection.
4. Use **Clear** to reset all bins to the Y minimum.

### Settings

Each panel resets the canvas when applied (this is intentional — the widget engine doesn't support live reshaping of an existing drawing). You'll be asked to confirm before anything is discarded.

**Scatter settings:**

| Setting | Range | Notes |
|---------|-------|-------|
| Number of classes | 1–4 | 1 is "regression only" — no class buttons are shown, all points are one color. |
| Canvas width | 360–1400 px | Applies instantly. |
| Canvas height | 240–900 px | Applies instantly. |

**Bar settings:**

| Setting | Range | Notes |
|---------|-------|-------|
| Number of bins | 4–60 | |
| Collections | 1–4 | Collection names are editable below. |
| Y minimum | any number | Must be less than Y max. |
| Y maximum | any number | Must be greater than Y min. |
| Canvas width | 360–1400 px | |
| Canvas height | 240–900 px | |
| Collection names | up to 24 chars each | Duplicates get auto-suffixed (`-2`, `-3`, …). |

### Data panel

Updates live. Shows a summary chip row at the top (point counts per class, or bin/collection info), then a scrollable table of the most recent rows:

- **Scatter:** up to 200 most recent points, showing `#`, `x`, `y`, `class`, `batch`. If you've drawn more than 200, the table shows a note and the export contains all of them.
- **Bar:** all bins for all collections, sorted by collection then bin.

### Export

Three buttons at the bottom of the Data panel:

- **Download CSV** — `drawdata-<mode>-<timestamp>.csv`. Header row + one row per record.
- **Download JSON** — `drawdata-<mode>-<timestamp>.json`. Array of objects, pretty-printed.
- **Copy JSON** — copies the same JSON to the clipboard. Falls back to a hidden `<textarea>` + `execCommand` if the async Clipboard API isn't available.

---

## Customization

### Colors and theme tokens

Everything visual is driven by CSS custom properties. The main palette lives at the top of `css/app.css`:

```css
:root {
  /* app palette */
  --paper: #eef2f7;
  --paper-raised: #ffffff;
  --paper-line: #c9d6e4;
  --ink: #16233a;
  --ink-soft: #56698a;
  --accent-lead: #2a4d8f;
  --accent-mark: #cc5500;

  /* widget tokens (consumed by the dd-* stylesheets) */
  --dd-primary-color: #2a4d8f;
  --dd-border-color: #9fb0c6;
  --dd-svg-bg: #f8fafc;
  /* …etc */
}
```

Override any of these in `:root` (light) or `html[data-theme="dark"]` (dark). The widget's stylesheets will pick up the changes automatically because they reference the same tokens.

### The four class colors (scatter)

The scatter widget uses a fixed palette defined in `js/scatter_render.js`:

```js
const allColors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"];
const allClassNames = ["a", "b", "c", "d"];
```

Edit those arrays to change the colors or the class labels. The order determines which color goes to which class.

### The four collection colors (bar)

The bar widget uses a different palette, defined in both `js/bar_render.js` and `js/app.js`:

```js
const colors = ["#36A2EB", "#FFCE56", "#4BC0C0", "#FF6384"];
```

Both files need to be updated if you change them — the render function uses them to draw bars, and `app.js` uses them to render the swatches in the settings panel and the stat row.

### Default values

In `js/app.js`:

```js
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
```

Edit these to change what a fresh session starts with. (The same defaults are also baked into `index.html` as the `value` attributes on the settings inputs — update both if you want them to stay in sync.)

### Adding a new mode

The app is structured to make adding a third widget straightforward:

1. Add a new render function in `js/` following the `render<Name>Widget({ model, el })` pattern.
2. Add a tab button and a settings panel in `index.html`.
3. Extend `state`, `mountWidget`, `updateDataPanel`, and `exportRows` in `js/app.js`.
4. Add default config to `DEFAULTS`.

The `LocalModel` shim and the mount/unmount lifecycle will handle the rest.

### Fonts

The app loads three Google Fonts:

```css
@import url("https://fonts.googleapis.com/css2?family=Caveat:wght@600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap");
```

If you want the app to work *fully* offline (no font fetch), remove this `@import` and self-host the fonts, or swap them for system stacks by editing the `--font-*` tokens in `app.css`.

---

## Saving & Restoring

Every change — a drawn point, a settings tweak, a mode switch — triggers a write to `localStorage` under the key `drawdata:session:v1`. The saved object contains:

```js
{
  mode: "scatter" | "bar",
  scatterConfig: { ... },
  barConfig: { ... },
  scatterData: [ { x, y, color, label, batch }, ... ],
  barData: [ { collection, bin, value, color }, ... ]
}
```

On load, if a previous session is found and it contains any drawn data, a banner appears at the top of the page:

> *A previous drawing was found in this browser. Restore it?* **[Restore] [Discard]**

- **Restore** replaces the current in-memory state with the saved one and remounts the widget.
- **Discard** clears the saved session from `localStorage`. The banner doesn't appear again until you draw something new.

Nothing is uploaded anywhere. The `localStorage` write is the entire persistence layer.

### Clearing saved data manually

Open DevTools → Application → Local Storage → find the origin → delete the `drawdata:session:v1` and `drawdata:theme` keys. Or, in the console:

```js
localStorage.removeItem("drawdata:session:v1");
localStorage.removeItem("drawdata:theme");
```

---

## Export Formats

### Scatter CSV

```csv
x,y,color,label,batch
412.5,289.1,#1f77b4,a,0
418.2,301.7,#1f77b4,a,0
610.4,150.2,#ff7f0e,b,1
```

### Scatter JSON

```json
[
  { "x": 412.5, "y": 289.1, "color": "#1f77b4", "label": "a", "batch": 0 },
  { "x": 418.2, "y": 301.7, "color": "#1f77b4", "label": "a", "batch": 0 },
  { "x": 610.4, "y": 150.2, "color": "#ff7f0e", "label": "b", "batch": 1 }
]
```

Note that `y` is in **math coordinates** — Y goes up. The widget flips the SVG Y axis internally so the drawing looks right, but the exported data uses the conventional orientation.

### Bar CSV

```csv
collection,bin,value,color
collection1,0,0.12,#36A2EB
collection1,1,0.34,#36A2EB
collection1,2,0.28,#36A2EB
collection2,0,0.08,#FFCE56
```

### Bar JSON

```json
[
  { "collection": "collection1", "bin": 0, "value": 0.12, "color": "#36A2EB" },
  { "collection": "collection1", "bin": 1, "value": 0.34, "color": "#36A2EB" }
]
```

### Loading into pandas

```python
import pandas as pd

scatter = pd.read_csv("drawdata-scatter-20251010-143022.csv")
# → columns: x, y, color, label, batch

bars = pd.read_csv("drawdata-bar-20251010-143110.csv")
pivot = bars.pivot(index="bin", columns="collection", values="value")
```

---

## Running It Locally

The app is a static site. Any of these works:

### Direct file open

```bash
open index.html       # macOS
start index.html      # Windows
xdg-open index.html   # Linux
```

Modern Chrome, Firefox, and Safari all handle `file://` fine for this app, but some browsers restrict `localStorage` on `file://` origins — meaning autosave might not work. If you care about that, use a local server.

### Python HTTP server (recommended)

```bash
python3 -m http.server 8000
# → http://localhost:8000
```

### Node HTTP server

```bash
npx serve .
# or
npx http-server -p 8000
```

### PHP

```bash
php -S localhost:8000
```

All of these serve the directory as-is with no build step.

---

## Deploying It

Because there's no build step and no server-side code, you can drop the folder onto any static host:

- **GitHub Pages** — push the folder to a repo, enable Pages, done.
- **Netlify / Vercel / Cloudflare Pages** — point at the folder, no build command.
- **S3 / CloudFront** — sync the folder, set `index.html` as the index document.
- **Any web server** — copy the files into the document root.

The only external request the app makes is the Google Fonts `@import` in `app.css`. If you want it to work fully offline (or in a restricted network), self-host the fonts or remove the import — see [Fonts](#fonts).

---

## Browser Support

| Browser | Status |
|---------|--------|
| Chrome / Edge 88+ | ✅ Full support |
| Firefox 78+ | ✅ Full support |
| Safari 14+ | ✅ Full support |
| Chrome on Android | ✅ Works, but the drawing UX assumes a mouse |
| Safari on iOS | ⚠️ Works, but touch handling is inherited from the widget (see below) |

The widgets use `mousedown` / `mousemove` / `mouseup` for drawing. On touch devices, click-to-place works, but click-and-drag-painting relies on the browser synthesizing mouse events from touch, which most modern mobile browsers do — with a delay that can make painting feel sluggish. This is inherited behavior from the original widget, not something this build changes.

The Clipboard API (`navigator.clipboard.writeText`) requires a secure context (`https://` or `localhost`). If you're serving over plain HTTP, the **Copy JSON** button falls back to the legacy `document.execCommand("copy")` path, which works almost everywhere.

---

## Troubleshooting

| Symptom | Cause & fix |
|---------|-------------|
| **Nothing renders on the canvas** | Open the console — likely a script failed to load. Check that `vendor/d3.v7.bundle.js` is present and that all script tags at the bottom of `index.html` point to real files. |
| **`d3 is not defined`** | `vendor/d3.v7.bundle.js` didn't load, or loaded after one of the render scripts. Script order in `index.html` matters. |
| **`LocalModel is not defined`** | `js/model.js` didn't load, or loaded after `js/app.js`. Keep the order: model → renders → app. |
| **The bar chart is white on dark mode** | `css/bar_widget_theme.css` didn't load. It must come *after* `css/bar_widget.css` in the `<head>`. |
| **Settings changes don't apply** | Most settings reset the canvas, and resetting requires confirmation. If you dismissed the confirm dialog, nothing changed. |
| **Restore banner never appears** | `localStorage` is empty or unavailable. On `file://` some browsers disable it. Serve over HTTP if you need persistence. |
| **Export button says "Nothing to export yet"** | You haven't drawn anything. Draw a point first, then export. |
| **Copy JSON doesn't work** | You're on plain HTTP and the `execCommand` fallback also failed. Use **Download JSON** instead. |
| **Canvas is blurry on retina** | The SVG has a fixed viewBox. Increase the canvas width/height in the settings to give the browser more pixels to work with. |
| **Points land in the wrong place after resizing the canvas** | This is inherited widget behavior: the viewBox is updated but stored points aren't rescaled. Resize *before* drawing, or export first, resize, and redraw. |
| **Dark mode looks off on the scatter widget** | The scatter stylesheet uses `@media (prefers-color-scheme: dark)` for its dark palette — it responds to your OS theme, not the in-app toggle. If you want the in-app toggle to fully control it, override the `--dd-*` tokens under `html[data-theme="dark"]` in `app.css`. |

If you're stuck, open DevTools (`F12`) and look for messages in the console. Every error path in the app logs something.

---

## Known Limitations

- **Resizing the canvas after drawing doesn't rescale the drawing.** The SVG viewBox updates, and existing points keep their stored coordinates — which means they visually shift. Resize first, then draw, or export and re-import.
- **No copy-paste or drag-and-drop import.** Once you export and close the tab, the only way back is to re-draw or restore from `localStorage`.
- **Undo is batch-level, not point-level.** The scatter widget's Undo removes the entire last drag stroke. There's no way to undo a single point out of the middle of a cloud.
- **The bar widget's Clear always resets to `y_min`** — not to zero. If your Y minimum is negative, that's what bins reset to.
- **No keyboard navigation** for the drawing surfaces. The canvas is not focusable and points can only be placed with a pointer. This is inherited from the original widget.
- **`localStorage` has a size limit** (typically 5–10 MB per origin). A few thousand points fit comfortably; very large drawings may fail to save silently.
- **Only one drawing is saved at a time.** Restoring a session overwrites whatever's currently on screen. There's no "named slots" system.
- **The `popup` `stat-chip` row doesn't paginate.** If you have many classes and a lot of points, the stat row wraps but doesn't scroll.
- **`app.css` loads Google Fonts by default**, which requires a network fetch on first load. See [Fonts](#fonts) for how to remove this.

---

## Extending the App

Some natural next steps if you want to build on this:

### Import a dataset instead of drawing

Add a file input, parse CSV/JSON, and hand the result to `currentModel.set("data", parsed)`. The widget will render the points.

### Save named snapshots

Instead of a single `drawdata:session:v1` key, use `drawdata:sessions:<name>`. Add a list UI to the sidebar. The `saveSession()` / `loadSessionRaw()` functions in `app.js` are the only places that touch the key.

### Add a third widget mode

See [Adding a new mode](#adding-a-new-mode) above.

### Persist to IndexedDB instead of localStorage

For very large drawings, swap the storage layer. `saveSession()` and `loadSessionRaw()` are the only call sites.

### Export as PNG / SVG

The scatter canvas is already an SVG — you can serialize `mountEl.querySelector("svg")` with `XMLSerializer` and trigger a download. The bar chart is also SVG; the same trick works.

### Wire the export buttons to a clipboard of structured data

Right now **Copy JSON** copies a JSON array. You could add a **Copy as Python literal** button that produces `[[x, y, class], ...]` for quick pasting into a REPL.

---

## Credits

Built on the open-source **drawdata** widget engine by **Vincent D. Warmerdam** ([github.com/koaning/drawdata](https://github.com/koaning/drawdata)), **MIT License**. This standalone build is a derivative work for offline, notebook-free use.

The two render functions (`js/scatter_render.js`, `js/bar_render.js`), the two widget stylesheets (`css/scatter_widget.css`, `css/bar_widget.css`), and the bundled D3 (`vendor/d3.v7.bundle.js`) are all taken from the upstream project with minimal or no modification. The `LocalModel` shim, `css/app.css`, `css/bar_widget_theme.css`, and `js/app.js` are new work for this build.

D3 v7.8.5 — [github.com/d3/d3](https://github.com/d3/d3), ISC License.

---

## License

MIT License, matching upstream drawdata.

You are free to use, modify, and redistribute this build. If you publish a derivative, please keep the credit to Vincent D. Warmerdam and the drawdata project visible, it's a small thing but the right thing.
