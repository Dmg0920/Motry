(() => {
  "use strict";

  function parseBrandList() {
    const dataElement = document.getElementById("brand-list-data");
    if (!dataElement) {
      return [];
    }

    try {
      const raw = dataElement.textContent || "[]";
      return JSON.parse(raw);
    } catch (error) {
      console.warn("[Motry] Failed to parse brand list:", error);
      return [];
    }
  }

  function buildBrandOptions(brands, currentValue) {
    const fragment = document.createDocumentFragment();
    const emptyOption = document.createElement("option");
    emptyOption.value = "";
    emptyOption.textContent = "全部品牌";
    fragment.appendChild(emptyOption);

    brands.forEach((name) => {
      if (!name) {
        return;
      }
      const option = document.createElement("option");
      option.value = name;
      option.textContent = name;
      if (name === currentValue) {
        option.selected = true;
      }
      fragment.appendChild(option);
    });

    return fragment;
  }

  function initBrandSelects(brands) {
    const selects = document.querySelectorAll("[data-brand-select]");
    if (!selects.length) {
      return;
    }

    selects.forEach((select) => {
      const current = select.dataset.selectedValue || select.value || "";

      while (select.options.length > 0) {
        select.remove(0);
      }
      select.appendChild(buildBrandOptions(brands, current));
      if (current) {
        select.value = current;
      }

      select.addEventListener("change", () => {
        select.dataset.selectedValue = select.value;
      });
    });
  }

  function initImageFallbacks() {
    document.querySelectorAll("img[data-fallback]").forEach((img) => {
      img.addEventListener("error", function handleError() {
        if (img.dataset.fallbackApplied === "1") {
          return;
        }
        img.dataset.fallbackApplied = "1";
        img.src = img.dataset.fallback;
      });
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    const brands = parseBrandList();
    initBrandSelects(brands);
    initImageFallbacks();
  });
})();
