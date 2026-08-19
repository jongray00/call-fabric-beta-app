# Verification tests for the USA Line Pro questions

These tests exist to check the behavioural claims in
`docs/usa-line-pro-answers.md` rather than to test this app. Run them with
`npm test`.

| File | What it proves |
| --- | --- |
| `fabric-push-notification.test.js` | How `registerDevice` / `handlePushNotification` / `online` actually behave in @signalwire/js 3.30.0: the WebSocket dependency, the app-side decrypt requirement, handler routing and the handler-wiping side effect. Drives the real SDK against `helpers/mockRelay.js`. |
| `fabric-cold-start.test.js` | What a cold-started page needs before it can handle a push: a reachable relay, a token the relay accepts, and awareness that `SignalWire()` is a singleton that ignores a newer token. |
| `swml-connect-confirm.test.js` | The `connect.confirm` / `live_transcribe` contract, validated against the official SWML JSON schema in `fixtures/swml-schema.json` — including that `live_transcribe` is not an allowed inline `confirm` method. |
| `helpers/mockRelay.js` | Mock relay WebSocket: answers `signalwire.connect`, records RPCs, can answer `webrtc.verto` with success/error/silence, and can push a server-side `verto.invite`. |
| `helpers/pushPayload.js` | Builds SignalWire-shaped encrypted push payloads and decrypts them with the exact algorithm in `public/minimal.js` (AES-256-GCM + pako). |
| `helpers/hangProbe.js` | Out-of-process probe for the case where `handlePushNotification` is handed a payload that was never decrypted (the promise never settles). |

Notes:

* `fixtures/swml-schema.json` is the official SWML JSON schema as retrieved on
  2026-08-19. Refresh it if SWML changes; the tests read the allowed-method list
  straight out of it.
* `pako` is pinned to 2.x on purpose: pako 3 removed the `{ to: 'string' }`
  inflate option that the browser code in `public/` relies on.
* Tests run with `--forceExit` because the SDK keeps reconnect timers alive after
  a session drops.
