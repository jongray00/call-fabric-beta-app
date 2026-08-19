/**
 * Behavioural verification of the Call Fabric push-notification API in
 * @signalwire/js 3.30.0 -- the version USA Line Pro reports using.
 *
 * Every test here asserts a specific claim made in the customer's questions
 * (or in the draft answer to them), against the real SDK build talking to a
 * mock relay WebSocket. Nothing is stubbed inside the SDK.
 */
const { SignalWire } = require('@signalwire/js')
const { startMockRelay, fakeSubscriberToken } = require('./helpers/mockRelay')
const {
  buildEncryptedPushPayload,
  readPushNotification,
} = require('./helpers/pushPayload')

jest.setTimeout(60000)

const EXECUTE_TIMEOUT_MS = 10000 // BaseSession._executeTimeoutMs

let relay
let client

async function createClient(overrides = {}) {
  client = await SignalWire({
    token: fakeSubscriberToken(),
    host: relay.host,
    // keep retries short: the SDK default is 10 retries of a 10s timeout
    maxApiRequestRetries: 0,
    ...overrides,
  })
  return client
}

/** Resolve with the first notification delivered to `handler`, or null on timeout. */
function collector(timeoutMs = 3000) {
  let resolveFn
  const promise = new Promise((resolve) => (resolveFn = resolve))
  const calls = []
  const handler = (notification) => {
    calls.push(notification)
    resolveFn(notification)
  }
  return {
    handler,
    calls,
    first: () =>
      Promise.race([
        promise,
        new Promise((resolve) => setTimeout(() => resolve(null), timeoutMs)),
      ]),
  }
}

beforeEach(async () => {
  relay = await startMockRelay()
})

afterEach(async () => {
  if (client) {
    // `disconnect()` only resolves on a `session.disconnected` event, which
    // never arrives if the relay is already gone -- so cap the wait.
    await Promise.race([
      client.disconnect().catch(() => {}),
      new Promise((r) => setTimeout(r, 2000)),
    ])
    client = null
  }
  await relay.close()
})

describe('SDK surface the customer reports finding (their premise)', () => {
  it('exposes registerDevice / handlePushNotification / online / offline', async () => {
    await createClient()

    expect(typeof client.registerDevice).toBe('function')
    expect(typeof client.unregisterDevice).toBe('function')
    expect(typeof client.handlePushNotification).toBe('function')
    expect(typeof client.online).toBe('function')
    expect(typeof client.offline).toBe('function')
  })

  it('creating the client already opens and authenticates a WebSocket', async () => {
    await createClient()

    // The client cannot exist without a completed `signalwire.connect`.
    expect(relay.methods()).toContain('signalwire.connect')
  })
})

describe('registerDevice (Q1.2 - what does a browser register?)', () => {
  it('POSTs device_type/device_token verbatim to /subscriber/devices', async () => {
    await createClient()

    // Intercept the SDK's internal HTTP client so we see exactly what
    // registerDevice sends, without needing the Fabric REST API.
    const calls = []
    client.__httpClient.httpClient = async (path, options) => {
      calls.push({ path, options })
      return {
        body: {
          id: 'device-1',
          device_type: 'Desktop',
          device_token: 'whatever-we-sent',
          date_registered: new Date().toISOString(),
          push_notification_key: Buffer.alloc(32, 7).toString('base64'),
        },
      }
    }

    const result = await client.registerDevice({
      deviceType: 'Desktop',
      deviceToken: 'fcm-web-registration-token-or-anything-else',
    })

    expect(calls).toHaveLength(1)
    expect(calls[0].path).toBe('/subscriber/devices')
    expect(calls[0].options.method).toBe('POST')
    // The SDK does not transform, validate or derive the token: whatever the
    // app supplies is forwarded as-is. "What belongs here for a browser" is a
    // provisioning question about the push provider, not an SDK question.
    expect(calls[0].options.body).toEqual({
      device_type: 'Desktop',
      device_token: 'fcm-web-registration-token-or-anything-else',
    })
    expect(typeof result.push_notification_key).toBe('string')
  })

  it('sends iOS | Android | Desktop unchanged - the SDK has no browser-specific branch', async () => {
    await createClient()

    const sent = []
    client.__httpClient.httpClient = async (_path, options) => {
      sent.push(options.body.device_type)
      return { body: { push_notification_key: 'a2V5' } }
    }

    for (const deviceType of ['iOS', 'Android', 'Desktop']) {
      await client.registerDevice({ deviceType, deviceToken: 'tok' })
    }

    expect(sent).toEqual(['iOS', 'Android', 'Desktop'])
  })

  it('registers over the Fabric REST API (fabric.<space-domain>), not the WebSocket', async () => {
    await createClient()

    const httpClient = client.__httpClient
    httpClient.options.host = 'example.signalwire.com'
    expect(httpClient.httpHost).toBe('fabric.signalwire.com')
    httpClient.options.host = 'puc.swire.io'
    expect(httpClient.httpHost).toBe('fabric.swire.io')

    expect(relay.methods()).not.toContain('subscriber.devices')
  })
})

