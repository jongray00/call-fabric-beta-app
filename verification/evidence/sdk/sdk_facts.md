# SignalWire Browser SDK v4 public API facts

Source: npm package `@signalwire/js` version `4.0.0-rc.4`, unpacked at `pkg/package`. All paths below are relative to `pkg/package/`. Citations are `dist/<file>:<line>`. Types from `dist/index.d.mts`; implementation from `dist/index.mjs`; constants from `dist/operators-CTNnvDcG.mjs` (the `src/core/constants.ts` region). Package contents were read only, never executed.

## Item 1: Constructing a client, SAT, refresh, registration

**Constructor.** The client class is `SignalWire` (not a factory function).

```ts
declare class SignalWire extends Destroyable implements DeviceController {
  constructor(credentialProvider: CredentialProvider | undefined, options?: SignalWireOptions);
}
```
`dist/index.d.mts:4923`, `dist/index.d.mts:4963`. Implementation `dist/index.mjs:11847`. The constructor immediately calls `resolveCredentials()` then `init()` (connect, then register) asynchronously; failures go to `errors$`, they do not throw from the constructor (`dist/index.mjs:11878-11890`).

**`SignalWireOptions`** (`dist/index.d.mts:4822-4893`): `skipConnection?`, `skipRegister?`, `skipDeviceMonitoring?`, `reconnectAttachedCalls?`, `savePreferences?`, `persistSession?`, `storageImplementation?: Storage`, `webSocketConstructor?`, `webRTCApiProvider?`, `logger?: SDKLogger | null`, `logLevel?: LogLevel`, `debug?: DebugOptions`, `callControl?: 'routed' | 'in-dialog'` (experimental). Defaults: all `skip*` false, `reconnectAttachedCalls` false, `savePreferences` false (`dist/index.mjs:435-441`).

**How the SAT is supplied.** Via a `CredentialProvider` whose `authenticate()` resolves an `SDKCredential`:

```ts
interface SDKCredential { token?: string; authorizationState?: string; expiry_at?: number /* ms since epoch */ }
interface AuthenticateContext { fingerprint?: string }
interface CredentialProvider {
  authenticate(context?: AuthenticateContext): Promise<SDKCredential>;
  refresh?: () => Promise<SDKCredential>;
}
```
`dist/index.d.mts:86-94`, `dist/index.d.mts:114-127`, `dist/index.d.mts:157-212`.

Built-in providers:
- `new StaticCredentialProvider(credentials: SDKCredential)`; only `authenticate()`, no `refresh` (`dist/index.d.mts:5430-5435`). Usage: `new SignalWire(new StaticCredentialProvider({ token: sat }))` (`dist/index.d.mts:5426-5427`).
- `new EmbedTokenCredentialProvider(host: string, embedToken: string)` with `authenticate()` and `refresh()` (`dist/index.d.mts:5439-5452`).
- `embeddableCall({ to, embedToken, host }): Promise<Call>` one-shot helper (`dist/index.d.mts:5400-5416`).

Validation (`dist/index.mjs:11966-11999`): the token is JWT-decoded (header `ch` is used as API host); a non-JWT token throws `InvalidCredentialsError("Invalid JWT token provided in credentials.")`. If `persistSession` is false and `expiry_at < Date.now()`, throws `InvalidCredentialsError("Provided credentials have expired.")`. Note: `expiry_at` is milliseconds since epoch.

**Refresh provider / callback.** `CredentialProvider.refresh?: () => Promise<SDKCredential>` (`dist/index.d.mts:211`). When it is called:
- Only if the credential has `expiry_at` AND the SAT does not carry `sat:refresh` scope (precedence table at `dist/index.d.mts:140-147`).
- Scheduled by `CredentialRefreshCoordinator.scheduleDeveloperRefresh`: first fire at `max(expiry_at - now - CREDENTIAL_REFRESH_BUFFER_MS, 1000)` ms, i.e. 5 s before expiry (`dist/index.mjs:10837-10845`, `dist/operators-CTNnvDcG.mjs:67`).
- On failure: retry with jittered exponential backoff (base 1 s, cap 30 s) up to `CREDENTIAL_REFRESH_MAX_RETRIES = 5` (`dist/operators-CTNnvDcG.mjs:61-65`). Each failure is pushed to `client.errors$`; after exhaustion it pushes `new TokenRefreshError("Credential refresh failed after max retries")` to `errors$` and calls `disconnect()` (`dist/index.mjs:10871-10881`, notifier wiring `dist/index.mjs:11935-11939`).
- After a successful refresh the new token is stored, persisted and the live session is reauthenticated (`signalwire.reauthenticate`) (`dist/index.mjs:10856-10866`).
- `refresh()` is also used for reconnect re-mint when the session is unbound and the in-memory token is within `CREDENTIAL_EXPIRY_SKEW_MS = 30000` of expiry (`dist/index.d.mts:5039-5053`, `dist/operators-CTNnvDcG.mjs:75`).
- If `expiry_at` is set but no `refresh` is provided, a warning `{ code: 'credential_no_refresh_handler', source: 'CredentialProvider', message, expiresAt }` is emitted on `client.warnings$` (`dist/index.mjs:11986-11993`, type `dist/index.d.mts:4763-4769`).

