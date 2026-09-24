const orb = document.getElementById("noorOrb");
const panel = document.getElementById("chatPanel");
const closeChat = document.getElementById("closeChat");
const form = document.getElementById("chatForm");
const input = document.getElementById("messageInput");
const messages = document.getElementById("messages");
const suggestions = document.getElementById("suggestions");
const datasetFile = document.getElementById("datasetFile");
const fileName = document.getElementById("fileName");
const statusText = document.getElementById("statusText");
const datasetEmpty = document.getElementById("datasetEmpty");
const emptyAttach = document.getElementById("emptyAttach");
const datasetView = document.getElementById("datasetView");
const datasetTitle = document.getElementById("datasetTitle");
const datasetMeta = document.getElementById("datasetMeta");
const workspaceTitle = document.getElementById("workspaceTitle");
const workspaceSubtitle = document.getElementById("workspaceSubtitle");
const workspaceState = document.getElementById("workspaceState");
const statFormat = document.getElementById("statFormat");
const statRows = document.getElementById("statRows");
const statColumns = document.getElementById("statColumns");
const statMissing = document.getElementById("statMissing");
const statMissingHint = document.getElementById("statMissingHint");
const statDuplicates = document.getElementById("statDuplicates");
const statDuplicatesHint = document.getElementById("statDuplicatesHint");
const statSize = document.getElementById("statSize");
const previewCaption = document.getElementById("previewCaption");
const tableSchemaSummary = document.getElementById("tableSchemaSummary");
const dataTable = document.getElementById("dataTable");
const columnsTable = document.getElementById("columnsTable");
const profileSummary = document.getElementById("profileSummary");
const columnProfile = document.getElementById("columnProfile");
const qualityGrid = document.getElementById("qualityGrid");
const activityList = document.getElementById("activityList");
const refreshPreview = document.getElementById("refreshPreview");
const runProfile = document.getElementById("runProfile");
const profileFromView = document.getElementById("profileFromView");

let selectedDataPath = null;
let selectedFileExtension = null;
let latestPreview = null;
let latestProfile = null;
let activity = [];

const DATASET_REQUEST_PATTERNS = [
  /\b(inspect|profile|profiling|analy[sz]e|analysis|clean|cleaning|transform|duplicate|fill\s+blank|read|load|show)\b/i,
  /\b(search|find|lookup)\b.*\b(workbook|sheet|dataset|data)\b/i,
  /\b(create|rename|freeze|filter|sort)\b.*\b(sheet|worksheet|workbook)\b/i,
];

function openChat() {
  panel.classList.add("is-open");
  panel.setAttribute("aria-hidden", "false");
  orb.classList.add("is-hidden");
  orb.setAttribute("aria-expanded", "true");
  window.setTimeout(() => input.focus(), 180);
}

function closePanel() {
  panel.classList.remove("is-open");
  panel.setAttribute("aria-hidden", "true");
  orb.classList.remove("is-hidden");
  orb.setAttribute("aria-expanded", "false");
  orb.focus();
}

function escapeHtml(value) {
  const element = document.createElement("div");
  element.textContent = String(value ?? "");
  return element.innerHTML;
}

function appendMessage(text, role = "assistant") {
  const article = document.createElement("article");
  article.className = `message ${role === "user" ? "user-message" : "assistant-message"}`;
  if (role === "user") article.innerHTML = `<div class="message-content"><p>${escapeHtml(text)}</p></div>`;
  else article.innerHTML = `<div class="message-avatar">N</div><div class="message-content"><span class="message-role">Noor</span><p>${escapeHtml(text)}</p></div>`;
  messages.appendChild(article);
  messages.scrollTop = messages.scrollHeight;
}

function appendWorkflow(result) {
  const article = document.createElement("article");
  article.className = "message assistant-message workflow-message";
  const plan = (result.plan || []).map((node) => `<li><strong>${escapeHtml(node.id)}</strong><span>${escapeHtml(node.provider)}</span></li>`).join("");
  const executions = (result.executions || []).map((item) => {
    const state = item.status === "success" ? "success" : "failed";
    const detail = item.status === "success" ? `${item.attempts} attempt${item.attempts === 1 ? "" : "s"}` : escapeHtml((item.errors || []).join("; "));
    return `<li class="execution-${state}"><strong>${escapeHtml(item.capability)}</strong><span>${escapeHtml(item.status)} · ${detail}</span></li>`;
  }).join("");
  article.innerHTML = `<div class="message-avatar">N</div><div class="message-content workflow-content"><span class="message-role">Noor · Orchestra</span><p>${result.success ? "Workflow completed successfully." : "Workflow stopped at a failed step."}</p><details open><summary>Task graph</summary><ol class="workflow-list">${plan}</ol></details><details><summary>Execution & verification</summary><ol class="workflow-list">${executions}</ol></details><p class="next-step"><strong>Next:</strong> ${escapeHtml(result.next_step)}</p></div>`;
  messages.appendChild(article);
  messages.scrollTop = messages.scrollHeight;
}

