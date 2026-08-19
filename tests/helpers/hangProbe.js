/**
 * Standalone probe: what happens when `handlePushNotification` is given the raw
 * (still encrypted) payload SignalWire delivers, i.e. without the app decrypting
 * it first?
 *
 * Run out-of-process because the SDK leaks a TypeError as an unhandled
 * rejection, which the test runner would otherwise attribute to whichever test
 * happened to be running.
 *
 * Prints one JSON line: { outcome, unhandled }
 */
const { startMockRelay, fakeSubscriberToken } = require('./mockRelay')
const { buildEncryptedPushPayload } = require('./pushPayload')
const { SignalWire } = require('@signalwire/js')

const unhandled = []
process.on('unhandledRejection', (reason) =>
  unhandled.push(String((reason && reason.message) || reason))
)

;(async () => {
  const relay = await startMockRelay()
  const client = await SignalWire({
    token: fakeSubscriberToken(),
    host: relay.host,
    maxApiRequestRetries: 0,
  })

  const { payload } = buildEncryptedPushPayload()

  const outcome = await Promise.race([
    client
      .handlePushNotification(payload)
      .then(() => 'resolved')
      .catch(() => 'rejected'),
    new Promise((resolve) => setTimeout(() => resolve('pending'), 3000)),
  ])

  console.log(JSON.stringify({ outcome, unhandled }))
  process.exit(0)
})()
