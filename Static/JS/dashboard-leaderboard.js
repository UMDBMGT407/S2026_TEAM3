(function () {
  var LABELS = { workouts: "Workouts", sets: "Sets", reps: "Reps" };

  function showMetric(root, prefix, metric) {
    var th = document.getElementById(prefix + "-lb-metric-th");
    var wBody = document.getElementById(prefix + "-lb-tbody-workouts");
    var sBody = document.getElementById(prefix + "-lb-tbody-sets");
    var rBody = document.getElementById(prefix + "-lb-tbody-reps");
    if (!wBody || !sBody || !rBody) return;

    [wBody, sBody, rBody].forEach(function (tb) {
      tb.classList.add("d-none");
      tb.setAttribute("hidden", "hidden");
    });

    var active =
      metric === "sets" ? sBody : metric === "reps" ? rBody : wBody;
    active.classList.remove("d-none");
    active.removeAttribute("hidden");

    if (th && LABELS[metric]) {
      th.textContent = LABELS[metric];
    }
  }

  function bindRoot(root) {
    var prefix = root.getAttribute("data-lb-prefix");
    if (!prefix) return;
    var sel = document.getElementById(prefix + "-rank-by");
    if (!sel) return;

    function apply() {
      var v = (sel.value || "workouts").toLowerCase();
      if (v !== "sets" && v !== "reps") v = "workouts";
      showMetric(root, prefix, v);
    }

    sel.addEventListener("change", apply);
    apply();
  }

  document.querySelectorAll("[data-lb-prefix]").forEach(bindRoot);
})();