**`TokenRefreshError`.** `declare class TokenRefreshError extends Error { originalError?: unknown; constructor(message: string, originalError?: unknown) }` (`dist/index.d.mts:1319-1322`). Exported. Thrown/emitted:
- Developer-refresh exhaustion: emitted on `client.errors$`, then `disconnect()` (`dist/index.mjs:10879-10880`).
- Client Bound SAT (DPoP device-token) refresh failures: `"Failed to refresh device token: <status>"`, `"Device token refresh response missing token field"`, `"No current token available for refresh"`, `"Automatic token refresh failed"`, `"All refresh retries exhausted"` (`dist/index.mjs:10686`, `10688`, `10724`, `10729`, `10750`), routed to `errors$` via the coordinator notifier.
- Related: `DeviceTokenError` for the initial `/devices/token` exchange (`dist/index.d.mts:1315-1318`, `dist/index.mjs:10659-10661`); `InvalidCredentialsError { reason }` (`dist/index.d.mts:1146-1149`); `DPoPInitError` (`dist/index.d.mts:1283`).

**Fingerprint / `sat:refresh` (Client Bound SAT, DPoP).**
- SDK generates an ECDSA DPoP key pair, persisted in IndexedDB DB `sw-dpop`, store `keys`, key id `dpop-keypair` (`dist/index.mjs:1722-1725`), fingerprint = RFC 7638 JWK thumbprint (`dist/index.mjs:1826-1911`).
- `authenticate({ fingerprint })` is called with that fingerprint when available (`dist/index.mjs:11967-11968`). App should forward it to `POST /api/fabric/subscribers/tokens` with `scope: ["sat:refresh"]` (`dist/index.d.mts:118-127`, `dist/index.d.mts:149-151`).
- `SAT_REFRESH_SCOPE = "sat:refresh"` (`dist/operators-CTNnvDcG.mjs:48`). If the user's `sat_claims.scope` contains it, `DeviceTokenManager.activate()` calls `/api/fabric/subscriber/devices/token` (`DEVICE_TOKEN_ENDPOINT`) and later `/api/fabric/subscriber/devices/refresh` (`DEVICE_REFRESH_ENDPOINT`) (`dist/operators-CTNnvDcG.mjs:50-51`, `dist/index.mjs:10565-10600`). Otherwise returns `{ activated: false, reason: 'no-scope' }` and the coordinator emits warning `{ code: 'credential_refresh_fallback', reason }` on `warnings$` (`dist/index.mjs:11010-11016`). Reasons: `'no-scope' | 'no-dpop-support' | 'endpoint-failed' | 'activation-timeout'` (`dist/index.d.mts:4735`).
- `SATClaims { scope?: string[]; cnf?: { jkt }; expires_at?: number /* seconds */ }` (`dist/index.d.mts:652-661`). `client.session.clientBound: boolean` (`dist/index.d.mts:4557`).

**Registration ("online").**
- `register(): Promise<void>` sends JSON-RPC `subscriber.online` and sets `isRegistered$` true; on failure tries credential recovery then throws `InvalidCredentialsError` (`dist/index.d.mts:5218`, `dist/index.mjs:12526-12557`).
- `unregister(): Promise<void>` sends `subscriber.offline` (`dist/index.d.mts:5224`, `dist/index.mjs:12563-12575`).
- Auto-registration: `init()` calls `connect()` unless `skipConnection`, then `register()` unless `skipRegister` (`dist/index.mjs:12172-12182`).
- Observables: `isRegistered$ / isRegistered`, `isConnected$ / isConnected`, `ready$` (connected and authenticated), `errors$: Observable<Error>`, `warnings$: Observable<SDKWarning>`, `user$`, `directory$` (`dist/index.d.mts:5131-5174`). `connect()`, `disconnect()`, `destroy()`, `resetToDefaults()` (`dist/index.d.mts:5119`, `5203`, `5395`, `5385`).

