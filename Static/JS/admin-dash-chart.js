(function () {
  var payloadEl = document.getElementById("admin-graph-payload");
  var canvas = document.getElementById("adminDashChart");
  var titleEl = document.getElementById("adminDashChartTitle");
  if (!payloadEl || !canvas) return;

  var raw = (payloadEl.textContent || "").trim();
  var charts;
  try {
    charts = JSON.parse(raw || "{}");
  } catch (e) {
    charts = {};
    if (titleEl) {
      titleEl.textContent = "Could not load chart data (invalid JSON).";
    }
  }

  if (typeof Chart === "undefined") {
    if (titleEl) titleEl.textContent = "Chart library failed to load.";
    return;
  }

  var chart = null;
  var buttons = document.querySelectorAll(".graph-type-btn");

  function baseOptions(chartType) {
    var legend = chartType === "pie" || chartType === "doughnut";
    var opts = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: legend },
      },
    };
    if (chartType !== "pie" && chartType !== "doughnut") {
      opts.scales = {
        x: { ticks: { maxRotation: 45, minRotation: 0 } },
        y: { beginAtZero: true, ticks: { precision: 0 } },
      };
    }
    return opts;
  }

  function render(slug) {
    var cfg = charts[slug];
    if (!cfg || !cfg.chartType) {
      if (titleEl) titleEl.textContent = "No chart for this selection.";
      return;
    }
    if (chart) chart.destroy();
    if (titleEl) titleEl.textContent = cfg.title || "";

    var opts = baseOptions(cfg.chartType);
    if (cfg.chartType === "line") {
      opts.scales = {
        x: { ticks: { maxRotation: 45, minRotation: 0 } },
        y: { beginAtZero: true, ticks: { precision: 0 } },
      };
    }

    chart = new Chart(canvas.getContext("2d"), {
      type: cfg.chartType,
      data: {
        labels: cfg.labels || [],
        datasets: cfg.datasets || [],
      },
      options: opts,
    });
  }

  buttons.forEach(function (btn) {
    btn.addEventListener("click", function () {
      var slug = btn.getAttribute("data-graph");
      buttons.forEach(function (b) {
        b.classList.remove("is-active");
        b.setAttribute("aria-pressed", "false");
      });
      btn.classList.add("is-active");
      btn.setAttribute("aria-pressed", "true");
      render(slug);
    });
  });

  var first = document.querySelector(".graph-type-btn.is-active") || buttons[0];
  if (first) {
    render(first.getAttribute("data-graph"));
  } else if (titleEl) {
    titleEl.textContent = "Select a data type to show a graph.";
  }
})();
