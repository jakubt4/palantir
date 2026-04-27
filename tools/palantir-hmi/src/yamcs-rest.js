/**
 * Yamcs REST client — minimal helpers for the telecommand panel.
 *
 * CORS is already permitted server-side (yamcs/etc/yamcs.yaml has
 * `allowOrigin: "*"`), so the browser hits Yamcs directly without a
 * proxy. All paths follow the patterns documented in FEATURES.md §1.3.
 */

const DEFAULT_BASE = "http://localhost:8090/api";

/**
 * Issue a no-argument command (e.g. PING, REBOOT_OBC). The qualified
 * command name maps onto the Yamcs URL path; e.g. "/Palantir/TC/PING"
 * becomes ".../commands/Palantir/TC/PING".
 *
 * @returns the parsed JSON response on 2xx; throws Error with a
 *   human-readable message on 4xx/5xx so callers can render it inline.
 */
export async function issueCommand(qualifiedCommand, { base = DEFAULT_BASE, instance = "palantir", processor = "realtime" } = {}) {
  const path = qualifiedCommand.replace(/^\//, "");
  const url = `${base}/processors/${instance}/${processor}/commands/${path}`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: "{}",
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status} ${res.statusText}${detail ? ` — ${detail}` : ""}`);
  }
  return res.json();
}

/**
 * Fetch recent command history from the Yamcs archive. Yamcs returns
 * results with newest first when `order=desc`; we keep that order so
 * the table shows the most recent at the top.
 */
export async function listRecentCommands(limit = 20, { base = DEFAULT_BASE, instance = "palantir" } = {}) {
  const url = `${base}/archive/${instance}/commands?limit=${limit}&order=desc`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`HTTP ${res.status} ${res.statusText}`);
  }
  const json = await res.json();
  return json.entry ?? [];
}
