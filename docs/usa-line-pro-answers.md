# USA Line Pro — answers to the two Call Fabric questions, and corrections to the draft reply

Verified 2026-08-19 against **@signalwire/js 3.30.0** (the version the customer
reports running) and the official **SWML JSON schema**.

## How this was verified

| Area | Method | Result |
| --- | --- | --- |
| Question 1 (push / `registerDevice` / `handlePushNotification`) | 23 behavioural tests driving the real SDK build against a mock relay WebSocket (`tests/fabric-push-notification.test.js`, `tests/fabric-cold-start.test.js`) | all pass; several of the customer's and the draft's premises turn out to be wrong |
| Question 1 (browser sample) | This repository — SignalWire's own Call Fabric beta client (`public/minimal.js`, `public/full.js`, `views/service-worker.ejs`, `env.example`) | a working browser push path exists; the *closed-page* part does not |
| Question 2 (`connect.confirm`, `live_transcribe`) | 11 contract tests against the official SWML JSON schema (`tests/swml-connect-confirm.test.js`, `tests/fixtures/swml-schema.json`) + the SWML reference text | the customer's intended design is invalid; the draft's answer to Q2.1 is wrong |

Run everything with `npm test`.

**What could not be verified here, and is therefore marked "needs engineering":**

* Runtime carrier semantics for `connect.confirm` (ordering, guarantees, webhook
  identifiers). That needs a live project and a real PSTN call; no SignalWire
  credentials exist in this environment.
* The live docs pages (`developer.signalwire.com`, `docs.signalwire.com`,
  `signalwire.com/docs`) are blocked by this environment's network egress
  policy, so claims about *what the docs say* are not first-hand except where
  the vendored SWML reference/schema is quoted.
* Whether the server side officially supports web push targets in production,
  and which customers run it.

---

# Question 1 — browser / Call Fabric native Web Push for closed-page inbound calls

## First, the premise that has to be corrected

> "handlePushNotification … does not appear to require an already-active
> WebSocket as a hard prerequisite."

**This is false, and it is the load-bearing assumption of their build plan.**
Three independent reasons, each with a test:

1. **You cannot obtain a client without an authenticated WebSocket.**
   `SignalWire()` awaits `wsClient.connect()` before it resolves
   (`SignalWire.ts:36`). Against an unreachable relay it never resolves (it
   retries forever); against a relay that refuses `signalwire.connect` it
   rejects. Tests: *"never resolves while the relay is unreachable"*,
   *"rejects when the relay refuses signalwire.connect"*.
2. **`handlePushNotification` itself awaits an RPC on that socket.** It sends
   `verto.subscribe` and `await`s it before handing over the invite
   (`WSClient.ts:355`). With no ready session, `BaseSession.execute` **queues the
   request with no timeout** (`BaseSession.ts:333-337`), so the invite is never
   delivered. Test: *"never delivers the invite while the session is
   disconnected (RPC is queued, not failed)"*.
   If the node is reachable but silent, delivery is blocked for the full 10 s
   execute timeout **per retry**, and the SDK default is 10 retries
   (`DEFAULT_API_REQUEST_RETRIES = 10`) — i.e. the invite can surface >100 s
   late, long after the call is gone. Test: *"blocks invite delivery for the
   whole verto.subscribe timeout"*.
3. **Answering or rejecting the invite is also WebSocket work.** `reject()`
   sends `verto.bye` and `accept()` performs WebRTC signalling over the same
   session. Test: *"reject() on the delivered invite needs the WebSocket: it
   sends verto.bye"*.

What *is* true is narrower: if `verto.subscribe` returns an **error**, the SDK
logs a warning and still delivers the reconstructed invite
(`WSClient.ts:352-360`). Test: *"still delivers the invite when the
verto.subscribe RPC fails"*. That tolerance requires a live session in order to
receive the error at all — it is not a WebSocket-free path.

