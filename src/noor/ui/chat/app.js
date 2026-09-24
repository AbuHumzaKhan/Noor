const orb = document.getElementById("noorOrb");
const panel = document.getElementById("chatPanel");
const closeChat = document.getElementById("closeChat");
const form = document.getElementById("chatForm");
const input = document.getElementById("messageInput");
const messages = document.getElementById("messages");
const suggestions = document.getElementById("suggestions");

const suggestionMap = [
  {
    match: /excel|spreadsheet|workbook|xlsx|xlsm/i,
    text: "I can start with workbook inspection, then profile the data. Next step: connect the selected file to the Excel skill."
  },
  {
    match: /profile|missing|duplicate|quality|data/i,
    text: "Next step: profile the dataset first, then identify quality issues before analysis or transformation."
  },
  {
    match: /analy[sz]e|trend|sales|report|insight/i,
    text: "Next step: build an analysis plan, identify the relevant fields, validate the data, then calculate and verify the requested insights."
  },
  {
    match: /formula|sum|average|count/i,
    text: "Next step: inspect the worksheet structure and generate a formula against the actual headers and ranges."
  }
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

function appendMessage(text, role = "assistant") {
  const article = document.createElement("article");
  article.className = `message ${role === "user" ? "user-message" : "assistant-message"}`;

  if (role === "user") {
    article.innerHTML = `<div class="message-content"><p>${escapeHtml(text)}</p></div>`;
  } else {
    article.innerHTML = `
      <div class="message-avatar">N</div>
      <div class="message-content">
        <span class="message-role">Noor</span>
        <p>${escapeHtml(text)}</p>
      </div>`;
  }

  messages.appendChild(article);
  messages.scrollTop = messages.scrollHeight;
}

function escapeHtml(value) {
  const element = document.createElement("div");
  element.textContent = value;
  return element.innerHTML;
}

function nextStepFor(text) {
  const match = suggestionMap.find((item) => item.match.test(text));
  return match?.text ?? "Next step: I’ll interpret the request, break it into tasks, choose the required capabilities, and verify the result before reporting back.";
}

function resizeInput() {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 110)}px`;
}

orb.addEventListener("click", openChat);
closeChat.addEventListener("click", closePanel);

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text) return;

  appendMessage(text, "user");
  input.value = "";
  resizeInput();

  const typing = document.createElement("article");
  typing.className = "message assistant-message";
  typing.innerHTML = `
    <div class="message-avatar">N</div>
    <div class="message-content">
      <span class="message-role">Noor</span>
      <p class="typing">Thinking about the workflow…</p>
    </div>`;
  messages.appendChild(typing);
  messages.scrollTop = messages.scrollHeight;

  window.setTimeout(() => {
    typing.remove();
    appendMessage(nextStepFor(text));
  }, 450);
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
