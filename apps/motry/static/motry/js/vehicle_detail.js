(() => {
  "use strict";

  function initGarageToggle() {
    const button = document.querySelector("[data-garage-toggle]");
    if (!button || typeof sendRequest !== "function") {
      return;
    }

    const statusEl = document.querySelector("[data-garage-status]");
    const vehicleId = Number(button.dataset.vehicleId);

    if (!vehicleId) {
      return;
    }

    const setState = (inGarage) => {
      button.dataset.inGarage = inGarage ? "true" : "false";
      if (inGarage) {
        button.textContent = "❤️ 已在我的車庫";
        button.classList.remove("button-ghost");
      } else {
        button.textContent = "🤍 加入我的車庫";
        if (!button.classList.contains("button-ghost")) {
          button.classList.add("button-ghost");
        }
      }

      if (statusEl) {
        statusEl.textContent = inGarage
          ? "已收藏，可在「我的車庫」管理備註與照片。"
          : "收藏後可在「我的車庫」快速管理車輛與心得。";
      }
    };

    const setLoading = (loading) => {
      if (loading) {
        button.textContent = "⏳ 處理中...";
        button.disabled = true;
        button.classList.add("is-loading");
      } else {
        button.disabled = false;
        button.classList.remove("is-loading");
        setState(button.dataset.inGarage === "true");
      }
    };

    setState(button.dataset.inGarage === "true");

    button.addEventListener("click", () => {
      if (button.disabled) {
        return;
      }

      const inGarage = button.dataset.inGarage === "true";
      if (inGarage && !window.confirm("確定要從車庫中移除嗎？")) {
        return;
      }

      setLoading(true);
      const action = inGarage ? "remove" : "add";
      const url = action === "add" ? `/api/garage/add/${vehicleId}/` : `/api/garage/remove/${vehicleId}/`;

      sendRequest({
        url,
        method: "POST",
        onSuccess: (data = {}) => {
          const nextState = Boolean(data.in_garage);
          setState(nextState);
          const message =
            data.message ||
            (nextState ? "已加入我的車庫！" : "已從我的車庫移除。");
          alert(message);
        },
        onError: (error) => {
          alert(error?.message || "操作失敗，請稍後再試。");
        },
        onComplete: () => {
          setLoading(false);
        },
      });
    });
  }

  document.addEventListener("DOMContentLoaded", initGarageToggle);
})();
