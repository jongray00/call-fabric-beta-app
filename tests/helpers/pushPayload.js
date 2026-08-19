/**
 * Builds and reads SignalWire-shaped encrypted push-notification payloads.
 *
 * `readPushNotification` is a line-for-line port of the browser code in
 * `public/minimal.js` (AES-256-GCM + pako inflate, key = `push_notification_key`
 * returned by `client.registerDevice`), so the tests exercise the decrypt
 * scheme this repo actually ships, not an invented one.
 */
const nodeCrypto = require('crypto')
const pako = require('pako')

const subtle = globalThis.crypto.subtle

const INVITE_DEFAULTS = {
  callID: '11111111-2222-3333-4444-555555555555',
  sdp: 'v=0\r\no=- 0 0 IN IP4 127.0.0.1\r\ns=-\r\nc=IN IP4 127.0.0.1\r\nt=0 0\r\nm=audio 9 UDP/TLS/RTP/SAVPF 111\r\n',
  caller_id_name: 'USA Line Pro PSTN caller',
  caller_id_number: '+15551231234',
  callee_id_name: 'subscriber',
  callee_id_number: '/private/usa-line-pro',
  display_direction: 'inbound',
}

/**
 * @returns {{ payload: object, pnSecretKey: string, invite: object, nodeId: string }}
 *   `payload` has the same shape SignalWire delivers to the device
 *   (PushNotificationPayload), `pnSecretKey` is the base64 key that
 *   `registerDevice` returns.
 */
function buildEncryptedPushPayload({
  invite: inviteOverrides = {},
  nodeId = 'mock-node-id',
  type = 'call_invite',
} = {}) {
  const invite = { ...INVITE_DEFAULTS, ...inviteOverrides }
  const decryptedEnvelope = {
    jsonrpc: '2.0',
    id: 'verto-invite-1',
    node_id: nodeId,
    params: {
      method: 'verto.invite',
      params: invite,
    },
  }

  const key = nodeCrypto.randomBytes(32)
  const iv = nodeCrypto.randomBytes(12)
  const compressed = Buffer.from(pako.deflate(JSON.stringify(decryptedEnvelope)))

  const cipher = nodeCrypto.createCipheriv('aes-256-gcm', key, iv)
  const ciphertext = Buffer.concat([cipher.update(compressed), cipher.final()])
  const tag = cipher.getAuthTag()

  return {
    invite,
    nodeId,
    pnSecretKey: key.toString('base64'),
    payload: {
      encryption_type: 'aes_256_gcm',
      notification_uuid: 'ffffffff-0000-1111-2222-333333333333',
      with_video: 'false',
      incoming_caller_name: invite.caller_id_name,
      incoming_caller_id: invite.caller_id_number,
      title: 'Incoming call',
      type,
      version: '1',
      iv: iv.toString('base64'),
      invite: ciphertext.toString('base64'),
      tag: tag.toString('base64'),
    },
  }
}

/** Port of `readPushNotification()` from public/minimal.js */
async function readPushNotification(payload, pnSecretKey) {
  const b642ab = (b64) => Uint8Array.from(Buffer.from(b64, 'base64'))

  const key = b642ab(pnSecretKey)
  const iv = b642ab(payload.iv)

  // Chain invite and tag to have the full enc string
  const fullEncrypted = Buffer.concat([
    Buffer.from(payload.invite, 'base64'),
    Buffer.from(payload.tag, 'base64'),
  ])

  const cryptoKey = await subtle.importKey('raw', key, { name: 'AES-GCM' }, false, [
    'decrypt',
  ])
  const compressed = await subtle.decrypt(
    { name: 'AES-GCM', iv },
    cryptoKey,
    fullEncrypted
  )

  const result = pako.inflate(new Uint8Array(compressed), { to: 'string' })

  return { ...payload, decrypted: JSON.parse(result) }
}

module.exports = { buildEncryptedPushPayload, readPushNotification }
