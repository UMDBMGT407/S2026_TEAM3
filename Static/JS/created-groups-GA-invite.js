(function () {
  var wrap = document.querySelector(".cgga-invite-wrap");
  if (!wrap) return;

  var groupIdRaw = wrap.getAttribute("data-group-id") || "";
  var groupId = String(groupIdRaw).trim();
  var searchUrl = wrap.getAttribute("data-search-url") || "/api/group-admin/user-email-search";
  var candidatesUrl =
    wrap.getAttribute("data-candidates-url") ||
    "/api/group-admin/group-invite-candidates";
  var form = document.getElementById("cgga-invite-form");
  var emailInput = document.getElementById("cgga-invite-email-input");
  var userIdInput = document.getElementById("cgga-invite-user-id");
  var listEl = document.getElementById("cgga-invite-suggestions");
  var candidateSelect = document.getElementById("cgga-invite-candidate-select");
  var groupMemberSelect = document.getElementById("cgga-group-member-select");
  if (!form || !emailInput || !userIdInput || !listEl) return;

  var debounceTimer = null;
  var lastResults = [];

  function setExpanded(on) {
    emailInput.setAttribute("aria-expanded", on ? "true" : "false");
  }

  function hideList() {
    listEl.classList.add("d-none");
    listEl.setAttribute("hidden", "hidden");
    listEl.style.display = "none";
    listEl.innerHTML = "";
    lastResults = [];
    setExpanded(false);
  }

  function showList() {
    listEl.classList.remove("d-none");
    listEl.removeAttribute("hidden");
    listEl.style.display = "block";
    setExpanded(true);
  }

  function clearSelection() {
    userIdInput.value = "";
    if (candidateSelect) {
      candidateSelect.value = "";
    }
  }

  emailInput.addEventListener("input", function () {
    clearSelection();
    var q = emailInput.value.trim();
    if (debounceTimer) clearTimeout(debounceTimer);
    if (q.length < 1) {
      hideList();
      return;
    }
    debounceTimer = setTimeout(function () {
      debounceTimer = null;
      if (!groupId || !/^\d+$/.test(groupId)) {
        hideList();
        return;
      }
      var url =
        searchUrl +
        "?group_id=" +
        encodeURIComponent(groupId) +
        "&q=" +
        encodeURIComponent(q);
      fetch(url, { credentials: "same-origin" })
        .then(function (res) {
          if (!res.ok) return [];
          return res.json();
        })
        .then(function (data) {
          if (!Array.isArray(data)) {
            hideList();
            return;
          }
          lastResults = data;
          listEl.innerHTML = "";
          if (data.length === 0) {
            hideList();
            return;
          }
          data.forEach(function (row, idx) {
            var li = document.createElement("li");
            li.setAttribute("role", "option");
            li.setAttribute("tabindex", "0");
            li.className = "cgga-invite-suggestion list-group-item";
            li.dataset.userId = String(row.user_id);
            li.dataset.email = row.user_email || "";
            if (row.user_name) {
              var nameEl = document.createElement("span");
              nameEl.className = "cgga-invite-suggestion-name";
              nameEl.textContent = row.user_name;
              li.appendChild(nameEl);
            }
            var emailEl = document.createElement("span");
            emailEl.className = "cgga-invite-suggestion-email";
            emailEl.textContent = row.user_email || "";
            li.appendChild(emailEl);
            li.addEventListener("mousedown", function (e) {
              e.preventDefault();
            });
            li.addEventListener("click", function () {
              pick(row.user_id, row.user_email);
            });
            li.addEventListener("keydown", function (e) {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                pick(row.user_id, row.user_email);
              }
            });
            listEl.appendChild(li);
          });
          showList();
        })
        .catch(function () {
          hideList();
        });
    }, 280);
  });

  function pick(uid, email) {
    userIdInput.value = String(uid);
    emailInput.value = email || "";
    hideList();
    if (candidateSelect) {
      candidateSelect.value = String(uid);
    }
    emailInput.focus();
  }

  function loadInviteCandidates() {
    if (!candidateSelect) return;
    candidateSelect.innerHTML = "";
    var ph = document.createElement("option");
    ph.value = "";
    ph.textContent = "Select someone to invite…";
    candidateSelect.appendChild(ph);
    if (!groupId || !/^\d+$/.test(groupId)) {
      candidateSelect.disabled = true;
      return;
    }
    candidateSelect.disabled = true;
    fetch(
      candidatesUrl + "?group_id=" + encodeURIComponent(groupId),
      { credentials: "same-origin" }
    )
      .then(function (res) {
        return res.ok ? res.json() : [];
      })
      .then(function (data) {
        candidateSelect.innerHTML = "";
        candidateSelect.appendChild(ph.cloneNode(true));
        if (!Array.isArray(data)) {
          candidateSelect.disabled = false;
          return;
        }
        data.forEach(function (row) {
          var opt = document.createElement("option");
          opt.value = String(row.user_id);
          var nm = (row.user_name || "").trim() || "User";
          opt.textContent = nm + " (" + (row.user_email || "") + ")";
          opt.setAttribute("data-email", row.user_email || "");
          candidateSelect.appendChild(opt);
        });
        candidateSelect.disabled = false;
      })
      .catch(function () {
        candidateSelect.innerHTML = "";
        candidateSelect.appendChild(ph.cloneNode(true));
        candidateSelect.disabled = false;
      });
  }

  if (candidateSelect) {
    candidateSelect.addEventListener("change", function () {
      var v = candidateSelect.value;
      if (!v) {
        clearSelection();
        emailInput.value = "";
        return;
      }
      var opt = candidateSelect.options[candidateSelect.selectedIndex];
      var em = opt ? opt.getAttribute("data-email") || "" : "";
      userIdInput.value = v;
      emailInput.value = em;
      hideList();
    });
    loadInviteCandidates();
  }

  if (groupMemberSelect) {
    groupMemberSelect.addEventListener("change", function () {
      var uid = groupMemberSelect.value;
      document
        .querySelectorAll("tr.cgga-member-row-flash")
        .forEach(function (el) {
          el.classList.remove("cgga-member-row-flash");
        });
      if (!uid) return;
      var row = document.querySelector(
        'tr[data-cgga-user-id="' + uid.replace(/"/g, "") + '"]'
      );
      if (!row) return;
      row.scrollIntoView({ block: "nearest", behavior: "smooth" });
      row.classList.add("cgga-member-row-flash");
      window.setTimeout(function () {
        row.classList.remove("cgga-member-row-flash");
      }, 2000);
    });
  }

  document.addEventListener("click", function (e) {
    if (!wrap.contains(e.target)) hideList();
  });

  form.addEventListener("submit", function (e) {
    if (!userIdInput.value.trim()) {
      e.preventDefault();
      alert(
        "Choose someone to invite using the invite list, the search box, or the suggestions."
      );
    }
  });
})();
