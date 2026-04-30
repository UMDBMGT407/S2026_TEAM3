(function () {
  "use strict";

  var pageSize = 3;
  var challengeInput = document.getElementById("chu-challenge-search");
  var challengeTiles = Array.prototype.slice.call(
    document.querySelectorAll(".js-chu-challenge-tile")
  );
  var prevBtn = document.getElementById("chuPrevChallenges");
  var nextBtn = document.getElementById("chuNextChallenges");
  var pageIndicator = document.getElementById("chuChallengesPageIndicator");
  var noChallengeMatch = document.getElementById("chu-no-challenges-match");
  var currentPage = 1;
  var filteredTiles = challengeTiles.slice();

  function updateChallengesView() {
    if (!challengeTiles.length) {
      if (pageIndicator) pageIndicator.textContent = "Page 1 of 1";
      if (prevBtn) prevBtn.disabled = true;
      if (nextBtn) nextBtn.disabled = true;
      if (noChallengeMatch) noChallengeMatch.classList.add("d-none");
      return;
    }

    var totalPages = Math.max(1, Math.ceil(filteredTiles.length / pageSize));
    if (currentPage > totalPages) currentPage = totalPages;
    var start = (currentPage - 1) * pageSize;
    var end = start + pageSize;

    for (var i = 0; i < challengeTiles.length; i++) {
      var tile = challengeTiles[i];
      var idx = filteredTiles.indexOf(tile);
      var visible = idx >= start && idx < end;
      tile.style.display = visible ? "" : "none";
    }

    if (pageIndicator) {
      pageIndicator.textContent = "Page " + currentPage + " of " + totalPages;
    }
    if (prevBtn) prevBtn.disabled = currentPage <= 1;
    if (nextBtn) nextBtn.disabled = currentPage >= totalPages;

    if (noChallengeMatch) {
      var q = (challengeInput && challengeInput.value ? challengeInput.value : "").trim();
      if (q && filteredTiles.length === 0) {
        noChallengeMatch.classList.remove("d-none");
      } else {
        noChallengeMatch.classList.add("d-none");
      }
    }
  }

  function applyChallengeSearch() {
    if (!challengeTiles.length) return;
    var q = (challengeInput && challengeInput.value ? challengeInput.value : "")
      .trim()
      .toLowerCase();
    filteredTiles = challengeTiles.filter(function (tile) {
      var hay = (tile.getAttribute("data-challenge-search") || "").toLowerCase();
      return !q || hay.indexOf(q) !== -1;
    });
    currentPage = 1;
    updateChallengesView();
  }

  if (challengeInput) challengeInput.addEventListener("input", applyChallengeSearch);
  if (prevBtn) {
    prevBtn.addEventListener("click", function () {
      currentPage = Math.max(1, currentPage - 1);
      updateChallengesView();
    });
  }
  if (nextBtn) {
    nextBtn.addEventListener("click", function () {
      var totalPages = Math.max(
        1,
        Math.ceil(filteredTiles.length / pageSize)
      );
      currentPage = Math.min(totalPages, currentPage + 1);
      updateChallengesView();
    });
  }
  updateChallengesView();
})();
