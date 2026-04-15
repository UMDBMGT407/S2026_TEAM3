document.addEventListener("DOMContentLoaded", () => {
  const sessionInput = document.getElementById("sga-session-search");
  const sessionList = document.getElementById("sga-session-search-list");
  const sessionRows = Array.from(document.querySelectorAll("[data-session-row]"));

  const memberInput = document.getElementById("sga-member-search");
  const memberList = document.getElementById("sga-member-search-list");
  const memberRows = Array.from(document.querySelectorAll("[data-member-row]"));

  if (sessionInput && sessionList) {
    const seenSessionLabels = new Set();

    const allSessionOption = document.createElement("option");
    allSessionOption.value = "All Sessions";
    sessionList.appendChild(allSessionOption);

    sessionRows.forEach((row) => {
      const sessionName = (row.dataset.sessionName || "").trim();
      const groupName = (row.dataset.groupName || "").trim();
      const label = groupName ? `${sessionName} (${groupName})` : sessionName;
      if (!label || seenSessionLabels.has(label)) {
        return;
      }
      seenSessionLabels.add(label);
      const opt = document.createElement("option");
      opt.value = label;
      sessionList.appendChild(opt);
    });

    const filterSessions = () => {
      const query = sessionInput.value.trim().toLowerCase();
      const showAll = !query || query === "all sessions";

      sessionRows.forEach((row) => {
        const sessionName = (row.dataset.sessionName || "").toLowerCase();
        const groupName = (row.dataset.groupName || "").toLowerCase();
        const label = `${sessionName} (${groupName})`;
        const isMatch =
          showAll ||
          sessionName.includes(query) ||
          groupName.includes(query) ||
          label.includes(query);

        row.style.display = isMatch ? "" : "none";
        row.classList.toggle("sga-row-highlight", !!query && isMatch);
      });
    };

    sessionInput.addEventListener("input", filterSessions);
    sessionInput.addEventListener("change", filterSessions);
  }

  if (memberInput && memberList) {
    const seenMemberNames = new Set();

    const allMemberOption = document.createElement("option");
    allMemberOption.value = "All Members";
    memberList.appendChild(allMemberOption);

    memberRows.forEach((row) => {
      const name = (row.dataset.memberName || "").trim();
      if (!name || seenMemberNames.has(name)) {
        return;
      }
      seenMemberNames.add(name);
      const opt = document.createElement("option");
      opt.value = name;
      memberList.appendChild(opt);
    });

    const filterMembers = () => {
      const query = memberInput.value.trim().toLowerCase();
      const showAll = !query || query === "all members";

      memberRows.forEach((row) => {
        const name = (row.dataset.memberName || "").toLowerCase();
        const email = (row.dataset.memberEmail || "").toLowerCase();
        const isMatch = showAll || name.includes(query) || email.includes(query);
        row.style.display = isMatch ? "" : "none";
      });
    };

    memberInput.addEventListener("input", filterMembers);
    memberInput.addEventListener("change", filterMembers);
  }
});
