const form = document.getElementById("form");
const log = document.getElementById("log");
const questionInput = document.getElementById("question");
const sendBtn = document.getElementById("sendBtn");
const statusDot = document.querySelector("#statusPill .dot");
const statusText = document.getElementById("statusText");
const suggestions = document.getElementById("suggestions");
const expandToggle = document.getElementById("expandToggle");
const expandIcon = document.getElementById("expandIcon");
const collapseIcon = document.getElementById("collapseIcon");
const appShell = document.querySelector(".app-shell");
let conversation = [];

function applyExpanded(isExpanded) {
  appShell.classList.toggle("expanded", isExpanded);
  expandIcon.style.display = isExpanded ? "none" : "block";
  collapseIcon.style.display = isExpanded ? "block" : "none";
  expandToggle.setAttribute("aria-pressed", String(isExpanded));
  expandToggle.setAttribute("aria-label", isExpanded ? "Collapse chat window" : "Expand chat window");
  expandToggle.title = isExpanded ? "Collapse chat window" : "Expand chat window";
  localStorage.setItem("askkevin-expanded", isExpanded ? "1" : "0");
}

function initExpanded() {
  applyExpanded(localStorage.getItem("askkevin-expanded") === "1");
}

expandToggle.addEventListener("click", () => {
  applyExpanded(!appShell.classList.contains("expanded"));
});

function setStatus(mode, label) {
  statusDot.classList.remove("busy", "error");
  if (mode === "busy") statusDot.classList.add("busy");
  if (mode === "error") statusDot.classList.add("error");
  statusText.textContent = label;
}

