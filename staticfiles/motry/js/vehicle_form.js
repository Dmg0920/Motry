/**
 * Vehicle form module responsible for refreshing the form
 * when the vehicle type selector changes.
 */
const VehicleFormApp = (() => {
  "use strict";

  function init() {
    const form = document.getElementById("vehicle-form");
    const typeSelect = document.getElementById("id_type");
    const refreshField = document.getElementById("refresh-flag");

    if (!form || !typeSelect || !refreshField) {
      return;
    }

    typeSelect.addEventListener("change", () => {
      refreshField.value = "1";
      form.submit();
    });
  }

  return {
    init,
  };
})();

document.addEventListener("DOMContentLoaded", () => {
  VehicleFormApp.init();
});
