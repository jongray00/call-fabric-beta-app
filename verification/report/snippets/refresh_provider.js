// Browser SDK v4 credential provider with backend-driven refresh.
// API surface verified against @signalwire/js@4.0.0-rc.4 types (evidence/sdk/sdk_facts.md, Item 1) and loaded
// in headless Chromium by the browser self-test. Live refresh behavior: not yet observed.
import { SignalWire, TokenRefreshError } from "@signalwire/js";

async function fetchSat() {
  const r = await fetch("/token");            // your backend calls mint_sat()
  const { token, expiry_at } = await r.json(); // expiry_at in ms since epoch
  return { token, expiry_at };
}

const first = await fetchSat();
const client = new SignalWire({
  authenticate: async () => first,
  refresh: async () => fetchSat(),             // called 5 s before expiry_at, up to 5 retries
});
client.errors$.subscribe((e) => {
  if (e instanceof TokenRefreshError) {
    // SDK has disconnected; prompt re-login or rebuild the client
  }
});
