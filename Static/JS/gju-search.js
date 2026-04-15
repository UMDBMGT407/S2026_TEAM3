document.addEventListener("DOMContentLoaded", () => {
  const groupInput = document.getElementById("gju-group-search");
  const groupList = document.getElementById("gju-group-search-list");
  const groupCards = Array.from(document.querySelectorAll("[data-group-card]"));

  const memberInput = document.getElementById("gju-member-search");
  const memberList = document.getElementById("gju-member-search-list");
  const memberRows = Array.from(document.querySelectorAll("[data-member-row]"));

  if (groupInput && groupList) {
    const seenGroups = new Set();
    const allGroupsOption = document.createElement("option");
    allGroupsOption.value = "All Groups";
    groupList.appendChild(allGroupsOption);

    groupCards.forEach((card) => {
      const name = (card.dataset.groupName || "").trim();
      if (!name || seenGroups.has(name.toLowerCase())) {
        return;
      }
      seenGroups.add(name.toLowerCase());
      const option = document.createElement("option");
      option.value = name;
      groupList.appendChild(option);
    });

    const filterGroups = () => {
      const query = groupInput.value.trim().toLowerCase();
      const showAll = !query || query === "all groups";
      groupCards.forEach((card) => {
        const groupName = (card.dataset.groupName || "").toLowerCase();
        const isMatch = showAll || groupName.includes(query);
        card.style.display = isMatch ? "" : "none";
      });
    };

    groupInput.addEventListener("input", filterGroups);
    groupInput.addEventListener("change", filterGroups);
  }

  if (memberInput && memberList) {
    const seenMembers = new Set();
    const allMembersOption = document.createElement("option");
    allMembersOption.value = "All Members";
    memberList.appendChild(allMembersOption);

    memberRows.forEach((row) => {
      const name = (row.dataset.memberName || "").trim();
      if (!name || seenMembers.has(name.toLowerCase())) {
        return;
      }
      seenMembers.add(name.toLowerCase());
      const option = document.createElement("option");
      option.value = name;
      memberList.appendChild(option);
    });

    const filterMembers = () => {
      const query = memberInput.value.trim().toLowerCase();
      const showAll = !query || query === "all members";
      memberRows.forEach((row) => {
        const name = (row.dataset.memberName || "").toLowerCase();
        const email = (row.dataset.memberEmail || "").toLowerCase();
        const isMatch = showAll || name.includes(query) || email.includes(query);
        row.style.display = isMatch ? "" : "none";
        const maybeDivider = row.nextElementSibling;
        if (maybeDivider && maybeDivider.classList.contains("gju-member-divider")) {
          maybeDivider.style.display = isMatch ? "" : "none";
        }
      });
    };

    memberInput.addEventListener("input", filterMembers);
    memberInput.addEventListener("change", filterMembers);
  }
});