describe('handlePushNotification (Q1.3, Q1.4, Q1.5)', () => {
  it('does NOT decrypt: it ignores the encrypted fields and uses `decrypted` as given', async () => {
    await createClient()

    const { payload, pnSecretKey, invite } = buildEncryptedPushPayload()
    const decryptedPayload = await readPushNotification(payload, pnSecretKey)

    const pn = collector()
    await client.handlePushNotification({
      ...decryptedPayload,
      // Corrupt every encrypted field. If the SDK decrypted anything, this
      // would fail; it does not, so the invite is still delivered.
      iv: 'AAAAAAAAAAAAAAAA',
      invite: 'bm90LWEtY2lwaGVydGV4dA==',
      tag: 'AAAAAAAAAAAAAAAAAAAAAA==',
      incomingCallHandler: pn.handler,
    })

    const notification = await pn.first()
    expect(notification).not.toBeNull()
    expect(notification.invite.details.callID).toBe(invite.callID)
  })

  it('never settles when `decrypted` is missing (raw push payload passed straight in)', () => {
    // Out-of-process: the SDK throws inside an async Promise executor, so the
    // TypeError escapes as an unhandled rejection instead of rejecting the
    // promise it returned.
    const { execFileSync } = require('child_process')
    const out = execFileSync(
      process.execPath,
      [require.resolve('./helpers/hangProbe.js')],
      { encoding: 'utf8', timeout: 30000 }
    )
    const { outcome, unhandled } = JSON.parse(out.trim().split('\n').pop())

    expect(outcome).toBe('pending')
    expect(unhandled.join(' ')).toMatch(/destructure property 'params' of 'decrypted'/)
  })

  it('delivers a reconstructed IncomingInvite from the decrypted payload, without client.online()', async () => {
    await createClient()

    const { payload, pnSecretKey, invite, nodeId } = buildEncryptedPushPayload()
    const decryptedPayload = await readPushNotification(payload, pnSecretKey)

    const pn = collector()
    const result = await client.handlePushNotification({
      ...decryptedPayload,
      incomingCallHandler: pn.handler,
    })

    expect(result).toEqual({ resultType: 'inboundCall' })
    // NOTE: 3.30.0 returns no `resultObject` -- the sample code in this repo
    // destructures one and gets `undefined`.
    expect(result.resultObject).toBeUndefined()

    const notification = await pn.first()
    expect(notification).not.toBeNull()
    expect(notification.invite.details).toMatchObject({
      callID: invite.callID,
      caller_id_number: invite.caller_id_number,
      caller_id_name: invite.caller_id_name,
      sdp: invite.sdp,
      nodeId,
    })
    expect(typeof notification.invite.accept).toBe('function')
    expect(typeof notification.invite.reject).toBe('function')
  })

  it('rejects any notification whose type is not "call_invite"', async () => {
    await createClient()

    const { payload, pnSecretKey } = buildEncryptedPushPayload({
      type: 'not_a_call_invite',
    })
    const decryptedPayload = await readPushNotification(payload, pnSecretKey)

    await expect(
      client.handlePushNotification({
        ...decryptedPayload,
        incomingCallHandler: () => {},
      })
    ).rejects.toBe('Unknown notification type')
  })

  it('still delivers the invite when the verto.subscribe RPC fails (their claim confirmed)', async () => {
    relay.setVertoMode('error')
    await createClient()

    const { payload, pnSecretKey, invite } = buildEncryptedPushPayload()
    const decryptedPayload = await readPushNotification(payload, pnSecretKey)

    const pn = collector()
    await client.handlePushNotification({
      ...decryptedPayload,
      incomingCallHandler: pn.handler,
    })

    const notification = await pn.first()
    expect(notification).not.toBeNull()
    expect(notification.invite.details.callID).toBe(invite.callID)
    // The subscribe really was attempted, and really did fail.
    expect(relay.vertoRequests().length).toBeGreaterThan(0)
  })

  it('drops the invite silently when no handler was registered', async () => {
    await createClient()

    const { payload, pnSecretKey } = buildEncryptedPushPayload()
    const decryptedPayload = await readPushNotification(payload, pnSecretKey)

    const warn = jest.spyOn(client.__wsClient.logger, 'warn')
    // no incomingCallHandler, no prior online()
    const result = await client.handlePushNotification(decryptedPayload)

    expect(result).toEqual({ resultType: 'inboundCall' })
    expect(
      warn.mock.calls.flat().join(' ')
    ).toMatch(/no listeners/i)
    warn.mockRestore()
  })

  it('overwrites an `all` handler previously registered through online()', async () => {
    await createClient()

    const all = collector()
    const pn = collector()
    await client.online({ incomingCallHandlers: { all: all.handler } })

    const { payload, pnSecretKey } = buildEncryptedPushPayload()
    const decryptedPayload = await readPushNotification(payload, pnSecretKey)

    await client.handlePushNotification({
      ...decryptedPayload,
      incomingCallHandler: pn.handler,
    })

    expect(await pn.first()).not.toBeNull()
    // setNotificationHandlers() unconditionally reassigns `all`, so the handler
    // installed by online() is silently dropped.
    expect(await all.first(500)).toBeNull()
    expect(all.calls).toHaveLength(0)
  })

  it('de-duplicates repeated notifications for the same callID', async () => {
    await createClient()

    const { payload, pnSecretKey } = buildEncryptedPushPayload()
    const decryptedPayload = await readPushNotification(payload, pnSecretKey)

    const pn = collector()
    await client.handlePushNotification({
      ...decryptedPayload,
      incomingCallHandler: pn.handler,
    })
    await pn.first()
    await client.handlePushNotification({
      ...decryptedPayload,
      incomingCallHandler: pn.handler,
    })
    await new Promise((r) => setTimeout(r, 300))

    expect(pn.calls).toHaveLength(1)
  })

  it('reject() on the delivered invite needs the WebSocket: it sends verto.bye', async () => {
    await createClient()

    const { payload, pnSecretKey, invite } = buildEncryptedPushPayload()
    const decryptedPayload = await readPushNotification(payload, pnSecretKey)

    const pn = collector()
    await client.handlePushNotification({
      ...decryptedPayload,
      incomingCallHandler: pn.handler,
    })
    const notification = await pn.first()
    await notification.invite.reject()

    const byes = relay
      .vertoRequests()
      .filter((r) => r.params?.message?.method === 'verto.bye')
    expect(byes).toHaveLength(1)
    expect(byes[0].params.callID).toBe(invite.callID)
  })
})

