(() => {
  "use strict";

  const OVERLAY_ID = "motry-loading-overlay";

  function ensureOverlay() {
    let overlay = document.getElementById(OVERLAY_ID);
    if (overlay) {
      return overlay;
    }
    overlay = document.createElement("div");
    overlay.id = OVERLAY_ID;
    overlay.style.position = "fixed";
    overlay.style.inset = "0";
    overlay.style.background = "rgba(0, 0, 0, 0.35)";
    overlay.style.display = "flex";
    overlay.style.alignItems = "center";
    overlay.style.justifyContent = "center";
    overlay.style.zIndex = "9999";
    overlay.style.color = "#fff";
    overlay.style.fontSize = "1rem";
    overlay.style.fontWeight = "600";
    overlay.style.letterSpacing = "0.05em";
    overlay.textContent = "處理中...";
    overlay.hidden = true;
    document.body.appendChild(overlay);
    return overlay;
  }

  function getCsrfToken() {
    const tokenInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (tokenInput && tokenInput.value) {
      return tokenInput.value;
    }
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    if (match) {
      return decodeURIComponent(match[1]);
    }
    return null;
  }

  async function parseResponse(response) {
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      return await response.json();
    }
    return await response.text();
  }

  async function sendRequest({
    url,
    method = "GET",
    params = null,
    data = null,
    onSuccess = () => {},
    onError = null,
    onComplete = null,
    showLoadingOverlay = false,
  }) {
    if (!url) {
      throw new Error("URL is required");
    }

    method = method.toUpperCase();

    if (params && typeof params === "object") {
      const query = new URLSearchParams(params).toString();
      if (query) {
        url += url.includes("?") ? `&${query}` : `?${query}`;
      }
    }

    const headers = {
      Accept: "application/json",
    };

    let body = null;
    const csrfToken = getCsrfToken();
    const requiresCsrf = !["GET", "HEAD", "OPTIONS"].includes(method);
    if (requiresCsrf && csrfToken) {
      headers["X-CSRFToken"] = csrfToken;
    }

    if (data instanceof FormData) {
      body = data;
    } else if (data && typeof data === "object") {
      headers["Content-Type"] = "application/json";
      body = JSON.stringify(data);
    } else if (typeof data === "string") {
      body = data;
    }

    const overlay = showLoadingOverlay ? ensureOverlay() : null;
    if (overlay) {
      overlay.hidden = false;
    }

    try {
      const response = await fetch(url, {
        method,
        headers,
        body,
        credentials: "same-origin",
      });

      const payload = await parseResponse(response);

      if (!response.ok) {
        const error = {
          status: response.status,
          message:
            (typeof payload === "object" && payload && payload.message) ||
            response.statusText ||
            "Request failed",
          data: payload,
        };
        if (typeof onError === "function") {
          onError(error);
        } else {
          alert(error.message);
        }
        return;
      }

      if (typeof onSuccess === "function") {
        onSuccess(payload);
      }
    } catch (err) {
      const error = {
        status: 0,
        message: err?.message || "網路或系統發生錯誤，請稍後再試。",
        data: null,
      };
      if (typeof onError === "function") {
        onError(error);
      } else {
        alert(error.message);
      }
    } finally {
      if (overlay) {
        overlay.hidden = true;
      }
      if (typeof onComplete === "function") {
        onComplete();
      }
    }
  }

  window.sendRequest = sendRequest;
})();