So the supported cold-start shape is: **push arrives → user taps → page opens →
create + authenticate the SignalWire client (fresh SAT, new WebSocket) →
decrypt the payload → `handlePushNotification(decrypted)` → `accept()`** — and
the inbound call has to still be ringing when that finishes. Nothing in the SDK
lets a closed page "hold" a live invitation.

## 1. Is provider-managed inbound Web Push supported for a browser with the page closed and no active Fabric WebSocket?

Two halves, two answers.

* **Browser web push as a delivery channel: yes, and it is not
  iOS/Android-native-only.** This repository is SignalWire's own Call Fabric
  beta client and it implements the browser path end to end: Firebase JS SDK +
  VAPID key + service worker (`views/service-worker.ejs`,
  `public/minimal.js:38-96`, `env.example` `FIREBASE_*`), `registerDevice`,
  payload decrypt, `handlePushNotification`, answer. The SDK contains no
  platform gating; `registerDevice` forwards whatever it is given (tests).
* **"With no active Fabric WebSocket": no.** See the premise correction above.
  The page must (re)connect and authenticate before the invitation can be
  delivered or answered.

The remaining piece — whether the platform's push fan-out to web/FCM targets is
**production-supported** (as opposed to beta-sample-supported) — is a product
answer, not an SDK one. That is the one part of Question 1 that genuinely needs
engineering.

## 2. Is `registerDevice({ deviceType, deviceToken })` the correct registration path, and what is `deviceToken` for a browser?

Yes, that is the path, and it is an HTTP call, not a WebSocket one:

* `POST https://fabric.<space-domain>/subscriber/devices`, body
  `{ device_type, device_token }`, `Authorization: Bearer <SAT>`
  (`HTTPClient.ts:120-134`). Tests: *"POSTs device_type/device_token verbatim to
  /subscriber/devices"*, *"registers over the Fabric REST API"*.
* Response: `{ id, device_name?, device_token, device_type, date_registered,
  push_notification_key }` (`interfaces/device.ts`).