## Item 2: Inbound calls

**Observable.** `incomingCalls$` is NOT on `SignalWire` itself; it is on `client.session` (type `ClientSessionWrapper`, implements `SessionState`):

```ts
get session(): ClientSessionWrapper;          // dist/index.d.mts:5277
readonly incomingCalls$: Observable<Call[]>;  // dist/index.d.mts:4225 (SessionState)
readonly incomingCalls: Call[];               // dist/index.d.mts:4229
readonly calls$: Observable<Call[]>;          // dist/index.d.mts:4233
get incomingCalls$(): Observable<Call[]>;     // dist/index.d.mts:4711 (ClientSessionWrapper)
```
Element type is an array `Call[]` of currently active inbound calls (filter of `calls$` by `direction === 'inbound'`), not a stream of single calls. Consumers must diff the arrays to detect a new call.

Inbound calls are created from a `verto.invite` (`dist/index.mjs:10026-10033`) by `createInboundCall` (`dist/index.mjs:10286-10301`), mapping: `nodeId: invite.node_id`, `callId: invite.callID`, `initOffer: invite.sdp`, `toName: invite.callee_id_name`, `to: invite.callee_id_number`, `fromName: invite.caller_id_name`, `from: invite.caller_id_number`, `displayDirection: invite.display_direction`, `userVariables: invite.userVariables`.

**Call object (`interface Call extends CallState`, `dist/index.d.mts:2411-2512`; class `WebRTCCall`, `dist/index.d.mts:3621`).**
- Identity: `id: string` (the Verto callID; there is no separate `callId` property) (`dist/index.d.mts:2412`, `3626`); `direction: 'inbound' | 'outbound'` (`2448`; computed as `options.initOffer ? 'inbound' : 'outbound'`, `dist/index.mjs:8338-8340`).
- Parties: `to?`, `toName?`, `from?`, `fromName?` (`dist/index.d.mts:2444-2447`).
- `userVariables?: Record<string, unknown>` (getter returns a copy, setter merges) and `userVariables$` (`dist/index.d.mts:2467-2468`, `3842-3846`). Seeded from global `preferences.userVariables`, then destination query params, then `options.userVariables`, then merged with any `params.userVariables` in later `webrtc.message` events (`dist/index.mjs:8268`, `8283-8294`).
- `nodeId` / `nodeId$`, `selfId`, `answered$`, `options: CallOptions` exist on `CallManager` / `WebRTCCall` but not on the public `Call` interface (`dist/index.d.mts:2514-2520`, `3925-3927`).
- Media: `localStream$ / localStream`, `remoteStream$ / remoteStream`, `rtcPeerConnection`, `mediaDirections$` (`dist/index.d.mts:2455-2462`).
- Other state: `participants$`, `self$ / self`, `recording$`, `streaming$`, `locked$`, `meta$`, `layouts$`, `layout$`, `capabilities$`, `address$`, `errors$: Observable<CallError>`, `signalingEvent$`, `networkIssues$`, `networkMetrics$`, `qualityScore$`, `qualityLevel$`, `recoveryState$`, `recoveryEvent$`, `bandwidthConstrained$`, `mediaParamsUpdated$`, `localAudioLevel$`, `localSpeaking$`, `remoteAudioLevel$`, `localMicrophoneGain$`.
- Methods: `answer(options?: MediaOptions): void` (`2493`), `reject(): void` (`2494`; implementation only does `_answered$.next(false)`, `dist/index.mjs:9105-9107`), `hangup(): Promise<void>` (`2484`), `toggleHold()`, `transfer(options)`, `sendDigits(digits)`, `toggleLock()`, `setLayout()`, `subscribe(eventType)`, `requestKeyframe()`, `requestIceRestart()`, `execute()`, `executeMethod()`, `setLocalMicrophoneGain()`, push-to-talk methods, `setEchoCancellation/NoiseSuppression/AutoGainControl()`. `startRecording`, `startStreaming`, `setMeta`, `updateMeta`, `toggleIncomingVideo`, `toggleIncomingAudio` throw `UnimplementedError` (`dist/index.d.mts:3674-3709`).
- Not present (searched `headers`, `sipHeaders`, `customData`, `custom`): no `headers` or custom-data property on calls. Only `userVariables` and `meta`.

