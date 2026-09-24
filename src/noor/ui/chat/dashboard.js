(() => {
  const $ = (id) => document.getElementById(id);
  const datasetFile = $("datasetFile");
  const chatForm = $("chatForm");
  const chatInput = $("messageInput");
  const chatPanel = $("chatPanel");
  const noorOrb = $("noorOrb");
  const workspaceCommand = $("workspaceCommand");
  const workspaceCommandSend = $("workspaceCommandSend");
  const sidebarOrb = $("sidebarOrb");
  const openChatTop = $("openChatTop");
  const openChatDock = $("openChatDock");
  const openAttach = $("openAttach");
  const emptyAttach = $("emptyAttach");
  const table = $("dataTable");
  const tbody = table?.querySelector("tbody");
  const search = $("gridSearch");
  const sidebarStatus = $("sidebarStatus");
  const sidebarRows = $("sidebarRows");
  const sidebarColumns = $("sidebarColumns");
  const sidebarQuality = $("sidebarQuality");
  const sidebarMemory = $("sidebarMemory");

  let datasetPath = window.noorDatasetPath || null;
  let latestPreview = null;
  let latestProfile = null;
  let hiddenColumns = new Set();
  let sortDescending = false;
  let profileRequestedForPath = null;

  const originalFetch = window.fetch.bind(window);
  window.fetch = async (...args) => {
    const response = await originalFetch(...args);
    const requestUrl = typeof args[0] === "string" ? args[0] : args[0]?.url || "";
    if (requestUrl.endsWith("/api/upload") && response.ok) {
      try {
        const payload = await response.clone().json();
        datasetPath = payload.upload?.path || datasetPath;
        window.noorDatasetPath = datasetPath;
        window.setTimeout(autoProfile, 250);
      } catch { /* app.js handles the primary upload result */ }
    }
    if (requestUrl.endsWith("/api/preview") && response.ok) {
      try {
        latestPreview = await response.clone().json();
        updateSidebarPreview(latestPreview);
      } catch { /* ignore malformed preview telemetry */ }
    }
    if (requestUrl.endsWith("/api/profile") && response.ok) {
      try {
        latestProfile = await response.clone().json();
        renderDashboardMetrics(latestProfile);
        renderQuality(latestProfile);
        renderInsights(latestProfile);
        renderCharts(latestProfile);
        updateSidebarProfile(latestProfile);
      } catch { /* app.js remains the source of truth for profile rendering */ }
    }
    return response;
  };

  function formatNumber(value) {
    return Number(value || 0).toLocaleString();
  }

  function formatBytes(bytes) {
    const n = Number(bytes);
    if (!Number.isFinite(n)) return "—";
    if (n < 1024) return `${n} B`;
    if (n < 1024 ** 2) return `${(n / 1024).toFixed(1)} KB`;
    if (n < 1024 ** 3) return `${(n / 1024 ** 2).toFixed(1)} MB`;
    return `${(n / 1024 ** 3).toFixed(1)} GB`;
  }

  function openNoor() {
    if (!chatPanel) return;
    if (typeof window.openChat === "function") window.openChat();
    else {
      chatPanel.classList.add("is-open");
      chatPanel.setAttribute("aria-hidden", "false");
      noorOrb?.classList.add("is-hidden");
    }
  }

  function sendChatCommand(text) {
    const command = String(text || "").trim();
    if (!command || !chatInput || !chatForm) return;
    openNoor();
    chatInput.value = command;
    chatForm.requestSubmit();
  }

  function wireCommandSurface() {
    [sidebarOrb, openChatTop, openChatDock, noorOrb].forEach((button) => button?.addEventListener("click", openNoor));
    openAttach?.addEventListener("click", () => datasetFile?.click());
    emptyAttach?.addEventListener("click", () => datasetFile?.click());
    workspaceCommandSend?.addEventListener("click", () => sendChatCommand(workspaceCommand?.value));
    workspaceCommand?.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        sendChatCommand(workspaceCommand.value);
      }
    });
    document.querySelectorAll("[data-chat-prompt]").forEach((button) => {
      button.addEventListener("click", () => sendChatCommand(button.dataset.chatPrompt));
    });
  }

  function wireNavigation() {
    document.querySelectorAll(".sidebar-item").forEach((item) => {
      item.addEventListener("click", () => {
        const target = document.querySelector(`.workspace-tab[data-view="${CSS.escape(item.dataset.view)}"]`);
        target?.click();
        document.querySelectorAll(".sidebar-item").forEach((node) => node.classList.toggle("is-active", node === item));
      });
    });
    document.querySelectorAll(".workspace-tab").forEach((tab) => {
      tab.addEventListener("click", () => {
        document.querySelectorAll(".sidebar-item").forEach((item) => item.classList.toggle("is-active", item.dataset.view === tab.dataset.view));
      });
    });
  }

  function updateSidebarPreview(preview) {
    if (!preview) return;
    sidebarStatus && (sidebarStatus.textContent = "Ready");
    sidebarRows && (sidebarRows.textContent = `${formatNumber(preview.rows_returned)} preview rows`);
    sidebarColumns && (sidebarColumns.textContent = `${preview.columns?.length || 0} columns`);
  }

  function renderDashboardMetrics(profile) {
    const columns = Array.isArray(profile.column_profile) ? profile.column_profile : [];
    const totalCells = Number(profile.rows || 0) * Number(profile.columns || 0);
    const missing = columns.reduce((sum, column) => sum + Number(column.missing_count || 0), 0);
    const completeness = totalCells ? Math.max(0, 100 - (missing / totalCells) * 100) : 100;
    $("statRows") && ($("statRows").textContent = formatNumber(profile.rows));
    $("statRowsHint") && ($("statRowsHint").textContent = "full dataset");
    $("statColumns") && ($("statColumns").textContent = formatNumber(profile.columns));
    $("statColumnsHint") && ($("statColumnsHint").textContent = "profiled schema");
    $("statMissing") && ($("statMissing").textContent = formatNumber(missing));
    $("statMissingHint") && ($("statMissingHint").textContent = missing ? "missing cells" : "none detected");
    $("statDuplicates") && ($("statDuplicates").textContent = formatNumber(profile.duplicate_rows));
    $("statDuplicatesHint") && ($("statDuplicatesHint").textContent = profile.duplicate_rows ? "requires review" : "none detected");
    $("statQuality") && ($("statQuality").textContent = `${completeness.toFixed(1)}%`);
    $("statQualityHint") && ($("statQualityHint").textContent = "cell completeness");
    $("statMemory") && ($("statMemory").textContent = formatBytes(profile.memory_bytes));
    $("statMemoryHint") && ($("statMemoryHint").textContent = "pandas profile memory");
    $("statUpdated") && ($("statUpdated").textContent = "Just now");
    $("statUpdatedHint") && ($("statUpdatedHint").textContent = "Profile completed");
  }

  function updateSidebarProfile(profile) {
    const columns = Array.isArray(profile.column_profile) ? profile.column_profile : [];
    const missing = columns.reduce((sum, column) => sum + Number(column.missing_count || 0), 0);
    const totalCells = Number(profile.rows || 0) * Number(profile.columns || 0);
    const quality = totalCells ? 100 - (missing / totalCells) * 100 : 100;
    sidebarRows && (sidebarRows.textContent = `${formatNumber(profile.rows)} rows`);
    sidebarColumns && (sidebarColumns.textContent = `${formatNumber(profile.columns)} columns`);
    sidebarQuality && (sidebarQuality.textContent = `${quality.toFixed(1)}% complete`);
    sidebarMemory && (sidebarMemory.textContent = formatBytes(profile.memory_bytes));
  }

  function renderQuality(profile) {
    const columns = Array.isArray(profile.column_profile) ? profile.column_profile : [];
    const missing = columns.reduce((sum, column) => sum + Number(column.missing_count || 0), 0);
    const totalCells = Number(profile.rows || 0) * Number(profile.columns || 0);
    const quality = totalCells ? Math.max(0, 100 - (missing / totalCells) * 100) : 100;
    const overview = $("qualityOverview");
    if (overview) {
      overview.innerHTML = `<div class="quality-ring" style="--quality:${quality.toFixed(2)}%"><div><strong>${quality.toFixed(1)}%</strong><span>cell completeness</span></div></div>`;
    }
    const bars = $("qualityBars");
    if (bars) {
      const ranked = [...columns].sort((a, b) => Number(b.missing_count || 0) - Number(a.missing_count || 0));
      bars.innerHTML = ranked.map((column) => {
        const pct = Math.max(0, 100 - Number(column.missing_pct || 0));
        return `<div class="quality-bar-row"><span title="${escapeHtml(column.name)}">${escapeHtml(column.name)}</span><div class="quality-bar-track"><div class="quality-bar-fill" style="width:${pct.toFixed(2)}%"></div></div><span>${pct.toFixed(1)}%</span></div>`;
      }).join("") || `<div class="profile-placeholder"><strong>No columns returned</strong></div>`;
    }
  }

  function renderInsights(profile) {
    const target = $("insightGrid");
    if (!target) return;
    const columns = Array.isArray(profile.column_profile) ? profile.column_profile : [];
    const missing = columns.reduce((sum, column) => sum + Number(column.missing_count || 0), 0);
    const missingColumns = columns.filter((column) => Number(column.missing_count || 0) > 0).sort((a, b) => Number(b.missing_count || 0) - Number(a.missing_count || 0));
    const constant = columns.filter((column) => column.constant);
    const numeric = columns.filter((column) => /int|float|double|decimal|number/i.test(String(column.dtype)));
    const cards = [
      ["Dataset scale", `${formatNumber(profile.rows)} × ${formatNumber(profile.columns)}`, "Rows and columns measured from the full dataset."],
      ["Completeness", `${missing.toLocaleString()} missing cells`, missing ? `${missingColumns.length} column(s) contain missing values.` : "No missing cells detected by the profiler."],
      ["Duplicate rows", formatNumber(profile.duplicate_rows), profile.duplicate_rows ? "Duplicate rows require investigation before downstream analysis." : "No duplicate rows detected."],
      ["Schema shape", `${numeric.length} numeric columns`, `${columns.length - numeric.length} other typed columns in the profile.`],
    ];
    if (constant.length) cards.push(["Constant columns", formatNumber(constant.length), `${constant.map((column) => column.name).join(", ")} contain one observed value.`]);
    if (missingColumns[0]) cards.push(["Highest missingness", missingColumns[0].name, `${Number(missingColumns[0].missing_pct).toFixed(1)}% missing in this column.`]);
    target.innerHTML = cards.map(([title, value, detail]) => `<article class="insight-card"><strong>${escapeHtml(title)}</strong><div class="insight-value">${escapeHtml(value)}</div><p>${escapeHtml(detail)}</p></article>`).join("");
  }

  function renderCharts(profile) {
    const columns = Array.isArray(profile.column_profile) ? profile.column_profile : [];
    const missingChart = $("missingChart");
    const completenessChart = $("completenessChart");
    const ranked = [...columns].sort((a, b) => Number(b.missing_count || 0) - Number(a.missing_count || 0));
    const maxMissing = Math.max(1, ...ranked.map((column) => Number(column.missing_count || 0)));
    if (missingChart) {
      missingChart.innerHTML = ranked.map((column) => {
        const value = Number(column.missing_count || 0);
        return `<div class="chart-bar-row"><label title="${escapeHtml(column.name)}">${escapeHtml(column.name)}</label><div class="chart-bar-track"><div class="chart-bar-fill" style="width:${(value / maxMissing * 100).toFixed(2)}%"></div></div><span class="chart-bar-value">${formatNumber(value)}</span></div>`;
      }).join("") || `<div class="profile-placeholder"><strong>No profile data</strong></div>`;
    }
    if (completenessChart) {
      completenessChart.innerHTML = columns.map((column) => {
        const value = Math.max(0, 100 - Number(column.missing_pct || 0));
        return `<div class="chart-bar-row"><label title="${escapeHtml(column.name)}">${escapeHtml(column.name)}</label><div class="chart-bar-track"><div class="chart-bar-fill" style="width:${value.toFixed(2)}%"></div></div><span class="chart-bar-value">${value.toFixed(1)}%</span></div>`;
      }).join("") || `<div class="profile-placeholder"><strong>No profile data</strong></div>`;
    }
  }

  function escapeHtml(value) {
    const element = document.createElement("div");
    element.textContent = String(value ?? "");
    return element.innerHTML;
  }

  async function autoProfile() {
    if (!datasetPath || profileRequestedForPath === datasetPath) return;
    profileRequestedForPath = datasetPath;
    try {
      const response = await originalFetch("/api/profile", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ path: datasetPath }) });
      if (!response.ok) return;
      latestProfile = await response.json();
      renderDashboardMetrics(latestProfile);
      renderQuality(latestProfile);
      renderInsights(latestProfile);
      renderCharts(latestProfile);
      updateSidebarProfile(latestProfile);
    } catch {
      profileRequestedForPath = null;
    }
  }

  function wireGridTools() {
    search?.addEventListener("input", () => {
      const query = search.value.trim().toLowerCase();
      if (!tbody) return;
      Array.from(tbody.rows).forEach((row) => {
        row.hidden = Boolean(query) && !row.textContent.toLowerCase().includes(query);
      });
      updateGridRowCount();
    });

    $("gridFilter")?.addEventListener("click", () => {
      if (!tbody) return;
      const expression = window.prompt("Preview filter — use Column=Value", "");
      if (!expression) return;
      const [rawColumn, ...rawValue] = expression.split("=");
      const column = rawColumn?.trim().toLowerCase();
      const value = rawValue.join("=").trim().toLowerCase();
      const header = Array.from(table.querySelectorAll("thead th")).find((th) => th.querySelector(".grid-name")?.textContent.trim().toLowerCase() === column);
      const index = header ? Number(header.dataset.columnIndex) : -1;
      if (index < 0) return window.alert(`Column not found in the preview: ${rawColumn}`);
      Array.from(tbody.rows).forEach((row) => {
        const cell = row.querySelector(`.grid-cell[data-column-index="${index}"]`);
        row.hidden = !String(cell?.textContent || "").toLowerCase().includes(value);
      });
      $("gridFilter")?.classList.add("grid-filtering-active");
      updateGridRowCount();
    });

    $("gridSort")?.addEventListener("click", () => {
      if (!tbody) return;
      const headers = Array.from(table.querySelectorAll("thead th.grid-column-header"));
      const names = headers.map((header) => header.querySelector(".grid-name")?.textContent.trim()).filter(Boolean);
      const selected = window.prompt(`Sort preview by column:\n${names.join(", ")}`, names[0] || "");
      if (!selected) return;
      const index = headers.findIndex((header) => header.querySelector(".grid-name")?.textContent.trim().toLowerCase() === selected.trim().toLowerCase());
      if (index < 0) return window.alert(`Column not found in the preview: ${selected}`);
      sortDescending = !sortDescending;
      const rows = Array.from(tbody.rows);
      rows.sort((a, b) => {
        const av = a.querySelector(`.grid-cell[data-column-index="${index}"]`)?.textContent.trim() || "";
        const bv = b.querySelector(`.grid-cell[data-column-index="${index}"]`)?.textContent.trim() || "";
        const an = Number(av.replace(/,/g, ""));
        const bn = Number(bv.replace(/,/g, ""));
        const comparison = Number.isFinite(an) && Number.isFinite(bn) && av !== "" && bv !== "" ? an - bn : av.localeCompare(bv, undefined, { numeric: true, sensitivity: "base" });
        return sortDescending ? -comparison : comparison;
      });
      rows.forEach((row) => tbody.appendChild(row));
    });

    $("gridColumns")?.addEventListener("click", () => {
      const headers = Array.from(table.querySelectorAll("thead th.grid-column-header"));
      const names = headers.map((header) => header.querySelector(".grid-name")?.textContent.trim()).filter(Boolean);
      const raw = window.prompt(`Hide columns by name, comma separated.\nAvailable: ${names.join(", ")}`, "");
      if (raw === null) return;
      hiddenColumns = new Set(raw.split(",").map((value) => value.trim().toLowerCase()).filter(Boolean));
      applyColumnVisibility();
    });

    $("gridDensity")?.addEventListener("click", () => {
      const root = table.closest(".table-shell");
      const modes = ["", "grid-density-compact", "grid-density-comfortable"];
      const current = modes.findIndex((mode) => mode && root?.classList.contains(mode));
      const next = modes[(current + 1) % modes.length];
      modes.forEach((mode) => mode && root?.classList.remove(mode));
      if (next) root?.classList.add(next);
    });
  }

  function applyColumnVisibility() {
    const headers = Array.from(table.querySelectorAll("thead th.grid-column-header"));
    headers.forEach((header) => {
      const name = header.querySelector(".grid-name")?.textContent.trim().toLowerCase() || "";
      header.hidden = hiddenColumns.has(name);
    });
    tbody && Array.from(tbody.rows).forEach((row) => {
      Array.from(row.querySelectorAll(".grid-cell")).forEach((cell) => {
        const header = headers.find((candidate) => Number(candidate.dataset.columnIndex) === Number(cell.dataset.columnIndex));
        const name = header?.querySelector(".grid-name")?.textContent.trim().toLowerCase() || "";
        cell.hidden = hiddenColumns.has(name);
      });
    });
  }

  function updateGridRowCount() {
    if (!tbody) return;
    const visible = Array.from(tbody.rows).filter((row) => !row.hidden).length;
    const total = tbody.rows.length;
    $("gridRowCount") && ($("gridRowCount").textContent = `${visible} of ${total} preview rows`);
  }

  function observeGrid() {
    if (!tbody) return;
    const observer = new MutationObserver(() => {
      applyColumnVisibility();
      updateGridRowCount();
    });
    observer.observe(tbody, { childList: true });
    updateGridRowCount();
  }

  function observeSelection() {
    const selection = $("gridSelection");
    if (!selection) return;
    const observer = new MutationObserver(() => {
      const hasSelection = !/Click a cell/i.test(selection.textContent || "");
      $("gridSelectedCount") && ($("gridSelectedCount").textContent = hasSelection ? "1 cell selected" : "0 cells selected");
    });
    observer.observe(selection, { childList: true, characterData: true, subtree: true });
  }

  wireCommandSurface();
  wireNavigation();
  wireGridTools();
  observeGrid();
  observeSelection();
})();
