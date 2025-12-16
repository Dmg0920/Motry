(() => {
  "use strict";

  function initFavoriteToggle() {
    const button = document.querySelector("[data-favorite-toggle]");
    if (!button || typeof sendRequest !== "function") {
      return;
    }

    const statusEl = document.querySelector("[data-favorite-status]");
    const vehicleId = Number(button.dataset.vehicleId);

    if (!vehicleId) {
      return;
    }

    const setState = (inFavorite) => {
      button.dataset.inFavorite = inFavorite ? "true" : "false";
      button.textContent = inFavorite ? "⭐ 已在我的最愛" : "☆ 加入我的最愛";
      if (statusEl) {
        statusEl.textContent = inFavorite
          ? "已加入我的最愛，可於清單中快速找到它。"
          : "喜歡這台車嗎？加入我的最愛就不會忘記。";
      }
    };

    const setLoading = (loading) => {
      if (loading) {
        button.textContent = "⏳ 處理中...";
        button.disabled = true;
      } else {
        button.disabled = false;
        setState(button.dataset.inFavorite === "true");
      }
    };

    setState(button.dataset.inFavorite === "true");

    button.addEventListener("click", () => {
      if (button.disabled) return;
      const inFavorite = button.dataset.inFavorite === "true";
      const action = inFavorite ? "remove" : "add";
      const url =
        action === "add"
          ? `/api/favorites/add/${vehicleId}/`
          : `/api/favorites/remove/${vehicleId}/`;

      setLoading(true);
      sendRequest({
        url,
        method: "POST",
        onSuccess: (data = {}) => {
          const nextState = Boolean(data.favorite);
          setState(nextState);
          alert(
            data.message ||
              (nextState ? "已加入我的最愛！" : "已從我的最愛移除。")
          );
        },
        onError: (error) => {
          alert(error?.message || "操作失敗，請稍後再試。");
        },
        onComplete: () => setLoading(false),
      });
    });
  }

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
          ? "已加入車庫，可在「我的車庫」管理備註與照片。"
          : "如果這是你的座駕，可加入我的車庫集中管理。";
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
            (nextState ? "已加入我的車庫！" : "已從車庫中移除。");
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

  function initIntroEditor() {
    const section = document.querySelector("[data-intro-section]");
    if (!section) {
      return;
    }

    const editor = section.querySelector("[data-intro-editor]");
    const trigger = section.querySelector("[data-intro-edit-trigger]");
    if (!editor || !trigger) {
      return;
    }

    const cancel = editor.querySelector("[data-intro-cancel]");
    const input = editor.querySelector("[data-intro-input]");
    const previewTarget = editor.querySelector("[data-intro-preview-target]");
    const emptyState = section.querySelector("[data-intro-empty]");
    const initialPreview = previewTarget ? previewTarget.innerHTML : "";

    const toggleEditor = (show) => {
      editor.hidden = !show;
      trigger.setAttribute("aria-expanded", show ? "true" : "false");
      trigger.classList.toggle("is-active", show);
      if (show && input) {
        input.focus();
      }
      if (emptyState) {
        emptyState.hidden = show;
      }
    };

    const formatPreview = (value) => {
      if (!previewTarget) return;
      if (!value.trim()) {
        previewTarget.innerHTML = initialPreview || "輸入後即可預覽段落。";
        return;
      }
      const escaped = value
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
      previewTarget.innerHTML = escaped.replace(/\n/g, "<br />");
    };

    trigger.addEventListener("click", () => {
      const willOpen = editor.hidden;
      toggleEditor(willOpen);
    });

    if (cancel) {
      cancel.addEventListener("click", () => {
        toggleEditor(false);
        if (previewTarget) {
          previewTarget.innerHTML = initialPreview || "輸入後即可預覽段落。";
        }
      });
    }

    if (input) {
      input.addEventListener("input", (event) => {
        formatPreview(event.target.value);
      });
    }
  }

  function initReplyToggles() {
    const toggles = document.querySelectorAll("[data-reply-toggle]");
    if (!toggles.length) {
      return;
    }

    const hideAll = () => {
      document.querySelectorAll(".comment-form--inline").forEach((form) => {
        form.setAttribute("hidden", "");
      });
    };

    toggles.forEach((button) => {
      const targetId = button.dataset.target;
      if (!targetId) {
        return;
      }
      const form = document.getElementById(targetId);
      if (!form) {
        return;
      }

      button.addEventListener("click", () => {
        const isHidden = form.hasAttribute("hidden");
        if (isHidden) {
          hideAll();
          form.removeAttribute("hidden");
          const textarea = form.querySelector("textarea");
          if (textarea) {
            textarea.focus();
          }
        } else {
          form.setAttribute("hidden", "");
        }
      });
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    initFavoriteToggle();
    initGarageToggle();
    initIntroEditor();
    initReplyToggles();
  });
})();
