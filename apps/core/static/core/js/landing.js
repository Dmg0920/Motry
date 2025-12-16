(() => {
  "use strict";

  function hideOverlay(overlay) {
    if (!overlay) return;
    overlay.classList.add("is-hidden");
    overlay.setAttribute("aria-hidden", "true");
  }

  function initLandingWindow() {
    const overlay = document.querySelector("[data-landing-window]");
    if (!overlay) {
      return;
    }

    const closeButtons = overlay.querySelectorAll("[data-landing-close]");

    closeButtons.forEach((button) => {
      button.addEventListener("click", () => hideOverlay(overlay));
    });

    overlay.addEventListener("click", (event) => {
      if (event.target === overlay) {
        hideOverlay(overlay);
      }
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        hideOverlay(overlay);
      }
    });
  }

  document.addEventListener("DOMContentLoaded", initLandingWindow);
})();
