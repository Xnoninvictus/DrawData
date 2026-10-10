/* bar_widget.css (copied verbatim from the drawdata library) hardcodes its
   colors -- it was written for a notebook cell, which is always on a light
   background. Rather than edit that file, this small stylesheet layers
   higher-specificity dark-mode rules on top of it when the app's manual
   theme toggle is set to dark, so the bar widget doesn't render as a jarring
   white box on a dark page. Everything else about the widget is untouched. */

html[data-theme="dark"] #widgetMount .container {
  color: var(--ink);
}

html[data-theme="dark"] #widgetMount button.control,
html[data-theme="dark"] #widgetMount button.reset {
  background-color: var(--dd-input-bg);
  border-color: var(--dd-border-color);
  color: var(--ink);
}

html[data-theme="dark"] #widgetMount button.control.active {
  background-color: var(--dd-active-color);
  border-color: var(--dd-primary-color);
}

html[data-theme="dark"] #widgetMount .chart-container {
  border-color: var(--dd-border-color);
}

html[data-theme="dark"] #widgetMount svg {
  background: var(--dd-svg-bg);
}

html[data-theme="dark"] #widgetMount .grid line {
  stroke: var(--dd-border-color);
}

html[data-theme="dark"] #widgetMount .domain,
html[data-theme="dark"] #widgetMount svg text {
  stroke: var(--ink-soft);
  fill: var(--ink-soft);
}

html[data-theme="dark"] #widgetMount input[type="number"] {
  background: var(--dd-input-bg);
  color: var(--ink);
  border: 1px solid var(--dd-border-color);
}
