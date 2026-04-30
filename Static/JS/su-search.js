(function () {
  "use strict";

  var pageSize = 2;
  var workoutInput = document.getElementById("su-workout-search");
  var workoutTiles = Array.prototype.slice.call(
    document.querySelectorAll(".js-su-workout-tile")
  );
  var prevBtn = document.getElementById("suPrevWorkouts");
  var nextBtn = document.getElementById("suNextWorkouts");
  var pageIndicator = document.getElementById("suWorkoutsPageIndicator");
  var noWorkoutMatch = document.getElementById("su-no-workouts-match");
  var currentPage = 1;
  var filteredTiles = workoutTiles.slice();

  function updateWorkoutsView() {
    if (!workoutTiles.length) {
      if (pageIndicator) pageIndicator.textContent = "Page 1 of 1";
      if (prevBtn) prevBtn.disabled = true;
      if (nextBtn) nextBtn.disabled = true;
      if (noWorkoutMatch) noWorkoutMatch.classList.add("d-none");
      return;
    }

    var totalPages = Math.max(1, Math.ceil(filteredTiles.length / pageSize));
    if (currentPage > totalPages) currentPage = totalPages;
    var start = (currentPage - 1) * pageSize;
    var end = start + pageSize;

    for (var i = 0; i < workoutTiles.length; i++) {
      var tile = workoutTiles[i];
      var idx = filteredTiles.indexOf(tile);
      var visible = idx >= start && idx < end;
      tile.style.display = visible ? "" : "none";
    }

    if (pageIndicator) {
      pageIndicator.textContent = "Page " + currentPage + " of " + totalPages;
    }
    if (prevBtn) prevBtn.disabled = currentPage <= 1;
    if (nextBtn) nextBtn.disabled = currentPage >= totalPages;

    if (noWorkoutMatch) {
      var q = (workoutInput && workoutInput.value ? workoutInput.value : "").trim();
      if (q && filteredTiles.length === 0) {
        noWorkoutMatch.classList.remove("d-none");
      } else {
        noWorkoutMatch.classList.add("d-none");
      }
    }
  }

  function applyWorkoutSearch() {
    if (!workoutTiles.length) return;
    var q = (workoutInput && workoutInput.value ? workoutInput.value : "")
      .trim()
      .toLowerCase();
    filteredTiles = workoutTiles.filter(function (tile) {
      var hay = (tile.getAttribute("data-workout-search") || "").toLowerCase();
      return !q || hay.indexOf(q) !== -1;
    });
    currentPage = 1;
    updateWorkoutsView();
  }

  if (workoutInput) workoutInput.addEventListener("input", applyWorkoutSearch);
  if (prevBtn) {
    prevBtn.addEventListener("click", function () {
      currentPage = Math.max(1, currentPage - 1);
      updateWorkoutsView();
    });
  }
  if (nextBtn) {
    nextBtn.addEventListener("click", function () {
      var totalPages = Math.max(
        1,
        Math.ceil(filteredTiles.length / pageSize)
      );
      currentPage = Math.min(totalPages, currentPage + 1);
      updateWorkoutsView();
    });
  }
  updateWorkoutsView();

  var memberInput = document.getElementById("su-member-search");
  var memberRows = Array.prototype.slice.call(
    document.querySelectorAll(".js-su-attendance-row")
  );
  var noMemberMatch = document.getElementById("su-no-members-match");

  function applyMemberSearch() {
    if (!memberRows.length) {
      if (noMemberMatch) noMemberMatch.classList.add("d-none");
      return;
    }
    var q = (memberInput && memberInput.value ? memberInput.value : "")
      .trim()
      .toLowerCase();
    var visible = 0;
    for (var j = 0; j < memberRows.length; j++) {
      var row = memberRows[j];
      var hay = (row.getAttribute("data-member-search") || "").toLowerCase();
      var show = !q || hay.indexOf(q) !== -1;
      row.style.display = show ? "" : "none";
      if (show) visible += 1;
    }
    if (noMemberMatch) {
      if (q && visible === 0) noMemberMatch.classList.remove("d-none");
      else noMemberMatch.classList.add("d-none");
    }
  }

  if (memberInput) memberInput.addEventListener("input", applyMemberSearch);
})();
