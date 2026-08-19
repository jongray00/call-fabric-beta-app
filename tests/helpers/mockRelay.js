/**
 * Minimal mock of the SignalWire relay WebSocket endpoint.
 *
 * It implements just enough of the wire protocol for the real @signalwire/js
 * Fabric client to authenticate (`signalwire.connect`) and for us to observe /
 * control what the SDK does afterwards, so the push-notification behaviour of
 * the SDK can be asserted without a live SignalWire project.
 */
const { WebSocketServer } = require('ws')

const PROJECT_ID = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'

function connectResult() {
  return {
    identity: 'test@example.signalwire.com',
    authorization: {
      jti: 'test-jti',
      project_id: PROJECT_ID,
      fabric_subscriber: {
        version: 2,
        expires_at: Math.floor(Date.now() / 1000) + 3600,
        subscriber_id: 'subscriber-1',
        application_id: 'application-1',
        project_id: PROJECT_ID,
        space_id: 'space-1',
      },
    },
    protocol: 'signalwire_mock_proto',
    ice_servers: [],
  }
}

/**
 * @param {object} opts
 * @param {'success'|'error'|'hang'} opts.vertoMode how to answer `webrtc.verto`
 */
async function startMockRelay({ vertoMode = 'success' } = {}) {
  const wss = new WebSocketServer({ port: 0 })
  const requests = []
  const sockets = []
  let mode = vertoMode

  wss.on('connection', (ws) => {
    sockets.push(ws)
    ws.on('message', (raw) => {
      let msg
      try {
        msg = JSON.parse(raw.toString())
      } catch (e) {
        return
      }
      requests.push(msg)

      const reply = (result) =>
        ws.send(JSON.stringify({ jsonrpc: '2.0', id: msg.id, result }))
      const replyError = (error) =>
        ws.send(JSON.stringify({ jsonrpc: '2.0', id: msg.id, error }))

      switch (msg.method) {
        case 'signalwire.connect':
          return reply(connectResult())
        case 'signalwire.subscribe':
          return reply({ protocol: 'signalwire_mock_proto', channels: [] })
        case 'webrtc.verto':
          if (mode === 'success') return reply({ code: '200', message: 'OK' })
          if (mode === 'error')
            return replyError({ code: '404', message: 'Call not found' })
          return // 'hang' -> never answer, like a dead/stale node
        default:
          return reply({})
      }
    })
  })

  await new Promise((resolve) => wss.on('listening', resolve))
  const { port } = wss.address()

  return {
    /** `host` value to hand to the SignalWire client */
    host: `ws://127.0.0.1:${port}`,
    requests,
    setVertoMode: (m) => (mode = m),
    vertoRequests: () => requests.filter((r) => r.method === 'webrtc.verto'),
    methods: () => requests.map((r) => r.method),
    /** Push a server-initiated verto.invite, i.e. an inbound call over the WS */
    sendVertoInvite: (invite, nodeId = 'mock-node-id') => {
      const payload = {
        jsonrpc: '2.0',
        id: 'sw-event-' + Math.random().toString(36).slice(2),
        method: 'signalwire.event',
        params: {
          event_type: 'webrtc.message',
          node_id: nodeId,
          params: {
            jsonrpc: '2.0',
            id: 'verto-' + Math.random().toString(36).slice(2),
            method: 'verto.invite',
            params: invite,
          },
        },
      }
      sockets.forEach((s) => s.send(JSON.stringify(payload)))
    },
    close: () =>
      new Promise((resolve) => {
        sockets.forEach((s) => s.terminate())
        wss.close(resolve)
      }),
  }
}

/** A syntactically valid (unsigned) SAT-looking JWT. */
function fakeSubscriberToken() {
  const b64 = (o) => Buffer.from(JSON.stringify(o)).toString('base64url')
  return `${b64({ typ: 'SAT' })}.${b64({ sub: 'subscriber-1' })}.not-a-real-signature`
}

module.exports = { startMockRelay, fakeSubscriberToken }
