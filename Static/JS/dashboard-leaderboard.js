(function () {
  var LABELS = { workouts: "Workouts", sets: "Sets", reps: "Reps" };
  var EM_DASH = "\u2014";

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

  function syncPodiumLabels(prefix) {
    var sel = document.getElementById(prefix + "-rank-by");
    var v = sel ? (sel.value || "workouts").toLowerCase() : "workouts";
    if (v !== "sets" && v !== "reps") v = "workouts";
    var bodyId =
      prefix +
      "-lb-tbody-" +
      (v === "sets" ? "sets" : v === "reps" ? "reps" : "workouts");
    var tb = document.getElementById(bodyId);
    var names = [EM_DASH, EM_DASH, EM_DASH];
    if (tb) {
      var rows = tb.querySelectorAll("tr");
      var dataRows = [];
      for (var i = 0; i < rows.length; i++) {
        var cells = rows[i].querySelectorAll("td");
        if (cells.length >= 3) {
          dataRows.push((cells[1].textContent || "").trim());
        }
      }
      names[0] = dataRows[0] || EM_DASH;
      names[1] = dataRows[1] || EM_DASH;
      names[2] = dataRows[2] || EM_DASH;
    }
    var el1 = document.getElementById(prefix + "-podium-name-1");
    var el2 = document.getElementById(prefix + "-podium-name-2");
    var el3 = document.getElementById(prefix + "-podium-name-3");
    if (el1) el1.textContent = names[0];
    if (el2) el2.textContent = names[1];
    if (el3) el3.textContent = names[2];
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
      syncPodiumLabels(prefix);
    }

    sel.addEventListener("change", apply);
    apply();
  }

  document.querySelectorAll("[data-lb-prefix]").forEach(bindRoot);
})();