**Status.** `status$: Observable<CallStatus>`, `status: CallStatus` (`dist/index.d.mts:2413-2414`).
```ts
type CallStatus = 'new' | 'trying' | 'ringing' | 'connecting' | 'connected' | 'recovering'
                | 'disconnecting' | 'disconnected' | 'failed' | 'destroyed';
```
`dist/index.d.mts:2375` (identical `ResilienceCallStatus`, `dist/index.d.mts:1349`). Inbound calls start in `'ringing'`, outbound in `'new'` (`dist/index.mjs:8298-8301`). There is no `'answered'`, `'active'` or `'ended'` value; use `'connected'` and `'disconnected'` / `'destroyed'` / `'failed'`. Fatal `CallError` moves the call to `'failed'` (`dist/index.mjs:8323-8330`). `hangup()` moves to `'disconnecting'` then destroys (`dist/index.d.mts:3975-3986`). Separate low-level type `SignalingCallStates = 'created' | 'ringing' | 'answered' | 'ending' | 'ended'` exists for server call-state payloads (`dist/index.d.mts:754`), surfaced via `CallManager.callStates$`.

## Item 3: Outbound `dial()`

```ts
dial(destination: string | Address, options?: DialOptions): Promise<Call>;   // dist/index.d.mts:5254
interface DialOptions extends MediaOptions {                                  // dist/index.d.mts:4895-4910
  preferredVideoCodecs?: string[];
  preferredAudioCodecs?: string[];
  stereo?: boolean;
  nodeId?: string;
  userVariables?: Record<string, unknown>;
}
interface MediaOptions {                                                      // dist/index.d.mts:339-361
  audio?: boolean;            // default true
  video?: boolean;            // default false
  inputAudioDeviceConstraints?: MediaTrackConstraints;
  inputVideoDeviceConstraints?: MediaTrackConstraints;
  inputAudioStream?: MediaStream;
  inputVideoStream?: MediaStream;
  receiveAudio?: boolean;
  receiveVideo?: boolean;
  fallbackToReceiveOnly?: boolean; // default true
}
```
There is no `to` field in `DialOptions`; the destination is the first argument (internally becomes `CallOptions.to`, `dist/index.mjs:10335-10342`). Merge order: preferred media options, then `?channel=video|audio` from the destination, then `options` (`dist/index.mjs:12605-12611`, `11809-11826`). Query-string params on the destination are also merged into userVariables (`fromDestinationParams`, `dist/index.mjs:8237-8249`). The invite sends `userVariables: { memberCallId, memberId, ...call.userVariables }` (`dist/index.mjs:7149-7153`). `dial()` resolves after signaling is ready, bounded by `DEFAULT_CALL_SIGNALING_TIMEOUT_MS = 12000` (`dist/index.mjs:10343`, `dist/operators-CTNnvDcG.mjs:33`).

Example:
```js
const call = await client.dial('/private/foo', {
  audio: true,
  video: false,
  userVariables: { scenario: 'abc', testId: '123' },
});
const call2 = await client.dial('/public/foo?channel=audio', { userVariables: { k: 'v' } });
```

## Item 4: In-call controls

- Hold: `call.toggleHold(): Promise<void>` (`dist/index.d.mts:2486`, `3693`). It sends `verto.modify` with `action: 'hold'` or `'unhold'` and flips a private `_holdState` (`dist/index.mjs:8391-8395`, `6468-6492`). No public `hold()` / `unhold()` on `Call` and no public hold-state observable; `hold()`/`unhold()` exist only on the internal `WebRTCVerto` manager (`dist/index.d.mts:3489-3490`).
- Audio mute: on the participant, not on the call: `call.self.mute()`, `call.self.unmute()`, `call.self.toggleMute()`; video: `muteVideo()`, `unmuteVideo()`, `toggleMuteVideo()`; deaf: `toggleDeaf()` (`CallParticipant` `dist/index.d.mts:2300-2307`; `Participant` `2016-2030`; `SelfParticipant` overrides `mute/unmute/muteVideo/unmuteVideo` with local fallback if RPC fails, `2235-2241`). State: `audioMuted$ / audioMuted` (`dist/index.d.mts:2257`, `2278`). `call.self` is `CallSelfParticipant | null`; `call.self$` waits for non-null (`dist/index.d.mts:2442-2443`).
- Hangup: `call.hangup(): Promise<void>` (Verto `bye`) (`dist/index.d.mts:2484`, `3986`).
- DTMF: `call.sendDigits(dtmf: string): Promise<void>` (`dist/index.d.mts:2495`, `3997`).
- Transfer: `call.transfer(options: TransferOptions): Promise<void>`, `interface TransferOptions { destination: string }` (`dist/index.d.mts:2490`, `1137-1139`); sends `verto.modify` `action: 'transfer'` (`dist/index.mjs:7342-7354`).
- Answer/reject: `call.answer(options?: MediaOptions)`, `call.reject()` (`dist/index.d.mts:4017`, `4026`).