function resizeInput() {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 110)}px`;
}

function requiresDataset(text) {
  const normalized = text.trim();
  if (!normalized) return false;
  if (/\b(validate|check|explain)\s+(?:this\s+)?formula\b/i.test(normalized)) return false;
  return DATASET_REQUEST_PATTERNS.some((pattern) => pattern.test(normalized));
}

function updateDatasetActions() {
  document.querySelectorAll("button[data-requires-dataset='true']").forEach((button) => {
    button.disabled = !selectedDataPath;
    button.setAttribute("aria-disabled", String(!selectedDataPath));
    button.title = selectedDataPath ? "Run this action" : "Attach a dataset first";
  });
}

function formatBytes(bytes) {
  if (!Number.isFinite(bytes) || bytes < 1024) return `${bytes || 0} B`;
  const units = ["KB", "MB", "GB"];
  let value = bytes;
  let unit = -1;
  do { value /= 1024; unit += 1; } while (value >= 1024 && unit < units.length - 1);
  return `${value.toFixed(value >= 10 ? 0 : 1)} ${units[unit]}`;
}

function setWorkspaceState(label, active = false) {
  workspaceState.innerHTML = `<span class="status-dot${active ? " workspace-active" : ""}"></span><span>${escapeHtml(label)}</span>`;
}

function clearTable() {
  dataTable.querySelector("thead").replaceChildren();
  dataTable.querySelector("tbody").replaceChildren();
}

function renderDatasetPreview(preview) {
  latestPreview = preview;
  datasetEmpty.classList.add("is-hidden");
  datasetView.classList.remove("is-hidden");
  workspaceTitle.textContent = preview.filename;
  workspaceSubtitle.textContent = `${preview.format} dataset loaded. Use Noor's chat as the control surface; the workspace shows the actual data and verified analytical results.`;
  datasetTitle.textContent = preview.filename;
  datasetMeta.textContent = `${preview.format} · ${preview.extension} · ${formatBytes(preview.bytes)}`;
  statFormat.textContent = preview.format;
  statRows.textContent = `${preview.rows_returned} preview`;
  statRowsHint.textContent = "bounded rows shown";
  statColumns.textContent = String(preview.columns.length);
  statColumnsHint.textContent = "loaded schema";
  statSize.textContent = formatBytes(preview.bytes);
  previewCaption.textContent = `First ${preview.rows_returned} row${preview.rows_returned === 1 ? "" : "s"}`;
  tableSchemaSummary.textContent = `${preview.columns.length} columns · types detected from the loaded data`;
  setWorkspaceState("Dataset ready", true);

  clearTable();
  const head = dataTable.querySelector("thead");
  const body = dataTable.querySelector("tbody");
  const headerRow = document.createElement("tr");
  preview.columns.forEach((column) => {
    const cell = document.createElement("th");
    cell.textContent = column;
    cell.title = preview.dtypes?.[column] || "unknown";
    headerRow.appendChild(cell);
  });
  head.appendChild(headerRow);

  preview.records.forEach((record) => {
    const row = document.createElement("tr");
    preview.columns.forEach((column) => {
      const cell = document.createElement("td");
      const value = record[column];
      cell.textContent = value === null || value === undefined ? "NULL" : String(value);
      if (value === null || value === undefined) cell.classList.add("null-value");
      row.appendChild(cell);
    });
    body.appendChild(row);
  });
  renderColumnsFromPreview(preview);
}

function renderColumnsFromPreview(preview) {
  columnsTable.replaceChildren();
  preview.columns.forEach((column) => {
    const row = document.createElement("tr");
    const values = preview.records.map((record) => record[column]).filter((value) => value !== null && value !== undefined && value !== "");
    const unique = new Set(values.map((value) => JSON.stringify(value))).size;
    row.innerHTML = `<td><strong>${escapeHtml(column)}</strong></td><td>${escapeHtml(preview.dtypes?.[column] || "unknown")}</td><td>${unique} in preview</td><td>Profile needed</td>`;
    columnsTable.appendChild(row);
  });
}

