document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("chu-challenge-search");
  const list = document.getElementById("chu-challenge-search-list");
  const cards = Array.from(document.querySelectorAll("[data-chu-challenge-card]"));
  const emptyFilter = document.getElementById("chu-filter-empty");

  if (!input || !cards.length) return;

  if (list) {
    const seen = new Set();
    const allOpt = document.createElement("option");
    allOpt.value = "All Challenges";
    list.appendChild(allOpt);
    cards.forEach((card) => {
      const title = (card.dataset.challengeTitle || "").trim();
      if (!title || seen.has(title.toLowerCase())) return;
      seen.add(title.toLowerCase());
      const opt = document.createElement("option");
      opt.value = title;
      list.appendChild(opt);
    });
  }

  const sync = () => {
    const q = input.value.trim().toLowerCase();
    const showAll = !q || q === "all challenges";
    let visible = 0;
    cards.forEach((card) => {
      const title = (card.dataset.challengeTitle || "").toLowerCase();
      const match = showAll || title.includes(q);
      card.style.display = match ? "" : "none";
      if (match) visible += 1;
    });
    if (emptyFilter) {
      emptyFilter.style.display = visible ? "none" : "";
    }
  };

  input.addEventListener("input", sync);
  input.addEventListener("change", sync);
  sync();
});