* `deviceType` is one of **`iOS` | `Android` | `Desktop`** and is sent verbatim;
  the SDK has no browser-specific branch (test: *"sends iOS | Android | Desktop
  unchanged"*).

**What a browser should supply as `deviceToken`: an FCM Web registration token.**
The beta client does exactly this and is explicit about the device type:

```js
const token = await FB.getToken(messaging, { serviceWorkerRegistration: registration, vapidKey })
const { push_notification_key } = await client.registerDevice({
  deviceType: 'Android', // Use Android w/ Firebase on the web
  deviceToken: token,
})
```
(`public/minimal.js:83-95`, identical in `public/full.js:131-144`)

So: **not** a raw `PushSubscription` endpoint, **not** a SignalWire-issued
token — an FCM registration token obtained with your VAPID key, registered
under the `Android` device type because delivery goes through FCM. The space
therefore needs the same FCM (Android) credentials that the docs describe for
Android apps. `Desktop` is accepted by the SDK and the API, but the working
sample deliberately does not use it for the browser; whether `Desktop` is wired
to FCM server-side is worth one line of confirmation from engineering.

## 3. Does SignalWire send the complete encrypted payload (`type: "call_invite"`, `notification_uuid`, `invite`, `iv`, `encryption_type`, node/invitation data…)?

The payload the SDK expects is declared in `interfaces/wsClient.ts:63-76`:

```
encryption_type: 'aes_256_gcm'   notification_uuid   with_video
incoming_caller_name             incoming_caller_id  title
type: 'call_invite'              version             iv
invite                           tag                 decrypted
```

Two corrections to their list:

* **`tag` matters and they omitted it.** The AES-GCM auth tag ships as a
  separate base64 field; the app must concatenate `invite` + `tag` before
  decrypting (`public/minimal.js:140-152`). Ignoring it makes decryption fail.
* **There is no top-level node/invitation data.** `node_id` and the
  `verto.invite` parameters live *inside* the encrypted blob. After decryption
  the SDK reads `decrypted.node_id` and `decrypted.params.params`
  (`WSClient.ts:346-349`) — that inner object is the `IncomingInvite`
  (`callID`, `sdp`, `caller_id_name/number`, `callee_id_name/number`,
  `display_direction`).
* `decrypted` is **not** sent by SignalWire. It is the field *your code adds*.

## 4. How do you persist the decryption key, decrypt in a Service Worker, and hand the payload to the client?

**There is no SignalWire-supported mechanism for any of this. All of it is
application code.** Concretely, verified:

* `registerDevice` returns `push_notification_key` (base64 AES-256 key) and the
  SDK never reads it again. It does not decrypt anything: corrupting `iv`,
  `invite` and `tag` while leaving `decrypted` intact changes nothing (test:
  *"does NOT decrypt: it ignores the encrypted fields and uses `decrypted` as
  given"*).
* `handlePushNotification` requires an already-decrypted payload. Passing the raw
  payload straight through does **not** throw or reject — the promise **never
  settles** (the SDK destructures `decrypted` inside an async Promise executor,
  so the `TypeError` escapes as an unhandled rejection). Test: *"never settles
  when `decrypted` is missing"*. Validate before you call it.
* The beta sample keeps the key in a page-scoped variable
  (`public/minimal.js:2`, `:95`) and its service worker does **not** decrypt: it
  `postMessage`s the raw message to already-open clients and shows a
  notification (`views/service-worker.ejs`).

So the honest answer to "what is the officially supported way" is: none is
published. If they build it, the shape is theirs to own — service worker
persists the raw encrypted message (IndexedDB, or the notification's `data`),
`notificationclick` opens the page, the page fetches/reads the key (from
IndexedDB, or re-fetched from their backend at login) and decrypts with
WebCrypto `AES-GCM` + inflate, then calls `handlePushNotification`. Key-storage
hardening guidance is a security question for engineering; note the key is a
long-lived symmetric key tied to the device registration, and
`unregisterDevice` is how you retire it.

Two SDK gotchas they will hit here:

* You must pass `incomingCallHandler` to `handlePushNotification`, or the invite
  is delivered to nobody ("Skiping nottification due to no listeners",
  `IncomingCallManager.ts:82`). Tests: *"drops the invite silently when no
  handler was registered"*, *"DROPS a push-sourced invite when
  handlePushNotification is called without a handler, even after online()
  registered one"*.
* Calling it **wipes handlers registered via `online()`, including `all`**
  (`IncomingCallManager.ts:56`). Tests: *"overwrites an `all` handler previously
  registered through online()"*, *"delivers a push-sourced invite only to the
  handler passed to handlePushNotification"*. `public/full.js:569-570` relies on
  `all`, so that combination silently stops working.

## 5. Can a newly opened page call `handlePushNotification(...)` **without** `client.online()` / an already-active WebSocket?

* **Without `online()`: yes.** Verified: the invite is delivered with no
  `online()` call anywhere (test: *"delivers a reconstructed IncomingInvite from
  the decrypted payload, without client.online()"*). `online()` is for the
  WebSocket-delivered path, and the SDK even warns if you go online while
  registered for push (`WSClient.ts:389-393`).
* **Without an active WebSocket: no** — see the premise correction. Their
  reading of the source ("attempts the Verto subscription but continues") is
  correct only for a *failed* subscription on a live session, not for a missing
  session.

Also relevant to cold start: `SignalWire()` is a module-level singleton. A
second call returns the **same** client and ignores the newer token (test:
*"returns the SAME client for a second call, ignoring a newer token"*). Use
`client.updateToken(newSAT)` after a refresh instead of re-creating the client.

## 6. Is there an official Browser SDK example for the exact flow (page closed → push → tap → cold start → answer)?

**No.** The closest official artifact is this beta client, and it stops short of
exactly the part they care about: the service worker forwards to *open* clients
and shows a notification, with **no `notificationclick` handler, no persistence
of the encrypted payload, and no cold-start rehydration**
(`views/service-worker.ejs`). The `?inbound` query-string flow in
`public/minimal.js:172-180` assumes a page that is already open.

Also, the sample's own answer path is stale against 3.30.0 — see "Bugs in the
sample" below — so they should not copy it verbatim.

## 7. Is this production-supported for web (especially Chrome on Android), or is `registerDevice`/native push intended primarily for native apps? Any production customer doing it?

Not answerable from the SDK, and not answerable from here (docs egress blocked;
the internal knowledge corpus contains no push-notification guide). This is the
question to escalate. What can be said with evidence:

* The SDK path is **not** native-only: a SignalWire-authored browser sample
  exists, the device type union includes `Desktop`, and no code path branches on
  platform.
* The browser transport is FCM Web + VAPID + service worker, i.e. it inherits
  Chrome's rules for background push and closed-page wake-ups, and it does not
  work on iOS Safari the way VoIP push does on native iOS.
* "Production-supported" and "who runs it" need product/engineering
  confirmation, and customer references need approval before being shared.

---

# Question 2 — `connect.confirm` timing with `live_transcribe`

Everything below is verified against the official SWML schema
(`tests/fixtures/swml-schema.json`) and the SWML `connect` reference text.
Runtime ordering guarantees are flagged where they are not documented.

## 1. Does `connect.confirm` execute only after the B-leg has accepted and the bridge is established?

**Answered as asked: no — and this is the correction that matters most.**
The reference is explicit:

> **confirm:** SWML URL or inline compact SWML script … *script to execute on
> destination when answered. **Parent and destination are bridged after script
> completes execution.*** If more than one destination is dialed in parallel,
> the destination that completes the script first wins and is bridged to the
> parent.

So `confirm` runs **after the destination answers but *before* the bridge**, and
the bridge waits for `confirm` to finish. It is a pre-bridge seam, not a
post-bridge one. `confirm_timeout` bounds how long that is allowed to take.

## 2. If the destination returns no-answer / busy / declined / timeout, is `confirm` guaranteed not to execute?

By construction yes: the documented trigger is "on destination **when
answered**", so a destination that never answers never runs the script. The docs
do not state a guarantee, and say nothing about the edge cases they will
eventually hit (answered-then-immediately-dropped, early media/183, one leg of a
parallel dial answering while another fails). **Guarantee wording: needs
engineering.**

## 3. Can `confirm` contain `live_transcribe` inline, or should it point at a URL returning SWML?

**Inline: no — the schema forbids it.** `confirm` inline is typed as an array of
`ValidConfirmMethods`, which is a closed list:

`cond`, `set`, `unset`, `hangup`, `play`, `prompt`, `record`, `record_call`,
`stop_record_call`, `tap`, `stop_tap`, `send_digits`, `send_sms`, `denoise`,
`stop_denoise`

`live_transcribe` is not in it. A document with `confirm: [{ live_transcribe:
… }]` fails schema validation (tests: *"restricts inline confirm to a fixed
subset of SWML methods"*, *"REJECTS live_transcribe inline inside confirm"*).

**URL form: allowed by the schema** (`confirm` may be a string URL, with
`confirm_timeout`; test: *"ACCEPTS a confirm URL that returns SWML"*). Whether
the SWML *returned* by that URL may use `live_transcribe`, or whether the same
whitelist is enforced on the fetched document, is **not documented — needs
engineering**. Given the inline whitelist, assume it is restricted until
confirmed.

## 4. On which leg does a `live_transcribe` started from `confirm` run?

If it ran at all, it would run on the **destination / B-leg** — that is the leg
the confirm script executes on — and it would run **pre-bridge**. Not the PSTN
A-leg, and not "the bridged media session". `live_transcribe.action.start`
requires `lang` and `direction`, where `direction` is
`remote-caller` / `local-caller`, i.e. relative to the leg it runs on; there is
no `call_id` or leg selector (test: *"requires lang and direction on start, and
direction is per-leg-relative"*). **Runtime confirmation: needs engineering** —
and moot while (3) stands.

## 5. Which `call_id` arrives in the `ai-result` callback, and how should they correlate it to the inbound PSTN call?

Not documented. The SWML reference says `live_transcribe` parameters "are passed
through to the RELAY `live_transcribe` method" and does not specify the webhook
payload's identifiers, so the exact field set **needs engineering**. What can be
said: the id will be the leg the method ran on, which for a confirm-hosted
transcription is the B-leg — precisely the correlation problem they are
worried about.

Recommendation independent of the mechanism: **do not rely on the callback's own
id.** Carry your own correlation key — a query string on the webhook URL, or
SWML `set` variables — that contains the inbound A-leg call id, and use
`connect`'s `call_state_url` / `call_state_events`
(`created`/`ringing`/`answered`/`ended`) to map leg transitions back to the
parent call (test: *"exposes call_state_url/call_state_events"*).

## 6. Does adding `confirm` preserve `answer_on_bridge`? Can SignalWire guarantee `confirm` will not answer the A-leg before the B-leg accepts?

`confirm` executes on the destination leg, so it does not answer the A-leg, and
media inside it (`play`, `prompt`) is heard by the destination only. So the
failure mode they were burned by (`live_transcribe` before `connect` answering
the A-leg) does not recur through `confirm`.

The real risk with `confirm` is different and worth telling them: because the
bridge only happens **after** `confirm` completes, `confirm` adds latency
between B-answer and bridge, bounded by `confirm_timeout`, and a `confirm` that
fails or times out costs that destination the bridge. The precise interaction
with `answer_on_bridge` — whether the A-leg is answered at B-answer or at bridge
completion — is not documented. **Needs engineering.**

## 7. Is `confirm` the recommended mechanism for starting transcription only after a successful Fabric bridge?

**No.** Given the whitelist it cannot host `live_transcribe`, and semantically it
is pre-bridge on the wrong leg. Options that fit the documented surface today,
in the order I would recommend them:

1. **`answer_on_bridge: true` + `call_state_url` / `call_state_events:
   ["answered","ended"]`, then start transcription from outside SWML** via
   the RELAY real-time call control API on the A-leg once the destination
   answers. This keeps the voicemail path untouched, keeps the A-leg answer
   semantics unchanged, and gives them the A-leg call id for free. Test: *"the
   customer's target flow validates when transcription is started off
   call_state_url instead of confirm"*. The exact RELAY call to start live
   transcription on an in-progress call should be confirmed with engineering.
2. **`tap` (which *is* allowed inline in `confirm`) or `stream` on the A-leg**,
   streaming audio to their own ASR endpoint. They own the transcription and the
   correlation; nothing about `answer_on_bridge` changes. Test: *"ACCEPTS the
   media methods that are allowed inline in confirm"*. (`stream` is **not** in
   the confirm whitelist; `tap` is.)
3. **`record_call` + post-call transcription/summary** if "passive artifacts" can
   be produced after the fact rather than live. `record_call` is allowed in
   `confirm` and on the parent.

An example of `connect.confirm` with `live_transcribe` cannot be provided,
because that combination is not valid SWML.

---

# Everywhere the draft response is wrong

Numbered against the "Claude Responses" section of the PDF.

### Question 1 part of the draft

1. **"There's no documented path for standard browser Web Push (VAPID/service
   worker) as a `registerDevice` target."** — Misleading. SignalWire's own Call
   Fabric beta client implements exactly that path (Firebase JS SDK, VAPID key,
   service worker, `registerDevice`), and it is what the customer should be
   pointed at. The accurate statement is narrower: *there is no separate browser
   device type — the browser path goes through FCM Web, and it is demonstrated
   in the beta sample rather than in the docs.* (I could not read the live docs
   pages from this environment; the correction rests on the SignalWire-authored
   sample, which the draft did not consult.)
2. **"The `deviceType: "Desktop"` example … never specifies what a browser is
   supposed to supply there — FCM token, PushSubscription endpoint, or something
   SignalWire-issued."** — Presents a resolved question as unresolved. The
   answer is an **FCM Web registration token**, registered as
   `deviceType: 'Android'` (`public/minimal.js:83-95`, with the comment "Use
   Android w/ Firebase on the web"), and the SDK forwards the token verbatim
   (verified by test). Only "is `Desktop` also wired to FCM?" remains open.
3. **"That's a real gap, not just a documentation-reading issue on their end."**
   — Half right. The real gaps are (a) the **closed-page cold-start** flow and
   (b) **key persistence guidance**. There is no gap about what token to
   register or how to decrypt.
4. **It escalates all five numbered questions.** Four of the five are answerable
   today from the shipped SDK and sample: Q2 (registration path + token), Q3
   (payload fields — with the `tag` and "node data is inside the blob"
   corrections), Q5 (`online()` not required), and most of Q4 (the SDK provides
   no key handling at all; decryption is entirely app-side). Only Q1's
   production-support half is genuinely an engineering question.
5. **Biggest error: it silently accepts the customer's false premise.** The
   customer wrote that `handlePushNotification` "does not appear to require an
   already-active WebSocket as a hard prerequisite" and asked whether the
   continue-on-subscribe-failure behaviour is "intended for the browser
   cold-start Push use case". The draft never corrects this. It is false three
   times over (client creation connects and authenticates; the invite is gated
   behind an awaited `verto.subscribe` that is queued indefinitely without a
   session; answering needs the socket). The customer explicitly said they would
   choose an architecture based on the answer, so leaving this uncorrected is the
   most costly omission in the draft.
6. **It does not answer Q4 at all** (key persistence / service-worker decrypt /
   hand-off), not even to say "the SDK offers nothing here, it is all
   application code" — which is the actionable answer.
7. **It never mentions that the beta sample they will be pointed at is stale**
   against 3.30.0 (`resultObject` no longer returned, `all` handler wiped by
   `handlePushNotification`) — so following the draft's "let me get you the
   sample" instinct hands them broken code.

### Question 2 part of the draft

8. **"Docs confirm the basic mechanic: `connect.confirm` fires only once the
   B-leg has connected/bridged … That answers their Q1 in principle."** —
   **Wrong.** `confirm` fires when the destination **answers**, and the parent
   and destination are bridged **after the confirm script completes**. It is a
   pre-bridge hook. Answering their Q2.1 with "yes, post-bridge" would have them
   build on an incorrect model of the timing they are specifically trying to
   pin down.
9. **"(either a URL returning SWML, or inline SWML methods)"** — Incomplete in a
   way that matters: inline `confirm` accepts only a closed whitelist of 15
   methods, and **`live_transcribe` is not among them**. Their Q2.3 plan A is
   invalid SWML, and the draft implicitly blesses it.
10. **"which leg `live_transcribe` binds to when started from inside `confirm`
    … aren't spelled out anywhere I could find."** — The leg question *is*
    answerable from the docs: `confirm` executes on the **destination**, so
    anything started there runs on the B-leg pre-bridge, and
    `live_transcribe`'s `direction` enum is leg-relative. Likewise, "is
    no-answer/busy guaranteed to skip confirm" follows from "on destination when
    answered" (only the word *guaranteed* is unsupported).
11. **It omits the single most decision-relevant fact of Question 2** — that
    `live_transcribe` cannot go inside `confirm` — and instead defers the whole
    thread to engineering. The customer would have spent a build cycle producing
    a document that fails validation.
12. **It offers no alternative pattern.** Q2.7 asked "or is there another
    supported pattern you recommend?" The draft does not answer it, although
    `call_state_url` + RELAY, `tap`/`stream`, and `record_call` are all
    documented and schema-valid.
13. **"Bottom line: both threads warrant an engineering-confirmed answer rather
    than a best-guess reply."** — Right instinct, wrong scope. As written it
    withholds roughly a dozen answers that are verifiable today, and — worse —
    fails to warn the customer off two designs that provably do not work
    (WebSocket-less `handlePushNotification`; `live_transcribe` inside
    `confirm`). The correct reply answers what is verifiable, states the two
    designs that are dead, and escalates exactly three things: production
    support for web push targets, `confirm` runtime guarantees/webhook
    identifiers, and whether `Desktop` is FCM-backed.
14. **Unverifiable detail:** the draft dates the second question as "Email 2
    (Aug 18, 2:50 PM, same thread)". The provided PDF carries no such timestamp
    — it only says the question "came out of the same inbound-call work". Not
    necessarily wrong, but nothing in the source supports it.

---

# Bugs in this repo's sample that the customer will hit

Verified against 3.30.0; these are why the sample should not be copied as-is.

1. **`resultObject` no longer exists.** `public/minimal.js:112` and
   `public/full.js:165` destructure `{ resultType, resultObject }` from
   `handlePushNotification`. 3.30.0 resolves with `{ resultType: 'inboundCall' }`
   only (`WSClient.ts:366`, and `HandlePushNotificationResult` has a single
   field), so `resultObject` is `undefined`, `window.__call = undefined`, and
   `window.__call.on('destroy', …)` throws. In 3.30.0 the call object arrives
   through the `incomingCallHandler` / `online()` handlers as
   `notification.invite.accept(params)`.
2. **`alert(body.title)` references an undefined variable** in
   `public/full.js:95` and `:103` (and `public/minimal.js:54` only works because
   `body` is assigned two lines earlier). In `full.js` the parsed object is
   `message`, so this throws inside the push handler.
3. **`incomingCallHandlers.all` is silently dropped.** `public/full.js:569-570`
   registers `{ all: … }`, but any later `handlePushNotification` call resets the
   `all` slot (`IncomingCallManager.ts:56`, verified by test).
4. **`registerDevice` + `online()` together.** `public/full.js:141-148` registers
   for push and then goes online; the SDK itself warns "Make sure the device is
   not registered to receive Push Notifications while it is online"
   (`WSClient.ts:389-393`).
5. **The service worker cannot support the closed-page flow.**
   `views/service-worker.ejs` only `postMessage`s to open clients and shows a
   notification: no `notificationclick`, no persistence of the encrypted
   payload, no cold-start hand-off.
6. **`pako` version trap.** The decrypt path uses `pako.inflate(data, { to:
   'string' })`, which the views pin to pako 2.1.0. pako 3.x removed the
   `to: 'string'` option — verified here: under pako 3.0.1 the same call returns
   a `Uint8Array` and `JSON.parse` fails. Keep the pin, or decode explicitly.

---

# Escalate exactly this

1. Is push delivery to **web/FCM device tokens** production-supported for Call
   Fabric subscribers, and is `deviceType: 'Desktop'` FCM-backed or reserved for
   something else?
2. Is there any supported way for a **closed** browser page to hold a Fabric
   invitation until the user taps the notification, beyond "reconnect fast and
   hope the call is still ringing"? What is the recommended lifetime/storage
   posture for `push_notification_key`?
3. For SWML: may a `confirm` **URL** return a document containing
   `live_transcribe` (or is the whitelist enforced there too)? Is a
   **post-bridge** hook planned? Is `confirm` guaranteed to be skipped on every
   connect failure, and which call id appears in the `live_transcribe` webhook?