function renderProfile(profile) {
  if (!profile) return;
  latestProfile = profile;
  const columns = profile.column_profile || [];
  const totalMissing = columns.reduce((sum, column) => sum + Number(column.missing_count || 0), 0);
  statRows.textContent = Number(profile.rows).toLocaleString();
  statRowsHint.textContent = "full dataset";
  statColumns.textContent = Number(profile.columns).toLocaleString();
  statMissing.textContent = totalMissing.toLocaleString();
  statMissingHint.textContent = totalMissing ? "missing cells" : "no missing cells detected";
  statDuplicates.textContent = Number(profile.duplicate_rows || 0).toLocaleString();
  statDuplicatesHint.textContent = profile.duplicate_rows ? "duplicate rows" : "no duplicate rows detected";

  profileSummary.innerHTML = [
    ["Rows", Number(profile.rows).toLocaleString(), "full dataset"],
    ["Columns", Number(profile.columns).toLocaleString(), "schema fields"],
    ["Missing cells", totalMissing.toLocaleString(), totalMissing ? "requires review" : "none detected"],
    ["Duplicate rows", Number(profile.duplicate_rows || 0).toLocaleString(), profile.duplicate_rows ? "requires review" : "none detected"],
  ].map(([label, value, hint]) => `<article class="profile-card"><span>${label}</span><strong>${value}</strong><small>${hint}</small></article>`).join("");

  columnProfile.innerHTML = columns.map((column) => `<div class="column-row"><strong title="${escapeHtml(column.name)}">${escapeHtml(column.name)}</strong><span>${escapeHtml(column.dtype)}</span><span>${Number(column.unique_count).toLocaleString()} unique</span><span>${Number(column.missing_pct).toFixed(1)}% missing</span></div>`).join("");

  qualityGrid.innerHTML = "";
  const constantColumns = columns.filter((column) => column.constant);
  const missingColumns = columns.filter((column) => column.missing_count > 0).sort((a, b) => b.missing_count - a.missing_count);
  const qualityItems = [
    ["Missing values", totalMissing ? "Review" : "Clear", totalMissing ? `${missingColumns.length} column(s) contain missing values` : "No missing cells detected", Boolean(totalMissing)],
    ["Duplicate rows", Number(profile.duplicate_rows || 0) ? "Review" : "Clear", Number(profile.duplicate_rows || 0) ? `${Number(profile.duplicate_rows).toLocaleString()} duplicate row(s)` : "No duplicate rows detected", Boolean(profile.duplicate_rows)],
    ["Constant columns", constantColumns.length ? "Review" : "Clear", constantColumns.length ? `${constantColumns.length} column(s) have one value` : "No constant columns detected", Boolean(constantColumns.length)],
    ["Schema", "Ready", `${Number(profile.columns)} columns profiled`, false],
  ];
  qualityItems.forEach(([label, value, detail, issue]) => {
    const card = document.createElement("article");
    card.className = `quality-card ${issue ? "issue" : "clean"}`;
    card.innerHTML = `<span>${label}</span><strong>${value}</strong><small>${escapeHtml(detail)}</small>`;
    qualityGrid.appendChild(card);
  });

  columnsTable.replaceChildren();
  columns.forEach((column) => {
    const row = document.createElement("tr");
    row.innerHTML = `<td><strong>${escapeHtml(column.name)}</strong></td><td>${escapeHtml(column.dtype)}</td><td>${Number(column.unique_count).toLocaleString()}</td><td>${Number(column.missing_count).toLocaleString()} (${Number(column.missing_pct).toFixed(1)}%)</td>`;
    columnsTable.appendChild(row);
  });
}

async function refreshDatasetPreview() {
  if (!selectedDataPath) return;
  const response = await fetch("/api/preview", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ path: selectedDataPath }) });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || "Could not preview the dataset");
  renderDatasetPreview(payload);
}

async function profileDataset() {
  if (!selectedDataPath) throw new Error("Attach a dataset first");
  setWorkspaceState("Profiling dataset");
  const response = await fetch("/api/profile", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ path: selectedDataPath }) });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || "Could not profile the dataset");
  renderProfile(payload);
  activateView("profile");
  setWorkspaceState("Profile complete", true);
  return payload;
}

async function checkHealth() {
  try {
    const response = await fetch("/api/health", { cache: "no-store" });
    if (!response.ok) throw new Error("Health check failed");
    const payload = await response.json();
    statusText.textContent = `Ready · ${payload.upload_formats}+ formats`;
  } catch {
    statusText.textContent = "Start Noor server";
  }
}

async function uploadDataset(file) {
  const body = new FormData();
  body.append("file", file);
  statusText.textContent = "Uploading";
  setWorkspaceState("Uploading dataset");
  const response = await fetch("/api/upload", { method: "POST", body });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || "Upload failed");
  selectedDataPath = payload.upload.path;
  selectedFileExtension = file.name.includes(".") ? file.name.split(".").pop().toLowerCase() : "data";
  fileName.textContent = `${payload.upload.filename} · .${selectedFileExtension}`;
  statusText.textContent = "Loading preview";
  await refreshDatasetPreview();
  statusText.textContent = "Dataset ready";
  updateDatasetActions();
}

