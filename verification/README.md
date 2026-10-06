# SalesGodCRM browser calling verification harness

Unattended harness that answers the SalesGodCRM question list (Parts A, B, C) against a SignalWire test Space using
Browser SDK v4 Subscribers, SWML webhooks and the Calling REST API. Results land in `report/`.

## Run

```
cd verification
pip install fastapi uvicorn httpx numpy pyflakes && pip install --no-deps signalwire==2.1.1 && pip install twilio
npm install                       # pins @signalwire/js@4.0.0-rc.4
cp node_modules/@signalwire/js/dist/browser.umd.js harness/browser/signalwire.umd.js
cat > .env <<'X'
SW_SPACE=yourspace.signalwire.com
SW_PROJECT_ID=...
SW_API_TOKEN=...
SW_SIGNING_KEY=...                # optional, enables live B11
BUDGET_USD=25
NUMBER_AREA_CODE=561
RELEASE_NUMBERS=false
X
python -m harness.run
```

Requirements for the live path: outbound HTTPS to the Space and `signalwire.com`, Chromium for Playwright, and a
public tunnel (cloudflared quick tunnel, or `NGROK_AUTHTOKEN` with ngrok installed). Without these the runner still
runs the local self-tests and writes a report whose behavioral items are documentary or BLOCKED.

## Layout

| Path | Purpose |
|---|---|
| `harness/config.py` | `.env` loading, emergency/N11 denylist, owned-number dial guard, budget cap |
| `harness/httplog.py` | HTTP client that logs every request to `evidence/http.log.jsonl` with the token redacted |
| `harness/sw.py` | Calling API, Fabric Subscribers/resources, phone numbers, recordings, logs (documented endpoints only) |
| `harness/backend.py` | FastAPI webhook backend: SWML per test, webhook capture, token minting, browser event sink |
| `harness/tunnel.py` | cloudflared quick tunnel, ngrok fallback |
| `harness/browser/` | Device page (Browser SDK v4) and Playwright driver; one browser context per device |
| `harness/audio.py` | Tone fixtures and per-channel, per-second FFT analysis of recordings |
| `harness/signature.py` | Webhook signature validation |
| `harness/tests.py` | Live test inventory A1 to B18, 3 runs each |
| `harness/doc_answers.py` | Documentary answers used when a live test cannot run, and for Part C |
| `harness/selftest_*.py` | Local self-tests that need no Space |
| `evidence/docs/` | Every document relied on, with source and fetch time; `swml_facts.json`, `rest_facts.json` |
| `evidence/sdk/sdk_facts.md` | Browser SDK v4 API facts with line citations (re-create the package with `npm pack @signalwire/js@4.0.0-rc.4`) |
