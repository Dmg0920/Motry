(() => {
  "use strict";

  const WS_PATH =
    (window.location.protocol === "https:" ? "wss://" : "ws://") +
    window.location.host +
    "/ws/motry/notifications/";

  function ensureContainer() {
    let container = document.getElementById("motry-toast-container");
    if (container) return container;
    container = document.createElement("div");
    container.id = "motry-toast-container";
    container.style.position = "fixed";
    container.style.right = "16px";
    container.style.bottom = "16px";
    container.style.display = "flex";
    container.style.flexDirection = "column";
    container.style.gap = "8px";
    container.style.zIndex = "9999";
    document.body.appendChild(container);
    return container;
  }

  function showToast(message) {
    const container = ensureContainer();
    const toast = document.createElement("div");
    toast.textContent = message;
    toast.style.background = "rgba(0, 0, 0, 0.82)";
    toast.style.color = "#fff";
    toast.style.padding = "10px 12px";
    toast.style.borderRadius = "8px";
    toast.style.boxShadow = "0 6px 24px rgba(0,0,0,0.18)";
    toast.style.fontSize = "14px";
    toast.style.maxWidth = "320px";
    toast.style.lineHeight = "1.4";
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transition = "opacity 200ms ease";
      setTimeout(() => toast.remove(), 220);
    }, 3200);
  }

  function handleMessage(event) {
    try {
      const data = JSON.parse(event.data || "{}");
      if (data.type === "new_post") {
        const vehicle = data.vehicle?.name || "車輛";
        showToast(`新貼文：${vehicle} — ${data.title || "新分享"}`);
      }
    } catch (err) {
      console.warn("[Motry] 無法解析 WebSocket 訊息", err);
    }
  }

  function initWebSocket() {
    if (!("WebSocket" in window)) {
      console.warn("[Motry] 瀏覽器不支援 WebSocket，略過即時通知。");
      return;
    }

    try {
      const socket = new WebSocket(WS_PATH);
      socket.onmessage = handleMessage;
      socket.onerror = (e) => console.warn("[Motry] 通知 WebSocket 錯誤", e);
      socket.onclose = () =>
        console.warn("[Motry] 通知 WebSocket 已關閉，稍後可重新整理再試。");
    } catch (err) {
      console.warn("[Motry] 無法建立 WebSocket 連線", err);
    }
  }

  document.addEventListener("DOMContentLoaded", initWebSocket);
})();