async function executeRequest(text) {
  const response = await fetch("/api/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message: text, path: selectedDataPath }) });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || "Noor could not execute the request");
  return payload;
}

function activateView(viewName) {
  document.querySelectorAll(".workspace-tab").forEach((tab) => tab.classList.toggle("is-active", tab.dataset.view === viewName));
  document.querySelectorAll(".workspace-view").forEach((view) => view.classList.toggle("is-active", view.dataset.viewPanel === viewName));
}

function requestedView(text) {
  const normalized = text.toLowerCase();
  if (/\b(profile|profiling)\b/.test(normalized)) return "profile";
  if (/\b(quality|missing|duplicate|clean|cleaning)\b/.test(normalized)) return "quality";
  if (/\b(column|schema|field|dtype)\b/.test(normalized)) return "columns";
  if (/\b(activity|workflow|what did you do)\b/.test(normalized)) return "activity";
  return "data";
}

function recordActivity(request, result) {
  activity.unshift({ request, success: result.success, next: result.next_step, capabilities: (result.executions || []).map((item) => item.capability) });
  activity = activity.slice(0, 12);
  activityList.innerHTML = activity.map((item) => `<article class="activity-item"><header><strong>${escapeHtml(item.request)}</strong><time>${item.success ? "Completed" : "Attention required"}</time></header><p>${escapeHtml(item.capabilities.join(" → "))}</p><span class="activity-status">${escapeHtml(item.next)}</span></article>`).join("");
}

function applyWorkflowResult(result, request) {
  const profileExecution = (result.executions || []).find((item) => item.capability === "data.profile" && item.status === "success");
  if (profileExecution?.output) renderProfile(profileExecution.output);
  recordActivity(request, result);
  activateView(requestedView(request));
}

orb.addEventListener("click", openChat);
closeChat.addEventListener("click", closePanel);
emptyAttach.addEventListener("click", () => { openChat(); datasetFile.click(); });

refreshPreview.addEventListener("click", async () => {
  if (!selectedDataPath) return;
  try { statusText.textContent = "Refreshing"; await refreshDatasetPreview(); statusText.textContent = "Dataset ready"; }
  catch (error) { statusText.textContent = "Error"; appendMessage(error.message || "Could not refresh the dataset preview."); }
});

runProfile.addEventListener("click", async () => {
  try { statusText.textContent = "Profiling"; await profileDataset(); statusText.textContent = "Completed"; }
  catch (error) { statusText.textContent = "Error"; setWorkspaceState("Attention required"); appendMessage(error.message || "Could not profile the dataset."); }
});
profileFromView.addEventListener("click", () => runProfile.click());

document.querySelectorAll(".workspace-tab").forEach((tab) => tab.addEventListener("click", () => activateView(tab.dataset.view)));

datasetFile.addEventListener("change", async () => {
  const file = datasetFile.files?.[0];
  if (!file) return;
  try { await uploadDataset(file); appendMessage(`Attached ${file.name}. The live dataset is now available on the workspace.`); }
  catch (error) { statusText.textContent = "Ready"; setWorkspaceState("Preview unavailable"); appendMessage(error.message || "Dataset upload failed."); }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  appendMessage(text, "user");
  input.value = "";
  resizeInput();

  if (requiresDataset(text) && !selectedDataPath) {
    statusText.textContent = "Ready";
    appendMessage("Please attach a dataset first. Once attached, I can inspect, profile, analyze, clean, transform, or automate it.");
    openChat();
    datasetFile.click();
    return;
  }

  statusText.textContent = "Planning";
  setWorkspaceState("Noor is working");
  const typing = document.createElement("article");
  typing.className = "message assistant-message";
  typing.innerHTML = `<div class="message-avatar">N</div><div class="message-content"><span class="message-role">Noor</span><p class="typing">Building the task graph and selecting providers…</p></div>`;
  messages.appendChild(typing);
  messages.scrollTop = messages.scrollHeight;

  try {
    const result = await executeRequest(text);
    typing.remove();
    statusText.textContent = result.success ? "Completed" : "Attention required";
    setWorkspaceState(result.success ? "Workflow completed" : "Attention required", result.success);
    appendWorkflow(result);
    applyWorkflowResult(result, text);
    if (result.success && selectedDataPath) {
      try { await refreshDatasetPreview(); } catch { /* keep verified workflow result visible */ }
    }
  } catch (error) {
    typing.remove();
    const message = error.message || "Noor could not complete the request.";
    statusText.textContent = "Error";
    setWorkspaceState("Attention required");
    appendMessage(message);
  }
});

input.addEventListener("input", resizeInput);
input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); form.requestSubmit(); }
});

suggestions.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-prompt]");
  if (!button || button.disabled) return;
  input.value = button.dataset.prompt;
  resizeInput();
  form.requestSubmit();
});

document.addEventListener("keydown", (event) => { if (event.key === "Escape" && panel.classList.contains("is-open")) closePanel(); });

updateDatasetActions();
checkHealth();
