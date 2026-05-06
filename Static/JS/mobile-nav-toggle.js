(() => {
  const MOBILE_QUERY = "(max-width: 991.98px)";
  const BODY_OPEN_CLASS = "mobile-nav-expanded";
  const BTN_CLASS = "global-mobile-nav-toggle";
  const HEADER_SELECTORS = [".topbar", 'header[class*="-topbar"]'];
  const NAV_SELECTORS = [".navigation-bar", 'aside[class*="-sidebar"] nav'];

  function queryFirst(root, selectors) {
    for (const selector of selectors) {
      const el = root.querySelector(selector);
      if (el) return el;
    }
    return null;
  }

  function syncButtonsExpanded(isExpanded) {
    document.querySelectorAll(`.${BTN_CLASS}`).forEach((btn) => {
      btn.setAttribute("aria-expanded", isExpanded ? "true" : "false");
    });
  }

  function onToggleClick() {
    const isExpanded = document.body.classList.toggle(BODY_OPEN_CLASS);
    syncButtonsExpanded(isExpanded);
  }

  function ensureToggleButtons() {
    const headers = HEADER_SELECTORS.flatMap((sel) =>
      Array.from(document.querySelectorAll(sel))
    );
    headers.forEach((header) => {
      if (header.querySelector(`.${BTN_CLASS}`)) return;
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = BTN_CLASS;
      btn.setAttribute("aria-label", "Toggle navigation");
      btn.setAttribute("aria-expanded", "false");
      btn.textContent = "Menu";
      btn.addEventListener("click", onToggleClick);
      header.insertBefore(btn, header.firstChild);
    });
  }

  function applyViewportState(mediaQueryList) {
    if (!mediaQueryList.matches) {
      document.body.classList.remove(BODY_OPEN_CLASS);
      syncButtonsExpanded(false);
    }
  }

  function setupNavMeta() {
    const nav = queryFirst(document, NAV_SELECTORS);
    if (!nav) return;
    if (!nav.id) nav.id = "global-mobile-nav";
    document.querySelectorAll(`.${BTN_CLASS}`).forEach((btn) => {
      btn.setAttribute("aria-controls", nav.id);
    });
  }

  function init() {
    ensureToggleButtons();
    setupNavMeta();
    const mq = window.matchMedia(MOBILE_QUERY);
    applyViewportState(mq);
    if (typeof mq.addEventListener === "function") {
      mq.addEventListener("change", () => applyViewportState(mq));
    } else if (typeof mq.addListener === "function") {
      mq.addListener(() => applyViewportState(mq));
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();