function scrollToBottom() {
  log.scrollTop = log.scrollHeight;
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function formatTimestamp() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function renderMarkdown(text) {
  const lines = escapeHtml(text).split("\n");
  const htmlLines = [];
  let inList = false;
  for (const line of lines) {
    const bulletMatch = line.match(/^[*-]\s+(.*)/);
    if (bulletMatch) {
      if (!inList) { htmlLines.push("<ul>"); inList = true; }
      htmlLines.push(`<li>${inlineMarkdown(bulletMatch[1])}</li>`);
      continue;
    }
    if (inList) { htmlLines.push("</ul>"); inList = false; }
    htmlLines.push(line.trim() ? `<p>${inlineMarkdown(line)}</p>` : "");
  }
  if (inList) htmlLines.push("</ul>");
  return htmlLines.join("");
}

function inlineMarkdown(escapedLine) {
  return escapedLine
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>");
}

function addUserRow(question) {
  const turn = document.createElement("div");
  turn.className = "turn";
  turn.innerHTML = `
    <div class="row user">
      <div class="bubble user">${escapeHtml(question)}</div>
      <div class="bubble-avatar user-avatar">You</div>
    </div>
    <div class="meta-row user-meta-row">
      <span class="meta-pill">${formatTimestamp()}</span>
    </div>
  `;
  log.appendChild(turn);
  scrollToBottom();
  return turn;
}

function addTypingRow() {
  const row = document.createElement("div");
  row.className = "turn";
  row.innerHTML = `
    <div class="row typing-row">
      <img src="/static/brand/mark.svg" class="bubble-avatar-img" alt="" />
      <div class="typing-dots"><span></span><span></span><span></span></div>
    </div>
  `;
  log.appendChild(row);
  scrollToBottom();
  return row;
}

const PROVIDER_ERROR_LABELS = {
  timeout: "timed out",
  rate_limit: "rate limited",
  connection: "connection issue",
  server_error: "provider error",
  auth: "auth error",
  bad_request: "bad request",
  error: "unavailable",
};

function classify(data) {
  const reason = data.refusal_reason || "";
  if (reason === "gibberish") return { kind: "unclear", label: "Unclear question", bubbleClass: "unclear", tagClass: "unclear-tag" };
  if (reason === "profanity") return { kind: "blocked", label: "Declined \u00b7 please keep it professional", bubbleClass: "blocked", tagClass: "blocked-tag" };
  if (reason.startsWith("personal_boundary") || reason === "not_grounded") return { kind: "blocked", label: "Declined \u00b7 outside job-relevant scope", bubbleClass: "blocked", tagClass: "blocked-tag" };
  if (reason.startsWith("provider_unavailable")) {
    const category = reason.split(":")[1] || "error";
    const detail = PROVIDER_ERROR_LABELS[category] || category;
    return { kind: "provider_down", label: `Provider unavailable \u00b7 ${detail}`, bubbleClass: "provider-down", tagClass: "down-tag" };
  }
  return { kind: "answer", label: "", bubbleClass: "answer", tagClass: "" };
}

function renderSources(data) {
  if (!data.sources || data.sources.length === 0) return "";
  const items = data.sources
    .map((source) => {
      const pct = Math.min(100, Math.round(source.score * 100 * 3));
      return `
        <div class="source-item">
          <div class="source-head"><span>${escapeHtml(source.source)} / ${escapeHtml(source.section)}</span><span>${source.score}</span></div>
          <div class="score-bar-track"><div class="score-bar-fill" style="width:${pct}%"></div></div>
        </div>
      `;
    })
    .join("");
  return `
    <details class="sources">
      <summary>${data.sources.length} source${data.sources.length > 1 ? "s" : ""} behind this answer</summary>
      ${items}
    </details>
  `;
}

function providerBadgeClass(provider) {
  if (provider === "openai") return "provider-openai";
  if (provider === "anthropic") return "provider-anthropic";
  if (provider === "gemini") return "provider-gemini";
  return "";
}

function formatCostUsd(cost) {
  if (cost == null) return null;
  if (cost === 0) return "$0";
  // Cost per turn is fractions of a cent, so show enough digits to be non-zero without pretending to more precision than a pricing snapshot can offer.
  if (cost < 0.0001) return `~$${cost.toExponential(2)}`;
  return `~$${cost.toFixed(6).replace(/0+$/, "").replace(/\.$/, "")}`;
}

function tokenUsagePill(data) {
  const usage = data.token_usage;
  if (!usage || usage.total_tokens == null) return "";
  const prompt = usage.prompt_tokens ?? 0;
  const completion = usage.completion_tokens ?? 0;
  const cached = usage.cached_tokens ?? 0;
  const cachedPercent = prompt > 0 ? Math.round((cached / prompt) * 100) : 0;
  const lines = [
    `Model: ${usage.model ?? "unknown"}`,
    `Prompt: ${prompt} tokens (${cached} cached, ${cachedPercent}%)`,
    `Completion: ${completion} tokens`,
    `Total: ${usage.total_tokens} tokens`,
  ];
  const costLabel = formatCostUsd(usage.estimated_cost_usd);
  if (costLabel) lines.push(`Estimated cost: ${costLabel}`);
  const tooltip = escapeHtml(lines.join("\n"));
  return `<span class="meta-pill" title="${tooltip}">${usage.total_tokens} tokens</span>`;
}

function renderAnswerTurn(data) {
  const info = classify(data);
  const tagHtml = info.label ? `<span class="tag ${info.tagClass}">${info.label}</span><br/>` : "";
  const turn = document.createElement("div");
  turn.className = "turn";
  turn.innerHTML = `
    <div class="row">
      <img src="/static/brand/mark.svg" class="bubble-avatar-img" alt="" />
      <div class="bubble ${info.bubbleClass}">${tagHtml}<div class="answer-text">${renderMarkdown(data.answer)}</div><button class="copy-btn" type="button" title="Copy answer" aria-label="Copy answer"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"><rect x="9" y="9" width="11" height="11" rx="2" stroke="currentColor" stroke-width="1.6"/><path d="M5 15V5a2 2 0 0 1 2-2h10" stroke="currentColor" stroke-width="1.6"/></svg></button></div>
    </div>
    <div class="meta-row">
      <span class="meta-pill provider-pill ${providerBadgeClass(data.provider)}">${escapeHtml(data.provider)}</span>
      <span class="meta-pill">${data.latency_ms}ms</span>
      ${tokenUsagePill(data)}
      <span class="meta-pill">${formatTimestamp()}</span>
    </div>
    ${renderSources(data)}
  `;
  const copyBtn = turn.querySelector(".copy-btn");
  copyBtn.addEventListener("click", () => {
    navigator.clipboard.writeText(data.answer).then(() => {
      copyBtn.classList.add("copied");
      setTimeout(() => copyBtn.classList.remove("copied"), 1200);
    });
  });
  return turn;
}

async function submitQuestion(question) {
  addUserRow(question);
  const typingRow = addTypingRow();
  sendBtn.disabled = true;
  questionInput.disabled = true;
  setStatus("busy", "Thinking...");

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, history: conversation }),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    typingRow.remove();
    log.appendChild(renderAnswerTurn(data));
    if (!data.refused && data.sources.length > 0) conversation.push([question, data.answer]);
    setStatus("ready", "Ready");
  } catch (error) {
    typingRow.remove();
    const errTurn = document.createElement("div");
    errTurn.className = "turn";
    errTurn.innerHTML = `
      <div class="row">
        <div class="bubble-avatar warn-avatar">!</div>
        <div class="bubble provider-down">Something went wrong reaching the assistant backend. Is the server running?</div>
      </div>
      <div class="meta-row">
        <span class="meta-pill">${formatTimestamp()}</span>
      </div>
    `;
    log.appendChild(errTurn);
    setStatus("error", "Connection error");
  }

  scrollToBottom();
  sendBtn.disabled = false;
  questionInput.disabled = false;
  questionInput.focus();
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const question = questionInput.value.trim();
  if (!question) return;
  questionInput.value = "";
  suggestions.style.display = "none";
  submitQuestion(question);
});

suggestions.addEventListener("click", (event) => {
  const chip = event.target.closest(".chip");
  if (!chip) return;
  suggestions.style.display = "none";
  submitQuestion(chip.dataset.q);
});

document.addEventListener("keydown", (event) => {
  if (event.key === "/" && document.activeElement !== questionInput) {
    event.preventDefault();
    questionInput.focus();
  }
});

initExpanded();
setStatus("ready", "Ready");
