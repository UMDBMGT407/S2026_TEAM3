(function () {
  var root = document.querySelector("[data-workout-coach]");
  if (!root) return;

  var apiUrl = root.getAttribute("data-coach-api");
  var statusUrl = root.getAttribute("data-coach-status");
  var input = root.querySelector(".motiv-workout-coach__input");
  var sendBtn = root.querySelector(".motiv-workout-coach__send");
  var replyEl = root.querySelector(".motiv-workout-coach__reply");
  var errEl = root.querySelector(".motiv-workout-coach__error");
  var statusEl = root.querySelector(".motiv-workout-coach__status");

  function setError(msg) {
    if (errEl) errEl.textContent = msg || "";
  }

  function setReply(text) {
    if (replyEl) replyEl.textContent = text || "";
  }

  function setLoading(on) {
    if (sendBtn) {
      sendBtn.disabled = on;
      sendBtn.setAttribute("aria-busy", on ? "true" : "false");
    }
  }

  if (statusUrl && statusEl) {
    fetch(statusUrl, { credentials: "same-origin" })
      .then(function (r) {
        return r.json();
      })
      .then(function (data) {
        if (data && data.gemini_configured) {
          statusEl.textContent = "Gemini is configured on the server.";
          statusEl.className =
            "motiv-workout-coach__status motiv-workout-coach__status--ok";
        } else {
          statusEl.textContent =
            "Gemini is not configured yet. Add GEMINI_API_KEY to the server .env file.";
          statusEl.className =
            "motiv-workout-coach__status motiv-workout-coach__status--off";
        }
      })
      .catch(function () {
        statusEl.textContent = "";
      });
  }

  function send() {
    if (!apiUrl || !input) return;
    var msg = (input.value || "").trim();
    if (!msg) {
      setError("Please enter a question.");
      return;
    }
    if (msg.length > 4000) {
      setError("Please keep your message under 4000 characters.");
      return;
    }
    setError("");
    setLoading(true);
    fetch(apiUrl, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ message: msg }),
    })
      .then(function (r) {
        return r.json().then(function (data) {
          return { ok: r.ok, status: r.status, data: data };
        });
      })
      .then(function (res) {
        if (!res.ok) {
          setReply("");
          setError(
            (res.data && res.data.error) ||
              "Request failed (" + res.status + ")."
          );
          return;
        }
        if (res.data && res.data.error) {
          setReply("");
          setError(res.data.error);
          return;
        }
        setError("");
        setReply((res.data && res.data.reply) || "");
      })
      .catch(function () {
        setReply("");
        setError("Network error. Try again.");
      })
      .finally(function () {
        setLoading(false);
      });
  }

  if (sendBtn) sendBtn.addEventListener("click", send);
})();
