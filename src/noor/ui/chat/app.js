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

let selectedDataPath = null;
let selectedFileExtension = null;

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

function appendMessage(text, role = "assistant") {
  const article = document.createElement("article");
  article.className = `message ${role === "user" ? "user-message" : "assistant-message"}`;
  if (role === "user") {
    article.innerHTML = `<div class="message-content"><p>${escapeHtml(text)}</p></div>`;
  } else {
    article.innerHTML = `<div class="message-avatar">N</div><div class="message-content"><span class="message-role">Noor</span><p>${escapeHtml(text)}</p></div>`;
  }
  messages.appendChild(article);
  messages.scrollTop = messages.scrollHeight;
}

function appendWorkflow(result) {
  const article = document.createElement("article");
  article.className = "message assistant-message workflow-message";
  const plan = result.plan.map((node) => `<li><strong>${escapeHtml(node.id)}</strong><span>${escapeHtml(node.provider)}</span></li>`).join("");
  const executions = result.executions.map((item) => {
    const state = item.status === "success" ? "success" : "failed";
    const detail = item.status === "success" ? `${item.attempts} attempt${item.attempts === 1 ? "" : "s"}` : escapeHtml(item.errors.join("; "));
    return `<li class="execution-${state}"><strong>${escapeHtml(item.capability)}</strong><span>${escapeHtml(item.status)} · ${detail}</span></li>`;
  }).join("");
  article.innerHTML = `<div class="message-avatar">N</div><div class="message-content workflow-content"><span class="message-role">Noor · Orchestra</span><p>${result.success ? "Workflow completed successfully." : "Workflow stopped at a failed step."}</p><details open><summary>Task graph</summary><ol class="workflow-list">${plan}</ol></details><details><summary>Execution & verification</summary><ol class="workflow-list">${executions}</ol></details><p class="next-step"><strong>Next:</strong> ${escapeHtml(result.next_step)}</p></div>`;
  messages.appendChild(article);
  messages.scrollTop = messages.scrollHeight;
}

function escapeHtml(value) {
  const element = document.createElement("div");
  element.textContent = String(value ?? "");
  return element.innerHTML;
}

function resizeInput() {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 110)}px`;
}

async function checkHealth() {
  try {
    const response = await fetch("/api/health", { cache: "no-store" });
    if (!response.ok) throw new Error("Health check failed");
    const payload = await response.json();
    statusText.textContent = `Connected · ${payload.upload_formats}+ formats`;
  } catch {
    statusText.textContent = "Start Noor server";
  }
}

async function uploadDataset(file) {
  const body = new FormData();
  body.append("file", file);
  statusText.textContent = "Uploading";
  const response = await fetch("/api/upload", { method: "POST", body });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || "Upload failed");
  selectedDataPath = payload.upload.path;
  selectedFileExtension = file.name.includes(".") ? file.name.split(".").pop().toLowerCase() : "data";
  fileName.textContent = `${payload.upload.filename} · .${selectedFileExtension}`;
  statusText.textContent = "Connected";
}

async function executeRequest(text) {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: text, path: selectedDataPath }),
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || "Noor could not execute the request");
  return payload;
}

orb.addEventListener("click", openChat);
closeChat.addEventListener("click", closePanel);

datasetFile.addEventListener("change", async () => {
  const file = datasetFile.files?.[0];
  if (!file) return;
  try {
    await uploadDataset(file);
    appendMessage(`Attached ${file.name}. I can now inspect, profile, analyze, and route this dataset to the appropriate V1 skill.`);
  } catch (error) {
    statusText.textContent = "Error";
    appendMessage(error.message || "Dataset upload failed.");
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  appendMessage(text, "user");
  input.value = "";
  resizeInput();
  statusText.textContent = "Planning";

  const typing = document.createElement("article");
  typing.className = "message assistant-message";
  typing.innerHTML = `<div class="message-avatar">N</div><div class="message-content"><span class="message-role">Noor</span><p class="typing">Building the task graph and selecting providers…</p></div>`;
  messages.appendChild(typing);
  messages.scrollTop = messages.scrollHeight;

  try {
    const result = await executeRequest(text);
    typing.remove();
    statusText.textContent = result.success ? "Verified" : "Attention required";
    appendWorkflow(result);
  } catch (error) {
    typing.remove();
    statusText.textContent = "Error";
    appendMessage(error.message || "Noor could not complete the request.");
  }
});

input.addEventListener("input", resizeInput);
input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

suggestions.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-prompt]");
  if (!button) return;
  input.value = button.dataset.prompt;
  resizeInput();
  form.requestSubmit();
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && panel.classList.contains("is-open")) closePanel();
});

checkHealth();
