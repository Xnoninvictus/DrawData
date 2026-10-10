// Extracted & adapted from drawdata/static/bar_widget.js (koaning/drawdata, MIT License)
// Renders the bar-drawing widget into `el`, driven by a model shim (see js/model.js).
// Uses the global `d3` exposed by vendor/d3.v7.bundle.js -- logic is otherwise unmodified.
function renderBarWidget({ model, el }) {
  const margin = { top: 20, right: 30, bottom: 30, left: 60 };
  const width = model.get("width") - margin.left - margin.right;
  const height = model.get("height") - margin.top - margin.bottom;
  const userNames = model.get("collection_names");
  const colors = ["#36A2EB", "#FFCE56", "#4BC0C0", "#FF6384"];
  const collections = {};
  const numCollections = Math.max(1, userNames.length);
  for (let i = 0; i < numCollections; i++) {
    const name = userNames[i] || `collection${i + 1}`;
    collections[name] = {
      color: colors[i],
      data: new Array(model.get("n_bins")).fill(model.get("y_min"))
    };
  }
  ;
  let activeCollection = Object.keys(collections)[0];
  let isDrawing = false;
  let minY = model.get("y_min");
  let maxY = model.get("y_max");
  let data;
  updateDataOut();
  getBins();
  let container = document.createElement("div");
  let controls = document.createElement("div");
  controls.setAttribute("class", "controls");
  if (Object.keys(collections).length > 1) {
    Object.keys(collections).forEach((key) => {
      let btn = document.createElement("button");
      btn.setAttribute("class", "control");
      btn.style.position = "relative";
      btn.style.paddingLeft = "30px";
      let circle = document.createElement("span");
      circle.style.position = "absolute";
      circle.style.left = "8px";
      circle.style.top = "50%";
      circle.style.transform = "translateY(-50%)";
      circle.style.width = "12px";
      circle.style.height = "12px";
      circle.style.borderRadius = "50%";
      circle.style.backgroundColor = collections[key].color;
      circle.style.display = "inline-block";
      let text = document.createElement("span");
      text.textContent = key;
      btn.appendChild(text);
      btn.appendChild(circle);
      btn.addEventListener("click", () => {
        activeCollection = key;
        updateChart();
      });
      controls.appendChild(btn);
    });
  }
  let clear_btn = document.createElement("button");
  clear_btn.setAttribute("class", "reset");
  clear_btn.innerHTML = "Clear";
  // NOTE: unlike the original notebook widget (which only shows Clear once a
  // second collection exists), this standalone app always shows it -- there's
  // no notebook cell to re-run to reset state, so a visible clear affordance
  // is needed even with a single collection.
  controls.appendChild(clear_btn);
  container.appendChild(controls);
  el.appendChild(container);
  const svg = d3.select(container).append("svg").attr("width", width + margin.left + margin.right).attr("height", height + margin.top + margin.bottom).append("g").attr("transform", `translate(${margin.left},${margin.top})`);
  const x = d3.scaleBand().range([0, width]).padding(0.1).domain(d3.range(model.get("n_bins")));
  ;
  const y = d3.scaleLinear().range([height, 0]).domain([Math.min(minY, 0), maxY]);
  ;
  const grid = svg.append("g").attr("class", "grid");
  const xAxis = svg.append("g").attr("transform", `translate(0,${height})`).call(
    d3.axisBottom(x).tickValues(
      x.domain().filter((d, i) => {
        const interval = Math.ceil(model.get("n_bins") / 10);
        return i % interval === 0;
      })
    )
  );
  const yAxis = svg.append("g").call(d3.axisLeft(y).ticks(10).tickFormat(formatAxisNumber));
  Object.keys(collections).forEach((key) => {
    svg.append("g").attr("class", key);
  });
  svg.append("rect").attr("width", width).attr("height", height).attr("fill", "none").attr("stroke", "#000").attr("stroke-width", 1);
  function getBins() {
    return model.get("n_bins");
  }
  function formatAxisNumber(num) {
    const absNum = Math.abs(num);
    if (absNum >= 1e6) {
      return (num / 1e6).toFixed(1) + "M";
    } else if (absNum >= 1e3) {
      return (num / 1e3).toFixed(1) + "K";
    } else if (absNum < 1) {
      return num.toFixed(2);
    } else if (absNum < 10) {
      return num.toFixed(1);
    }
    return Math.round(num);
  }
  function updateChart() {
    const bins = getBins();
    x.domain(d3.range(bins));
    y.domain([Math.min(minY, 0), maxY]);
    xAxis.call(d3.axisBottom(x).tickValues(x.domain().filter((d, i) => {
      const interval = Math.ceil(bins / 10);
      return i % interval === 0;
    })));
    yAxis.call(d3.axisLeft(y).ticks(10).tickFormat(formatAxisNumber));
    grid.selectAll(".horizontal-grid").data(y.ticks(10)).enter().append("line").attr("class", "horizontal-grid").attr("x1", 0).attr("x2", width).attr("y1", (d) => y(d)).attr("y2", (d) => y(d)).attr("stroke", "#ddd").attr("stroke-opacity", 0.7);
    Object.entries(collections).forEach(([key, collection]) => {
      const bars = svg.select(`.${key}`).selectAll(".bar").data(collection.data);
      bars.enter().append("rect").attr("class", "bar").merge(bars).attr("x", (d, i) => x(i)).attr("width", x.bandwidth()).attr("y", (d) => y(Math.max(0, d))).attr("height", (d) => Math.abs(y(0) - y(d))).attr("fill", collection.color);
      bars.exit().remove();
    });
    updateDataOut();
  }
  function updateDataOut() {
    data = [];
    Object.keys(collections).forEach((key, i) => {
      let values = collections[key].data;
      values.forEach((value, j) => {
        data.push({ collection: key, value, bin: j, color: collections[key].color });
      });
    });
    model.set("data", data);
    model.save_changes();
  }
  ;
  const chartArea = svg.append("rect").attr("width", width).attr("height", height).attr("fill", "none").attr("pointer-events", "all");
  function updateValue(event) {
    const [xPos, yPos] = d3.pointer(event);
    const binIndex = Math.floor(x.domain().length * xPos / width);
    const value = y.invert(yPos);
    if (binIndex >= 0 && binIndex < getBins()) {
      collections[activeCollection].data[binIndex] = Math.max(minY, Math.min(maxY, value));
      updateChart();
    }
  }
  chartArea.on("mousedown", (event) => {
    isDrawing = true;
    updateValue(event);
  });
  chartArea.on("mousemove", (event) => {
    if (isDrawing) {
      updateValue(event);
    }
  });
  chartArea.on("mouseup", () => {
    isDrawing = false;
  });
  chartArea.on("mouseleave", () => {
    isDrawing = false;
  });
  document.querySelectorAll("button.control").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll("button.control").forEach((b) => b.classList.remove("active"));
      button.classList.add("active");
      activeCollection = button.querySelector("span").textContent;
    });
  });
  clear_btn.addEventListener("click", () => {
    Object.values(collections).forEach((collection) => {
      collection.data = new Array(getBins()).fill(0);
    });
    updateChart();
  });
  if (Object.keys(collections).length > 1) {
    document.querySelector("button.control").click();
  }
  updateChart();
}
