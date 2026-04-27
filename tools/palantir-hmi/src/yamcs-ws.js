/**
 * Yamcs WebSocket client — subscribe to parameter updates with auto-reconnect.
 *
 * Yamcs 5.x WebSocket API spoken here is documented at
 * https://docs.yamcs.org/yamcs-server-manual/general/websocket/. The
 * server's first frame after subscription contains a numericId↔name
 * mapping; later frames reference parameters by numericId only to save
 * bandwidth. This client unpacks both shapes back into the qualified
 * parameter name so callers don't care about the wire optimisation.
 */

const RECONNECT_INITIAL_MS = 1000;
const RECONNECT_MAX_MS = 30000;

/**
 * Subscribe to a list of qualified parameter names. The supplied
 * onUpdate callback fires whenever any parameter has a fresh value:
 *
 *     onUpdate({name: "/Palantir/Latitude", value: 48.7, time: Date})
 *
 * Returns a "close" function the caller can invoke on teardown.
 *
 * @param {string} url - ws://host:port/api/websocket
 * @param {string} instance - Yamcs instance name (e.g. "palantir")
 * @param {string} processor - Yamcs processor (e.g. "realtime")
 * @param {string[]} parameterNames - fully-qualified parameter paths
 * @param {(p: {name: string, value: number, time: Date}) => void} onUpdate
 * @param {(state: "connecting" | "open" | "closed") => void} [onStatus]
 */
export function subscribeParameters(url, instance, processor, parameterNames, onUpdate, onStatus) {
  let ws = null;
  let backoff = RECONNECT_INITIAL_MS;
  let teardown = false;
  // numericId -> qualified name; rebuilt on every (re)subscribe.
  let idToName = {};

  function connect() {
    onStatus?.("connecting");
    ws = new WebSocket(url);

    ws.onopen = () => {
      backoff = RECONNECT_INITIAL_MS;
      onStatus?.("open");
      ws.send(JSON.stringify({
        type: "parameters",
        id: 1,
        options: {
          instance,
          processor,
          id: parameterNames.map((name) => ({ name })),
          sendFromCache: true,
          updateOnExpiration: false,
        },
      }));
    };

    ws.onmessage = (event) => {
      let frame;
      try { frame = JSON.parse(event.data); } catch { return; }
      if (frame.type !== "parameters" || !frame.data) return;

      // First frame after subscribe carries the numericId<->name mapping.
      // Yamcs sends each entry as a NamedObjectId object {namespace, name},
      // not a plain string — flatten to qualified name for callers.
      if (frame.data.mapping) {
        idToName = {};
        for (const [numId, entry] of Object.entries(frame.data.mapping)) {
          idToName[numId] = typeof entry === "string"
            ? entry
            : `${entry.namespace ?? ""}/${entry.name ?? ""}`.replace(/\/+/g, "/");
        }
      }
      // Older Yamcs builds also include id.name on each value; prefer that.
      for (const val of frame.data.values ?? []) {
        const qualifiedName = val.id
          ? `${val.id.namespace ?? ""}/${val.id.name}`.replace(/\/+/g, "/")
          : idToName[val.numericId];
        if (!qualifiedName || typeof qualifiedName !== "string") continue;
        const eng = val.engValue ?? {};
        const v = eng.floatValue ?? eng.doubleValue ?? eng.uint32Value ?? eng.sint32Value;
        if (v === undefined) continue;
        const time = val.generationTime ? new Date(val.generationTime) : new Date();
        onUpdate({ name: qualifiedName, value: Number(v), time });
      }
    };

    ws.onclose = () => {
      onStatus?.("closed");
      if (teardown) return;
      setTimeout(connect, backoff);
      backoff = Math.min(backoff * 2, RECONNECT_MAX_MS);
    };

    ws.onerror = () => { ws?.close(); };
  }

  connect();
  return () => { teardown = true; ws?.close(); };
}
