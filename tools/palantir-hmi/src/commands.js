/**
 * PAL-102 — Telecommand panel.
 *
 * Two buttons issue PING / REBOOT_OBC via the Yamcs REST commanding
 * API; a table polled every 5 s shows the last 20 archived commands
 * with their lifecycle status (QUEUED → RELEASED → SENT under the
 * baseline configuration; FEATURES.md §1.3 notes there is no
 * closed-loop verifier yet so SENT is terminal, not COMPLETED).
 */

import { issueCommand, listRecentCommands } from "./yamcs-rest.js";

const POLL_INTERVAL_MS = 5000;
const HISTORY_LIMIT = 20;

const feedbackEl = document.getElementById("feedback");
const historyBodyEl = document.getElementById("historyBody");
const historyStatusEl = document.getElementById("historyStatus");

document.querySelectorAll("button[data-command]").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const cmd = btn.dataset.command;
    setFeedback(`Issuing ${cmd}…`, "pending");
    btn.disabled = true;
    try {
      const result = await issueCommand(cmd);
      const id = result?.id ?? "";
      setFeedback(`Issued ${cmd}${id ? ` (${id})` : ""}`, "ok");
      // Refresh history right away so the operator sees the new entry
      // without waiting up to 5 s for the next poll.
      refreshHistory();
    } catch (err) {
      setFeedback(`Failed: ${err.message}`, "error");
    } finally {
      btn.disabled = false;
    }
  });
});

function setFeedback(text, kind) {
  feedbackEl.textContent = text;
  feedbackEl.className = `feedback feedback-${kind}`;
}

async function refreshHistory() {
  try {
    const entries = await listRecentCommands(HISTORY_LIMIT);
    historyBodyEl.replaceChildren(...entries.map(renderRow));
    historyStatusEl.textContent = `last refresh ${new Date().toLocaleTimeString()}`;
    historyStatusEl.classList.remove("error");
  } catch (err) {
    historyStatusEl.textContent = `refresh failed: ${err.message}`;
    historyStatusEl.classList.add("error");
  }
}

function renderRow(entry) {
  const tr = document.createElement("tr");
  // Archive entries use epoch-ms strings on commandId.generationTime,
  // while realtime POST responses return ISO. Handle both.
  const rawTime = entry.commandId?.generationTime ?? entry.generationTime;
  const ts = rawTime
    ? new Date(/^\d+$/.test(String(rawTime)) ? Number(rawTime) : rawTime)
    : null;
  const time = ts ? ts.toLocaleTimeString() : "—";
  const name = entry.commandId?.commandName ?? entry.commandName ?? "—";
  const attrs = attrArrayToMap(entry.attr ?? []);
  const status = attrs.CommandComplete_Status
              ?? attrs.Acknowledge_Sent_Status
              ?? attrs.TransmissionConstraints
              ?? "SENT";
  const issuer = attrs.username ?? entry.username ?? "—";

  tr.innerHTML = `
    <td class="col-time">${time}</td>
    <td class="col-cmd">${escapeHtml(name)}</td>
    <td class="col-status"><span class="status-pill status-${escapeAttr(status.toLowerCase())}">${escapeHtml(status)}</span></td>
    <td class="col-issuer">${escapeHtml(issuer)}</td>
  `;
  return tr;
}

/**
 * Yamcs serialises command attributes as a list of {name, value} pairs
 * where each value is a typed wrapper ({stringValue} / {uint32Value} /
 * etc.). Flatten to a plain {name: scalar} map for ergonomic lookup.
 */
function attrArrayToMap(arr) {
  const out = {};
  for (const a of arr) {
    const v = a.value ?? {};
    out[a.name] = v.stringValue ?? v.uint32Value ?? v.sint32Value ?? v.doubleValue ?? v.binaryValue;
  }
  return out;
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function escapeAttr(s) { return escapeHtml(s).replace(/\s+/g, "-"); }

refreshHistory();
setInterval(refreshHistory, POLL_INTERVAL_MS);
