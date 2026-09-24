(() => {
  const nativeFetch = window.fetch.bind(window);
  let lastChatResult = null;

  const style = document.createElement("style");
  style.textContent = `
    .noor-intelligence-result { margin-top: 12px; padding: 12px; border: 1px solid rgba(96,165,250,.20); border-radius: 12px; background: rgba(8,15,31,.72); }
    .noor-intelligence-result h4 { margin: 0 0 8px; font-size: 13px; }
    .noor-intelligence-result p { margin: 6px 0; line-height: 1.5; }
    .noor-evidence { margin-top: 8px; overflow-x: auto; }
    .noor-evidence table { width: 100%; border-collapse: collapse; font-size: 12px; }
    .noor-evidence th, .noor-evidence td { padding: 6px 8px; border-bottom: 1px solid rgba(148,163,184,.12); text-align: left; white-space: nowrap; }
    .noor-formula { display: block; margin: 8px 0; padding: 9px 10px; border-radius: 8px; background: rgba(15,23,42,.9); color: #dbeafe; font-family: ui-monospace, SFMono-Regular, Consolas, monospace; overflow-x: auto; }
    .noor-question-list { margin: 6px 0 0 18px; padding: 0; }
    .noor-question-list li { margin: 5px 0; }
    .noor-meta { color: #94a3b8; font-size: 11px; }
    .noor-badge { display:inline-block; margin-left:6px; padding:2px 6px; border-radius:999px; background:rgba(34,197,94,.12); color:#86efac; font-size:10px; }
  `;
  document.head.appendChild(style);

  function escapeHtml(value) {
    const element = document.createElement("div");
    element.textContent = String(value ?? "");
    return element.innerHTML;
  }

  function formatValue(value) {
    if (value === null || value === undefined) return "—";
    if (typeof value === "number") return Number.isInteger(value) ? value.toLocaleString() : value.toLocaleString(undefined, { maximumFractionDigits: 4 });
    return String(value);
  }

  function tableHtml(rows, maxRows = 12) {
    if (!Array.isArray(rows) || !rows.length) return "<p class='noor-meta'>No tabular evidence was returned.</p>";
    const visible = rows.slice(0, maxRows);
    const columns = [...new Set(visible.flatMap(row => Object.keys(row || {})))];
    return `<div class='noor-evidence'><table><thead><tr>${columns.map(c => `<th>${escapeHtml(c)}</th>`).join("")}</tr></thead><tbody>${visible.map(row => `<tr>${columns.map(c => `<td>${escapeHtml(formatValue(row?.[c]))}</td>`).join("")}</tr>`).join("")}</tbody></table></div>${rows.length > maxRows ? `<div class='noor-meta'>Showing ${maxRows} of ${rows.length} returned rows.</div>` : ""}`;
  }

  function renderExecution(execution) {
    const output = execution?.output || {};
    const capability = execution?.capability || "";
    if (capability === "excel.intelligence.answer") {
      return `<h4>Answer <span class='noor-badge'>verified</span></h4><p>${escapeHtml(output.answer || "No answer returned.")}</p><div class='noor-meta'>Calculation: ${escapeHtml(output.calculation || "direct dataset calculation")}</div>${tableHtml(Array.isArray(output.evidence) ? output.evidence : [], 10)}`;
    }
    if (capability === "excel.intelligence.formula") {
      return `<h4>Recommended Excel formula</h4><p><strong>${escapeHtml(output.recommended_function || "Formula")}</strong></p><code class='noor-formula'>${escapeHtml(output.formula || "")}</code><p>${escapeHtml(output.reason || "")}</p><div class='noor-meta'>Excel ${escapeHtml(output.excel_version || "2021")} compatibility: ${output.compatible ? "supported" : "not supported"}.</div>`;
    }
    if (capability === "excel.intelligence.questions") {
      const questions = Array.isArray(output.questions) ? output.questions : [];
      return `<h4>Questions Noor generated from the dataset</h4><ol class='noor-question-list'>${questions.map(q => `<li>${escapeHtml(q)}</li>`).join("")}</ol>`;
    }
    if (capability === "excel.intelligence.pivot") {
      return `<h4>Pivot-style summary</h4><p>Grouped by <strong>${escapeHtml(output.row_field)}</strong>, using <strong>${escapeHtml(output.aggregation)}</strong> of <strong>${escapeHtml(output.value_field)}</strong>.</p>${tableHtml(output.rows, 20)}`;
    }
    if (capability === "excel.intelligence.profile") {
      const columns = Array.isArray(output.column_profile) ? output.column_profile : [];
      const missing = Number(output.missing_cells || 0);
      return `<h4>Deep dataset profile <span class='noor-badge'>computed</span></h4><p><strong>${formatValue(output.rows)}</strong> rows · <strong>${formatValue(output.columns)}</strong> columns · <strong>${formatValue(missing)}</strong> missing cells · <strong>${formatValue(output.duplicate_rows || 0)}</strong> duplicate rows.</p><div class='noor-evidence'><table><thead><tr><th>Column</th><th>Type</th><th>Missing</th><th>Unique</th></tr></thead><tbody>${columns.slice(0, 30).map(c => `<tr><td>${escapeHtml(c.name)}</td><td>${escapeHtml(c.dtype)}</td><td>${formatValue(c.missing)} (${formatValue(c.missing_pct)}%)</td><td>${formatValue(c.unique)}</td></tr>`).join("")}</tbody></table></div>`;
    }
    if (capability === "excel.intelligence.dashboard") {
      const kpis = Array.isArray(output.kpis) ? output.kpis : [];
      const charts = Array.isArray(output.charts) ? output.charts : [];
      return `<h4>Dashboard plan</h4><p>${formatValue(output.dataset_rows)} rows · ${formatValue(output.dataset_columns)} columns.</p><p><strong>KPIs:</strong> ${kpis.map(k => escapeHtml(k.name)).join(" · ") || "None detected"}</p><p><strong>Charts:</strong> ${charts.map(c => `${escapeHtml(c.type)} — ${escapeHtml(c.purpose)}`).join(" · ") || "None detected"}</p>`;
    }
    if (capability === "excel.intelligence.formulas") {
      const formulas = Array.isArray(output.formulas) ? output.formulas : [];
      return `<h4>Excel formula catalog</h4><p>${formatValue(formulas.length)} matching functions.</p>${tableHtml(formulas.map(f => ({ Formula: f.name, Category: f.category, Version: f.version, Use: f.use })), 25)}`;
    }
    return "";
  }

  function enrichLatestWorkflow() {
    if (!lastChatResult) return;
    const executions = Array.isArray(lastChatResult.executions) ? lastChatResult.executions : [];
    const intelligence = executions.filter(item => item?.capability?.startsWith("excel.intelligence.") && item.status === "success");
    if (!intelligence.length) return;
    const workflowMessages = document.querySelectorAll("#messages .workflow-message");
    const target = workflowMessages[workflowMessages.length - 1];
    if (!target || target.querySelector(".noor-intelligence-result")) return;
    const container = document.createElement("div");
    container.className = "noor-intelligence-result";
    container.innerHTML = intelligence.map(renderExecution).filter(Boolean).join("");
    if (container.innerHTML) {
      target.querySelector(".workflow-content")?.appendChild(container);
    }
  }

  window.fetch = async (...args) => {
    const response = await nativeFetch(...args);
    try {
      const url = typeof args[0] === "string" ? args[0] : args[0]?.url || "";
      if (url.includes("/api/chat")) {
        response.clone().json().then(payload => {
          lastChatResult = payload;
          window.__noorLastChat = payload;
          window.setTimeout(enrichLatestWorkflow, 0);
          window.setTimeout(enrichLatestWorkflow, 80);
          window.setTimeout(enrichLatestWorkflow, 250);
        }).catch(() => {});
      }
    } catch (_) {}
    return response;
  };

  const observer = new MutationObserver(() => enrichLatestWorkflow());
  const startObserver = () => {
    const messages = document.getElementById("messages");
    if (messages) observer.observe(messages, { childList: true, subtree: true });
    else window.setTimeout(startObserver, 100);
  };
  startObserver();
})();
