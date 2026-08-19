/**
 * Cold-start prerequisites for the "page was closed, user taps the
 * notification" flow in Question 1.
 *
 * `SignalWire()` memoises its client in module scope, and a pending/failed
 * creation stays cached, so every case here loads a fresh copy of the SDK.
 */
const { startMockRelay, fakeSubscriberToken } = require('./helpers/mockRelay')
const { WebSocketServer } = require('ws')

jest.setTimeout(40000)

/** A fresh copy of the SDK module, so the SignalWire() singleton is empty. */
function freshSignalWire() {
  let mod
  jest.isolateModules(() => {
    mod = require('@signalwire/js')
  })
  return mod.SignalWire
}

const withTimeout = (promise, ms) =>
  Promise.race([
    promise
      .then((value) => ({ settled: 'resolved', value }))
      .catch((error) => ({ settled: 'rejected', error })),
    new Promise((resolve) => setTimeout(() => resolve({ settled: 'pending' }), ms)),
  ])

async function deadHost() {
  // Bind and release a port, so the address is routable but nothing answers.
  const probe = new WebSocketServer({ port: 0 })
  await new Promise((r) => probe.on('listening', r))
  const { port } = probe.address()
  await new Promise((r) => probe.close(r))
  return `ws://127.0.0.1:${port}`
}

describe('a client cannot exist without a reachable relay (Q1.1 / Q1.5)', () => {
  it('never resolves while the relay is unreachable: no client, so no handlePushNotification', async () => {
    const SignalWire = freshSignalWire()
    const host = await deadHost()

    const outcome = await withTimeout(
      SignalWire({ token: fakeSubscriberToken(), host }),
      6000
    )

    expect(outcome.settled).toBe('pending')
  })
})

describe('a client cannot exist without a subscriber token the relay accepts', () => {
  let wss
  let sockets = []

  afterEach(async () => {
    // The SDK keeps reconnecting after an auth error, so sockets must be
    // terminated before the server will close.
    sockets.forEach((s) => s.terminate())
    sockets = []
    if (wss) await new Promise((r) => wss.close(r))
    wss = null
  })

  it('rejects when the relay refuses signalwire.connect (expired / invalid SAT)', async () => {
    const SignalWire = freshSignalWire()

    wss = new WebSocketServer({ port: 0 })
    wss.on('connection', (ws) => {
      sockets.push(ws)
      ws.on('message', (raw) => {
        const msg = JSON.parse(raw.toString())
        ws.send(
          JSON.stringify({
            jsonrpc: '2.0',
            id: msg.id,
            error: { code: -32002, message: 'Authentication failure' },
          })
        )
      })
    })
    await new Promise((r) => wss.on('listening', r))
    const { port } = wss.address()

    const outcome = await withTimeout(
      SignalWire({ token: fakeSubscriberToken(), host: `ws://127.0.0.1:${port}` }),
      20000
    )

    expect(outcome.settled).toBe('rejected')
  })
})

describe('the happy path needs both, and the client is a singleton', () => {
  it('resolves once a relay authenticates the token', async () => {
    const SignalWire = freshSignalWire()
    const relay = await startMockRelay()

    try {
      const outcome = await withTimeout(
        SignalWire({ token: fakeSubscriberToken(), host: relay.host }),
        10000
      )
      expect(outcome.settled).toBe('resolved')
      expect(relay.methods()).toContain('signalwire.connect')
      await Promise.race([
        outcome.value.disconnect().catch(() => {}),
        new Promise((r) => setTimeout(r, 2000)),
      ])
    } finally {
      await relay.close()
    }
  })

  it('returns the SAME client for a second call, ignoring a newer token', async () => {
    const SignalWire = freshSignalWire()
    const relay = await startMockRelay()

    try {
      const first = await SignalWire({
        token: fakeSubscriberToken(),
        host: relay.host,
      })
      const second = await SignalWire({
        token: fakeSubscriberToken() + '-refreshed',
        host: relay.host,
      })

      // Only one authentication happened: a cold-started page that re-creates
      // the client with a refreshed SAT keeps the first one. Use
      // client.updateToken() instead.
      expect(second).toBe(first)
      expect(relay.methods().filter((m) => m === 'signalwire.connect')).toHaveLength(1)

      await Promise.race([
        first.disconnect().catch(() => {}),
        new Promise((r) => setTimeout(r, 2000)),
      ])
    } finally {
      await relay.close()
    }
  })
})
