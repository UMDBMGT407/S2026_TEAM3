document.addEventListener("DOMContentLoaded", () => {
  const challengeInput = document.getElementById("ccga-challenge-search");
  const challengeList = document.getElementById("ccga-challenge-search-list");
  const challengeRows = Array.from(document.querySelectorAll("[data-challenge-row]"));

  const memberInput = document.getElementById("ccga-member-search");
  const memberList = document.getElementById("ccga-member-search-list");
  const participationTable = document.getElementById("ccga-participation-table");

  const getMemberRows = () => Array.from(document.querySelectorAll("[data-member-row]"));
  const getEmptyRow = () => document.querySelector("[data-member-empty-row]");

  if (challengeInput && challengeList) {
    const seenChallengeLabels = new Set();

    const allChallengesOption = document.createElement("option");
    allChallengesOption.value = "All Challenges";
    challengeList.appendChild(allChallengesOption);

    challengeRows.forEach((row) => {
      const challengeName = (row.dataset.challengeName || "").trim();
      const groupName = (row.dataset.groupName || "").trim();
      const label = groupName ? `${challengeName} (${groupName})` : challengeName;
      if (!label || seenChallengeLabels.has(label)) {
        return;
      }
      seenChallengeLabels.add(label);
      const opt = document.createElement("option");
      opt.value = label;
      challengeList.appendChild(opt);
    });

    const filterChallenges = () => {
      const query = challengeInput.value.trim().toLowerCase();
      const showAll = !query || query === "all challenges";

      challengeRows.forEach((row) => {
        const challengeName = (row.dataset.challengeName || "").toLowerCase();
        const groupName = (row.dataset.groupName || "").toLowerCase();
        const label = `${challengeName} (${groupName})`;
        const isMatch =
          showAll ||
          challengeName.includes(query) ||
          groupName.includes(query) ||
          label.includes(query);

        row.style.display = isMatch ? "" : "none";
        row.classList.toggle("ccga-row-highlight", !!query && isMatch);
      });
    };

    challengeInput.addEventListener("input", filterChallenges);
    challengeInput.addEventListener("change", filterChallenges);
  }

  const rebuildMemberOptions = () => {
    if (!memberList) {
      return;
    }
    memberList.innerHTML = "";
    const allMembersOption = document.createElement("option");
    allMembersOption.value = "All Members";
    memberList.appendChild(allMembersOption);

    const seenMemberNames = new Set();
    getMemberRows().forEach((row) => {
      const name = (row.dataset.memberName || "").trim();
      if (!name || seenMemberNames.has(name)) {
        return;
      }
      seenMemberNames.add(name);
      const opt = document.createElement("option");
      opt.value = name;
      memberList.appendChild(opt);
    });
  };

  const filterMembers = () => {
    const query = (memberInput?.value || "").trim().toLowerCase();
    const showAll = !query || query === "all members";
    const memberRows = getMemberRows();

    memberRows.forEach((row) => {
      const name = (row.dataset.memberName || "").toLowerCase();
      const isMatch = showAll || name.includes(query);
      row.style.display = isMatch ? "" : "none";
    });
  };

  const removeMemberRow = (row) => {
    row.remove();
    const memberRows = getMemberRows();
    const emptyRow = getEmptyRow();

    if (!memberRows.length && participationTable && !emptyRow) {
      const tbody = participationTable.querySelector("tbody");
      if (tbody) {
        const tr = document.createElement("tr");
        tr.setAttribute("data-member-empty-row", "");
        tr.innerHTML =
          '<td colspan="4" class="text-muted p-4">No participants found for this challenge\'s group.</td>';
        tbody.appendChild(tr);
      }
    }
    rebuildMemberOptions();
    filterMembers();
  };

  if (memberInput && memberList) {
    rebuildMemberOptions();
    memberInput.addEventListener("input", filterMembers);
    memberInput.addEventListener("change", filterMembers);
  }

  document.addEventListener("click", (event) => {
    const btn = event.target.closest(".ccga-row-delete-btn");
    if (!btn) {
      return;
    }
    const row = btn.closest("[data-member-row]");
    if (!row) {
      return;
    }
    removeMemberRow(row);
  });
});
