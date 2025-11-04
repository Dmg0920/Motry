(() => {
  "use strict";

  function parseBrandMap() {
    const dataElement = document.getElementById("brand-map-data");
    if (!dataElement) {
      return {};
    }

    try {
      const raw = dataElement.textContent || "{}";
      return JSON.parse(raw);
    } catch (error) {
      console.warn("[Motry] Failed to parse brand map:", error);
      return {};
    }
  }

  function buildBrandOptions(brandMap, type, currentValue) {
    const fragment = document.createDocumentFragment();
    const emptyOption = document.createElement("option");
    emptyOption.value = "";
    emptyOption.textContent = "全部品牌";
    fragment.appendChild(emptyOption);

    const seen = new Set();

    function appendOptions(items) {
      items.forEach((name) => {
        if (!name || seen.has(name)) {
          return;
        }
        seen.add(name);
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        if (name === currentValue) {
          option.selected = true;
        }
        fragment.appendChild(option);
      });
    }

    if (!type) {
      Object.values(brandMap).forEach((items) => appendOptions(items));
    } else if (brandMap[type]) {
      appendOptions(brandMap[type]);
    }

    return fragment;
  }

  function initBrandSelects(brandMap) {
    const selects = document.querySelectorAll("[data-brand-select]");
    if (!selects.length) {
      return;
    }

    selects.forEach((select) => {
      const typeSelector = select.dataset.typeInput
        ? document.querySelector(select.dataset.typeInput)
        : select.form && select.form.querySelector('select[name="type"]');

      const refreshOptions = () => {
        const current = select.dataset.selectedValue || select.value || "";
        const typeValue = typeSelector ? typeSelector.value : "";

        while (select.options.length > 0) {
          select.remove(0);
        }
        select.appendChild(buildBrandOptions(brandMap, typeValue, current));
        if (current) {
          select.value = current;
        }
      };

      if (typeSelector) {
        typeSelector.addEventListener("change", refreshOptions);
      }

      refreshOptions();

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
    const brandMap = parseBrandMap();
    initBrandSelects(brandMap);
    initImageFallbacks();
  });
})();