describe('incomingCallHandlers routing (websocket vs pushNotification)', () => {
  it('routes a WebSocket verto.invite to the `websocket` handler only, after online()', async () => {
    await createClient()

    const ws = collector()
    const pn = collector()
    await client.online({
      incomingCallHandlers: { websocket: ws.handler, pushNotification: pn.handler },
    })
    expect(relay.methods()).toContain('subscriber.online')

    relay.sendVertoInvite({
      callID: 'aaaa-websocket-call',
      sdp: 'v=0\r\n',
      caller_id_name: 'PSTN caller',
      caller_id_number: '+15550001111',
      callee_id_name: 'subscriber',
      callee_id_number: '/private/usa-line-pro',
      display_direction: 'inbound',
    })

    const notification = await ws.first(5000)
    expect(notification).not.toBeNull()
    expect(notification.invite.details.callID).toBe('aaaa-websocket-call')
    expect(notification.invite.details.nodeId).toBe('mock-node-id')
    expect(pn.calls).toHaveLength(0)
  })

  it('DROPS a push-sourced invite when handlePushNotification is called without a handler, even after online() registered one', async () => {
    await createClient()

    const all = collector()
    const ws = collector()
    const pn = collector()
    await client.online({
      incomingCallHandlers: {
        all: all.handler,
        websocket: ws.handler,
        pushNotification: pn.handler,
      },
    })

    const { payload, pnSecretKey } = buildEncryptedPushPayload()
    const decryptedPayload = await readPushNotification(payload, pnSecretKey)
    // No `incomingCallHandler` in the params.
    await client.handlePushNotification(decryptedPayload)

    // setNotificationHandlers({ pushNotification: undefined }) clears all three
    // handler slots, so the invite is delivered to nobody.
    expect(await pn.first(1000)).toBeNull()
    expect(await all.first(500)).toBeNull()
    expect(ws.calls).toHaveLength(0)
  })

  it('delivers a push-sourced invite only to the handler passed to handlePushNotification', async () => {
    await createClient()

    const all = collector()
    const ws = collector()
    const pn = collector()
    await client.online({
      incomingCallHandlers: { all: all.handler, websocket: ws.handler },
    })

    const { payload, pnSecretKey } = buildEncryptedPushPayload()
    const decryptedPayload = await readPushNotification(payload, pnSecretKey)
    await client.handlePushNotification({
      ...decryptedPayload,
      incomingCallHandler: pn.handler,
    })

    expect(await pn.first()).not.toBeNull()
    expect(await all.first(500)).toBeNull()
    expect(ws.calls).toHaveLength(0)
  })
})