## Item 5: Multiple client instances in one page

Multiple `new SignalWire(...)` instances are possible (each has its own `DependencyContainer`, transport and session; `dist/index.mjs:11858`), but there is shared global state:
- `PreferencesContainer.instance` is a module-level singleton (`dist/index.mjs:419-423`). Every `client.preferences` (`ClientPreferences`) getter/setter reads/writes it (`dist/index.mjs:652-802`), including `preferences.userVariables`, timeouts, ICE servers, codecs. New calls on any instance seed `userVariables` from it (`dist/index.mjs:8268`). Default `SignalWireOptions` also come from it (`dist/index.mjs:11860-11863`).
- Logger configuration is global (`setLogger`, `setLogLevel`, `setDebugOptions`; documented at `dist/index.d.mts:4862`, `4870`).
- Storage keys (default `Storage` is `localStorage` / `sessionStorage`, default scope `'session'`; `dist/index.mjs:1491-1529`):
  - Per subscriber (keyed by `user.id`): `sw:${userId}:as` (authorization state), `sw:${userId}:pt` (protocol), `sw:${userId}:att` (attached calls) (`dist/index.mjs:1675-1683`).
  - NOT keyed per token or subscriber: `sw:cached_credential` (`dist/index.mjs:12146-12151`, `11958`), `sw:client_bound` (`dist/index.mjs:11808`), `sw:preferences` (`dist/operators-CTNnvDcG.mjs:46`), `sw:device:audioinput|audiooutput|videoinput` (`dist/operators-CTNnvDcG.mjs:150-152`).
  - IndexedDB `sw-dpop` / `keys` / `dpop-keypair`: a single DPoP key pair (thus the same fingerprint) shared by all instances in the origin (`dist/index.mjs:1722-1725`).
  - `clear()` / `resetToDefaults()` remove all `sw:` keys in the scope (`dist/index.mjs:1519-1527`).
- Practical implication: two clients for different subscribers in the same tab will overwrite each other's `sw:cached_credential`. With a provider present, `resolveCredentials` always calls `provider.authenticate()` (the cache is read only when there is no provider), despite the doc comment saying "cache-first" (`dist/index.mjs:11916-11964`). For isolation, pass a distinct `storageImplementation` per instance (in-memory) and avoid `persistSession` / `savePreferences`, and do not rely on `preferences.userVariables` (use per-dial `userVariables`).

## Item 6: RTCPeerConnection / getStats

- `call.rtcPeerConnection: RTCPeerConnection | undefined` (`dist/index.d.mts:2462`, `3945`, "Underlying RTCPeerConnection, for advanced use cases"). Codec info: `await call.rtcPeerConnection.getStats()` and read `codec` reports (`mimeType`, `clockRate`, `sdpFmtpLine`) referenced by `outbound-rtp` / `inbound-rtp` `codecId`. No SDK method returns negotiated codec directly (searched `codec` in d.mts: only preference lists and `PlatformCapabilities.audioCodecs/videoCodecs`, `dist/index.d.mts:1427-1430`).
- Internal stats monitor polls `peerConnection.getStats()` every `statsPollingInterval` (default 1000 ms) (`dist/index.mjs:7535`, `dist/operators-CTNnvDcG.mjs:98`), surfaced as `call.networkMetrics$` (`NetworkMetrics`: audio packetsReceived/Lost/jitter, video packets, `roundTripTime`, `availableOutgoingBitrate`; `dist/index.d.mts:1119-1133`), `networkIssues$`, `qualityScore$` (MOS 1-5), `qualityLevel$`.
- `client.exportDiagnostics(): SessionDiagnostics` (`dist/index.d.mts:5183`); `CallDiagnosticSummary` has no codec field (`dist/index.d.mts:1552-1573`).
- Codec preference: `DialOptions.preferredAudioCodecs` / `preferences.preferredAudioCodecs`, `stereo` (`dist/index.d.mts:4897-4901`, `537-542`).

