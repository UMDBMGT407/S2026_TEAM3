(function () {
  var wrap = document.querySelector(".cgga-invite-wrap");
  if (!wrap) return;

  var groupId = wrap.getAttribute("data-group-id");
  var searchUrl = wrap.getAttribute("data-search-url") || "/api/group-admin/user-email-search";
  var form = document.getElementById("cgga-invite-form");
  var emailInput = document.getElementById("cgga-invite-email-input");
  var userIdInput = document.getElementById("cgga-invite-user-id");
  var listEl = document.getElementById("cgga-invite-suggestions");
  if (!form || !emailInput || !userIdInput || !listEl) return;

  var debounceTimer = null;
  var lastResults = [];

  function hideList() {
    listEl.classList.add("d-none");
    listEl.setAttribute("hidden", "hidden");
    listEl.style.display = "none";
    listEl.innerHTML = "";
    lastResults = [];
  }

  function showList() {
    listEl.classList.remove("d-none");
    listEl.removeAttribute("hidden");
    listEl.style.display = "block";
  }

  function clearSelection() {
    userIdInput.value = "";
  }

  emailInput.addEventListener("input", function () {
    clearSelection();
    var q = emailInput.value.trim();
    if (debounceTimer) clearTimeout(debounceTimer);
    if (q.length < 2) {
      hideList();
      return;
    }
    debounceTimer = setTimeout(function () {
      debounceTimer = null;
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
            var primary = document.createElement("span");
            primary.className = "cgga-invite-suggestion-email";
            primary.textContent = row.user_email || "";
            li.appendChild(primary);
            if (row.user_name) {
              var sub = document.createElement("span");
              sub.className = "cgga-invite-suggestion-name";
              sub.textContent = row.user_name;
              li.appendChild(sub);
            }
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
    emailInput.focus();
  }

  document.addEventListener("click", function (e) {
    if (!wrap.contains(e.target)) hideList();
  });

  form.addEventListener("submit", function (e) {
    if (!userIdInput.value.trim()) {
      e.preventDefault();
      alert("Choose an email from the suggestions list.");
    }
  });
})();