describe('the WebSocket is a hard prerequisite (Q1.1, Q1.5)', () => {
  it('blocks invite delivery for the whole verto.subscribe timeout when the node does not answer', async () => {
    relay.setVertoMode('hang')
    await createClient()

    const { payload, pnSecretKey } = buildEncryptedPushPayload()
    const decryptedPayload = await readPushNotification(payload, pnSecretKey)

    const pn = collector(EXECUTE_TIMEOUT_MS * 2)
    const started = Date.now()
    await client.handlePushNotification({
      ...decryptedPayload,
      incomingCallHandler: pn.handler,
    })
    const notification = await pn.first()
    const elapsed = Date.now() - started

    expect(notification).not.toBeNull()
    // handlePushNotification awaits verto.subscribe before it hands the invite
    // over, so delivery is delayed by the execute timeout (10s), once per
    // retry -- 10 retries by SDK default.
    expect(elapsed).toBeGreaterThanOrEqual(EXECUTE_TIMEOUT_MS - 500)
  })

  it('never delivers the invite while the session is disconnected (RPC is queued, not failed)', async () => {
    await createClient()

    const { payload, pnSecretKey } = buildEncryptedPushPayload()
    const decryptedPayload = await readPushNotification(payload, pnSecretKey)

    // Take the relay away: this is the "page cold-started, nothing connected"
    // situation the customer is asking about.
    await relay.close()
    await new Promise((r) => setTimeout(r, 500))

    const pn = collector(6000)
    client
      .handlePushNotification({
        ...decryptedPayload,
        incomingCallHandler: pn.handler,
      })
      .catch(() => {})

    expect(await pn.first()).toBeNull()
    expect(pn.calls).toHaveLength(0)
  })
})
