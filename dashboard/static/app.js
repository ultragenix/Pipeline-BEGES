(function () {
  "use strict";

  const constats = Array.from(document.querySelectorAll(".constat"));
  if (constats.length === 0) {
    return;
  }

  const company = document.getElementById("filter-company");
  const severity = document.getElementById("filter-severity");
  const family = document.getElementById("filter-family");
  const status = document.getElementById("filter-status");
  const search = document.getElementById("filter-search");
  const reset = document.getElementById("filter-reset");
  const count = document.getElementById("filter-count");
  const empty = document.getElementById("filter-empty");

  function normalize(value) {
    return value
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function applyFilters() {
    const query = normalize(search.value.trim());
    let visible = 0;

    for (const constat of constats) {
      const matchesCompany = !company.value || constat.dataset.company === company.value;
      const matchesSeverity = !severity.value || constat.dataset.severity === severity.value;
      const matchesFamily = !family.value || constat.dataset.family === family.value;
      const matchesStatus = !status.value || constat.dataset.status === status.value;
      const haystack = normalize(constat.dataset.search || "");
      const matchesSearch = !query || haystack.includes(query);
      const show =
        matchesCompany && matchesSeverity && matchesFamily && matchesStatus && matchesSearch;

      constat.hidden = !show;
      if (show) {
        visible += 1;
      }
    }

    const plural = visible > 1 ? "s" : "";
    count.textContent = `${visible} constat${plural} affiché${plural}.`;
    empty.hidden = visible !== 0;
  }

  for (const control of [company, severity, family, status]) {
    control.addEventListener("change", applyFilters);
  }
  search.addEventListener("input", applyFilters);

  reset.addEventListener("click", function () {
    company.value = "";
    severity.value = "";
    family.value = "";
    status.value = "";
    search.value = "";
    applyFilters();
    search.focus();
  });

  applyFilters();
})();
