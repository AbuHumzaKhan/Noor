(() => {
  const nativeFetch = window.fetch.bind(window);
  let lastChatResult = null;

  const style = document.createElement("style");
  style.textContent = `
    .noor-intelligence-result { margin-top: 12px; padding: 12px; border: 1px solid rgba(96,165,250,.20); border-radius: 12px; background: rgba(8,15,31,.72); position: relative; }
    .noor-intelligence-result h4 { margin: 0 0 8px; font-size: 13px; padding-right: 92px; }
    .noor-intelligence-result p { margin: 6px 0; line-height: 1.5; }
    .noor-intelligence-toolbar { position: absolute; top: 8px; right: 8px; display: inline-flex; align-items: center; gap: 3px; padding: 3px; border: 1px solid rgba(148,163,184,.16); border-radius: 9px; background: rgba(2,6,23,.78); backdrop-filter: blur(8px); }
    .noor-intelligence-control { width: 27px; height: 27px; display: inline-flex; align-items: center; justify-content: center; border: 0; border-radius: 6px; background: transparent; color: #94a3b8; cursor: pointer; padding: 0; transition: background .16s ease, color .16s ease, transform .16s ease; }
    .noor-intelligence-control:hover { background: rgba(59,130,246,.14); color: #dbeafe; }
    .noor-intelligence-control:active { transform: scale(.94); }
    .noor-intelligence-control:focus-visible { outline: 1px solid rgba(96,165,250,.8); outline-offset: 1px; }
    .noor-intelligence-control.is-danger:hover { background: rgba(239,68,68,.14); color: #fecaca; }
    .noor-intelligence-control svg { width: 15px; height: 15px; pointer-events: none; }
    .noor-intelligence-body { transition: opacity .16s ease; }
    .noor-intelligence-result.is-minimized { padding-bottom: 10px; }
    .noor-intelligence-result.is-minimized .noor-intelligence-body { display: none; }
    .noor-intelligence-result.is-minimized h4 { margin-bottom: 0; }
    .noor-intelligence-result.is-closing { opacity: 0; transform: translateY(-3px); transition: opacity .14s ease, transform .14s ease; }
    .noor-intelligence-copy-status { position: absolute; right: 8px; bottom: 8px; padding: 4px 7px; border-radius: 6px; background: rgba(34,197,94,.12); color: #86efac; font-size: 10px; pointer-events: none; opacity: 0; transform: translateY(3px); transition: opacity .16s ease, transform .16s ease; }
    .noor-intelligence-copy-status.is-visible { opacity: 1; transform: translateY(0); }
    .noor-evidence { margin-top: 8px; overflow-x: auto; }
    .noor-evidence table { width: 100%; border-collapse: collapse; font-size: 12px; }
    .noor-evidence th, .noor-evidence td { padding: 6px 8px; border-bottom: 1px solid rgba(148,163,184,.12); text-align: left; white-space: nowrap; }
    .noor-formula { display: block; margin: 8px 0; padding: 9px 10px; border-radius: 8px; background: rgba(15,23,42,.9); color: #dbeafe; font-family: ui-monospace, SFMono-Regular, Consolas, monospace; overflow-x: auto; }
    .noor-question-list { margin: 6px 0 0 18px; padding: 0; }
    .noor-question-list li { margin: 5px 0; }
    .noor-meta { color: #94a3b8; font-size: 11px; }
    .noor-badge { display:inline-block; margin-left:6px; padding:2px 6px; border-radius:999px; background:rgba(34,197,94,.12); color:#86efac; font-size:10px; }
    .noor-finding { margin: 5px 0; padding: 7px 9px; border-radius: 8px; background: rgba(15,23,42,.6); }
    .noor-capability-list { margin: 8px 0 0 18px; padding: 0; }
    .noor-capability-list li { margin: 5px 0; }
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

  function windowControls() {
    return `<div class="noor-intelligence-toolbar" role="toolbar" aria-label="Result controls">
      <button class="noor-intelligence-control" type="button" data-intelligence-action="copy" title="Copy result" aria-label="Copy result">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><rect x="8" y="8" width="11" height="11" rx="2"></rect><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"></path></svg>
      </button>
      <button class="noor-intelligence-control" type="button" data-intelligence-action="minimize" title="Minimize result" aria-label="Minimize result" aria-expanded="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M5 12h14"></path></svg>
      </button>
      <button class="noor-intelligence-control is-danger" type="button" data-intelligence-action="close" title="Close result" aria-label="Close result">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"></path></svg>
      </button>
    </div>`;
  }

  function renderExecution(execution) {
    const output = execution?.output || {};
    const capability = execution?.capability || "";
    if (capability === "excel.intelligence.full_analysis") {
      const profile = output.profile || {};
      const findings = Array.isArray(output.findings) ? output.findings : [];
      const questions = Array.isArray(output.questions) ? output.questions : [];
      const dashboard = output.dashboard || {};
      const formulas = Array.isArray(output.formula_guidance) ? output.formula_guidance : [];
      return `<h4>Complete Excel analysis <span class='noor-badge'>computed</span></h4><div class='noor-intelligence-body'><p><strong>${formatValue(profile.rows)}</strong> rows · <strong>${formatValue(profile.columns)}</strong> columns · <strong>${formatValue(profile.missing_cells)}</strong> missing cells · <strong>${formatValue(profile.duplicate_rows || 0)}</strong> duplicate rows.</p><p><strong>Findings</strong></p>${findings.map(f => `<div class='noor-finding'><strong>${escapeHtml(f.type)}:</strong> ${escapeHtml(f.message)}</div>`).join("")}<p><strong>Suggested questions</strong></p><ol class='noor-question-list'>${questions.slice(0, 8).map(q => `<li>${escapeHtml(q)}</li>`).join("")}</ol><p><strong>Dashboard structure</strong></p><p>KPIs: ${dashboard.kpis?.map(k => escapeHtml(k.name)).join(" · ") || "None detected"}</p><p>Charts: ${dashboard.charts?.map(c => `${escapeHtml(c.type)} — ${escapeHtml(c.purpose)}`).join(" · ") || "None detected"}</p><p><strong>Formula guidance</strong></p>${formulas.slice(0, 6).map(f => `<div class='noor-finding'><strong>${escapeHtml(f.recommended_function)}</strong> <code>${escapeHtml(f.formula)}</code><br><span class='noor-meta'>${escapeHtml(f.reason)}</span></div>`).join("")}<div class='noor-meta'>${escapeHtml(output.verified_basis || "Computed from the attached dataset.")}</div></div>`;
    }
    if (capability === "excel.intelligence.answer") {
      const capabilityList = Array.isArray(output.capabilities) ? output.capabilities : [];
      const commands = Array.isArray(output.suggested_commands) ? output.suggested_commands : [];
      if (capabilityList.length) {
        return `<h4>What you can do with this dataset <span class='noor-badge'>available</span></h4><div class='noor-intelligence-body'><p>${escapeHtml(output.answer || "")}</p><ul class='noor-capability-list'>${capabilityList.map(item => `<li>${escapeHtml(item)}</li>`).join("")}</ul><p><strong>Try asking:</strong></p><ol class='noor-question-list'>${commands.map(item => `<li>${escapeHtml(item)}</li>`).join("")}</ol><div class='noor-meta'>${escapeHtml(output.basis || "Computed from the attached dataset and registered Noor capabilities.")}</div></div>`;
      }
      return `<h4>Answer <span class='noor-badge'>verified</span></h4><div class='noor-intelligence-body'><p>${escapeHtml(output.answer || "No answer returned.")}</p><div class='noor-meta'>Calculation: ${escapeHtml(output.calculation || "direct dataset calculation")}</div>${tableHtml(Array.isArray(output.evidence) ? output.evidence : [], 10)}</div>`;
    }
    if (capability === "excel.intelligence.formula") {
      return `<h4>Recommended Excel formula</h4><div class='noor-intelligence-body'><p><strong>${escapeHtml(output.recommended_function || "Formula")}</strong></p><code class='noor-formula'>${escapeHtml(output.formula || "")}</code><p>${escapeHtml(output.reason || "")}</p><div class='noor-meta'>Excel ${escapeHtml(output.excel_version || "2021")} compatibility: ${output.compatible ? "supported" : "not supported"}.</div></div>`;
    }
    if (capability === "excel.intelligence.questions") {
      const questions = Array.isArray(output.questions) ? output.questions : [];
      return `<h4>Questions Noor generated from the dataset</h4><div class='noor-intelligence-body'><ol class='noor-question-list'>${questions.map(q => `<li>${escapeHtml(q)}</li>`).join("")}</ol></div>`;
    }
    if (capability === "excel.intelligence.pivot") {
      return `<h4>Pivot-style summary</h4><div class='noor-intelligence-body'><p>Grouped by <strong>${escapeHtml(output.row_field)}</strong>, using <strong>${escapeHtml(output.aggregation)}</strong> of <strong>${escapeHtml(output.value_field)}</strong>.</p>${tableHtml(output.rows, 20)}</div>`;
    }
    if (capability === "excel.intelligence.profile") {
      const columns = Array.isArray(output.column_profile) ? output.column_profile : [];
      return `<h4>Deep dataset profile <span class='noor-badge'>computed</span></h4><div class='noor-intelligence-body'><p><strong>${formatValue(output.rows)}</strong> rows · <strong>${formatValue(output.columns)}</strong> columns · <strong>${formatValue(output.missing_cells)}</strong> missing cells · <strong>${formatValue(output.duplicate_rows || 0)}</strong> duplicate rows.</p><div class='noor-evidence'><table><thead><tr><th>Column</th><th>Type</th><th>Missing</th><th>Unique</th></tr></thead><tbody>${columns.slice(0, 30).map(c => `<tr><td>${escapeHtml(c.name)}</td><td>${escapeHtml(c.dtype)}</td><td>${formatValue(c.missing)} (${formatValue(c.missing_pct)}%)</td><td>${formatValue(c.unique)}</td></tr>`).join("")}</tbody></table></div></div>`;
    }
    if (capability === "excel.intelligence.dashboard") {
      const kpis = Array.isArray(output.kpis) ? output.kpis : [];
      const charts = Array.isArray(output.charts) ? output.charts : [];
      return `<h4>Dashboard plan</h4><div class='noor-intelligence-body'><p>${formatValue(output.dataset_rows)} rows · ${formatValue(output.dataset_columns)} columns.</p><p><strong>KPIs:</strong> ${kpis.map(k => escapeHtml(k.name)).join(" · ") || "None detected"}</p><p><strong>Charts:</strong> ${charts.map(c => `${escapeHtml(c.type)} — ${escapeHtml(c.purpose)}`).join(" · ") || "None detected"}</p></div>`;
    }
    if (capability === "excel.intelligence.formulas") {
      const formulas = Array.isArray(output.formulas) ? output.formulas : [];
      return `<h4>Excel formula catalog</h4><div class='noor-intelligence-body'><p>${formatValue(formulas.length)} matching functions.</p>${tableHtml(formulas.map(f => ({ Formula: f.name, Category: f.category, Version: f.version, Use: f.use })), 25)}</div>`;
    }
    return "";
  }

  function intelligenceText(container) {
    const clone = container.cloneNode(true);
    clone.querySelector(".noor-intelligence-toolbar")?.remove();
    clone.querySelector(".noor-intelligence-copy-status")?.remove();
    return clone.innerText.trim();
  }

  async function copyIntelligenceResult(container, button) {
    const text = intelligenceText(container);
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
    } catch (_) {
      const textarea = document.createElement("textarea");
      textarea.value = text;
      textarea.setAttribute("readonly", "");
      textarea.style.position = "fixed";
      textarea.style.opacity = "0";
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      textarea.remove();
    }
    const status = container.querySelector(".noor-intelligence-copy-status") || document.createElement("span");
    status.className = "noor-intelligence-copy-status";
    status.textContent = "Copied";
    if (!status.parentElement) container.appendChild(status);
    status.classList.add("is-visible");
    button.setAttribute("aria-label", "Result copied");
    window.setTimeout(() => {
      status.classList.remove("is-visible");
      button.setAttribute("aria-label", "Copy result");
    }, 1200);
  }

  function handleIntelligenceAction(event) {
    const button = event.target.closest("[data-intelligence-action]");
    if (!button) return;
    const container = button.closest(".noor-intelligence-result");
    if (!container) return;
    event.preventDefault();
    event.stopPropagation();

    const action = button.dataset.intelligenceAction;
    if (action === "copy") {
      copyIntelligenceResult(container, button);
      return;
    }
    if (action === "minimize") {
      const minimized = container.classList.toggle("is-minimized");
      button.setAttribute("aria-expanded", String(!minimized));
      button.title = minimized ? "Expand result" : "Minimize result";
      button.setAttribute("aria-label", minimized ? "Expand result" : "Minimize result");
      return;
    }
    if (action === "close") {
      container.classList.add("is-closing");
      window.setTimeout(() => container.remove(), 150);
    }
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
    container.innerHTML = `${windowControls()}<div class="noor-intelligence-content">${intelligence.map(renderExecution).filter(Boolean).join("")}</div>`;
    const copyStatus = document.createElement("span");
    copyStatus.className = "noor-intelligence-copy-status";
    copyStatus.setAttribute("aria-live", "polite");
    container.appendChild(copyStatus);
    if (container.querySelector(".noor-intelligence-content")?.innerHTML) target.querySelector(".workflow-content")?.appendChild(container);
  }

  document.addEventListener("click", handleIntelligenceAction);

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