## Item 7: Limits and timeouts (constants)

From `dist/operators-CTNnvDcG.mjs` (`src/core/constants.ts`):
| Constant | Value | Line |
|---|---|---|
| `DEFAULT_CONNECTION_TIMEOUT_MS` | 10000 | 10 |
| `DEFAULT_RECONNECT_DELAY_MIN_MS` / `MAX_MS` | 100 / 3000 | 42-43 |
| `DEFAULT_RECONNECT_CALLS_TIMEOUT_MS` | 300000 | 9 |
| `SERVER_PING_TIMEOUT_MS` (server pings every 10 s) | 15000 | 16 |
| `SERVER_PING_PROBE_TIMEOUT_MS` | 10000 | 22 |
| `DEFAULT_CALL_SIGNALING_TIMEOUT_MS` (dial budget after media settles) | 12000 | 33 |
| `DEFAULT_AUX_LEG_CONNECT_TIMEOUT_MS` | 15000 | 41 |
| `DEFAULT_ICE_CANDIDATE_TIMEOUT_MS` / `DEFAULT_ICE_GATHERING_TIMEOUT_MS` | 600 / 6000 | 7-8 |
| `DEVICE_TOKEN_DEFAULT_EXPIRE_IN` (s) | 900 | 53 |
| `DEVICE_TOKEN_REFRESH_BUFFER_MS` | 30000 | 55 |
| `DEVICE_TOKEN_REFRESH_MAX_RETRIES` / base | 3 / 1000 ms | 57-59 |
| `CREDENTIAL_REFRESH_MAX_RETRIES` / base / max delay | 5 / 1000 / 30000 ms | 61-65 |
| `CREDENTIAL_REFRESH_BUFFER_MS` (developer refresh fires this early) | 5000 | 67 |
| `CREDENTIAL_EXPIRY_SKEW_MS` | 30000 | 75 |
| `CREDENTIAL_ACTIVATE_TIMEOUT_MS` | 30000 | 82 |
| RPC error codes -32003 / -32602 / -32002 | | 84-88 |
| `DEFAULT_MAX_RECOVERY_ATTEMPTS`, `DEFAULT_REINVITE_MAX_ATTEMPTS` | 3, 3 | 132, 120 |
| `DEFAULT_ICE_DISCONNECTED_GRACE_PERIOD_MS`, `DEFAULT_ICE_RESTART_TIMEOUT_MS` | 3000, 5000 | 128, 130 |
| `DEFAULT_DEVICE_DEBOUNCE_TIME_MS` | 1500 | 44 |

RPC default timeout 5 s per `connect()` docs (`dist/index.d.mts:5111-5113`). Not found (searched `MAX_DEVICES`, `maxDevices`, `max_devices`, `ringTimeout`, `ring_timeout`, `RING`): no max-device count and no client-side ring/answer timeout for inbound calls.

## Item 8: Loading in a plain browser page

`dist/browser.umd.js` header: `factory((global.SignalWire = {}))` with `global = globalThis` (`dist/browser.umd.js:4`). So the UMD global is the namespace object `window.SignalWire`, and the client class is `window.SignalWire.SignalWire` (`exports.SignalWire = SignalWire`, `dist/browser.umd.js:23874`). Also `window.SignalWire.StaticCredentialProvider` (`23875`), `TokenRefreshError`, `version` (`"4.0.0-rc.4"`), `ready` (true). Dependencies (rxjs, loglevel, jwt-decode) are bundled (no `require(` calls). It dispatches `window` event `signalwire:js:ready` with `detail.version` on load (`dist/browser.umd.js:23826-23832`) and polyfills `globalThis.process` if missing. `package.json` `unpkg`/`jsdelivr` point to `./dist/browser.umd.js`; ESM bundle `dist/browser.mjs` via `@signalwire/js/bundle`.

Playwright:
```js
await page.addScriptTag({ path: '<abs>/pkg/package/dist/browser.umd.js' });
await page.evaluate(async (sat) => {
  const { SignalWire, StaticCredentialProvider } = window.SignalWire;
  const client = new SignalWire(new StaticCredentialProvider({ token: sat }), { persistSession: false });
  client.session.incomingCalls$.subscribe(calls => { /* Call[] */ });
}, sat);
```
