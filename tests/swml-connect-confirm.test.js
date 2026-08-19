/**
 * Verification of the Question 2 claims about `connect.confirm` +
 * `live_transcribe`, against the official SWML JSON schema
 * (tests/fixtures/swml-schema.json, retrieved from SignalWire's SWML schema
 * source on 2026-08-19).
 *
 * IMPORTANT SCOPE NOTE: this is a *schema/contract* level verification. Runtime
 * carrier semantics (does confirm run before or after the bridge, which leg a
 * method binds to, which call_id shows up in a webhook) cannot be verified from
 * here -- they need a live SignalWire project and a real PSTN call. The tests
 * below therefore only assert what the published contract actually says, and the
 * accompanying answer document marks everything else as unverified.
 */
const Ajv = require('ajv/dist/2020')
const schema = require('./fixtures/swml-schema.json')

const ajv = new Ajv({ strict: false, allErrors: true })
const validate = ajv.compile(schema)

const doc = (...instructions) => ({
  version: '1.0.0',
  sections: { main: instructions },
})

const LIVE_TRANSCRIBE = {
  live_transcribe: {
    action: {
      start: {
        lang: 'en-US',
        direction: ['remote-caller', 'local-caller'],
        webhook: 'https://example.com/ai-result',
        ai_summary: true,
      },
    },
  },
}

function errorsFor(instance) {
  return validate(instance) ? [] : validate.errors
}

describe('connect.confirm contract', () => {
  it('exists on every connect dial algorithm, as a URL string or an inline method array', () => {
    for (const def of [
      'ConnectDeviceSingle',
      'ConnectDeviceSerial',
      'ConnectDeviceParallel',
      'ConnectDeviceSerialParallel',
    ]) {
      const confirm = schema.$defs[def].properties.confirm
      expect(confirm.anyOf).toEqual([
        { type: 'string' },
        { type: 'array', items: { $ref: '#/$defs/ValidConfirmMethods' } },
      ])
      expect(schema.$defs[def].properties.confirm_timeout).toBeDefined()
    }
  })

  it('restricts inline confirm to a fixed subset of SWML methods', () => {
    const allowed = schema.$defs.ValidConfirmMethods.anyOf.map((r) =>
      r.$ref.replace('#/$defs/', '')
    )

    expect(allowed).toEqual([
      'Cond',
      'Set',
      'Unset',
      'Hangup',
      'Play',
      'Prompt',
      'Record',
      'RecordCall',
      'StopRecordCall',
      'Tap',
      'StopTap',
      'SendDigits',
      'SendSMS',
      'Denoise',
      'StopDenoise',
    ])
    // The method the customer wants to put there is not in the list.
    expect(allowed).not.toContain('LiveTranscribe')
  })

  it('REJECTS live_transcribe inline inside confirm (their Q2.3 plan A)', () => {
    const errors = errorsFor(
      doc({
        connect: {
          to: '/private/usa-line-pro',
          answer_on_bridge: true,
          confirm: [LIVE_TRANSCRIBE],
        },
      })
    )

    expect(errors.length).toBeGreaterThan(0)
    expect(JSON.stringify(errors)).toMatch(/confirm/)
  })

  it('ACCEPTS a confirm URL that returns SWML (their Q2.3 plan B)', () => {
    expect(
      errorsFor(
        doc({
          connect: {
            to: '/private/usa-line-pro',
            answer_on_bridge: true,
            confirm: 'https://example.com/confirm.swml',
            confirm_timeout: 30,
          },
        })
      )
    ).toEqual([])
  })

  it('ACCEPTS the media methods that are allowed inline in confirm', () => {
    expect(
      errorsFor(
        doc({
          connect: {
            to: '/private/usa-line-pro',
            answer_on_bridge: true,
            confirm: [
              { play: { url: 'silence:1' } },
              { record_call: { stereo: true, format: 'mp3' } },
              { tap: { uri: 'wss://example.com/tap', direction: 'both' } },
            ],
          },
        })
      )
    ).toEqual([])
  })
})

describe('live_transcribe contract', () => {
  it('is valid as a top-level method in main (so placement, not the method, is the question)', () => {
    expect(errorsFor(doc(LIVE_TRANSCRIBE))).toEqual([])
  })

  it('requires lang and direction on start, and direction is per-leg-relative', () => {
    const start = schema.$defs.TranscribeStartAction.properties.start
    expect(start.required).toEqual(expect.arrayContaining(['lang', 'direction']))
    expect(schema.$defs.TranscribeDirection.enum).toEqual([
      'remote-caller',
      'local-caller',
    ])
    // No "call leg" selector exists: the method binds to the call it runs on.
    expect(Object.keys(start.properties)).not.toContain('call_id')
    expect(Object.keys(start.properties)).not.toContain('leg')
  })

  it('has no parameter to defer its start until a bridge is established', () => {
    const start = schema.$defs.TranscribeStartAction.properties.start
    const names = Object.keys(start.properties).join(' ')
    expect(names).not.toMatch(/bridge|on_answer|delay|wait/)
  })
})

describe('answer_on_bridge and connect results', () => {
  it('answer_on_bridge is a connect parameter on all dial algorithms', () => {
    for (const def of [
      'ConnectDeviceSingle',
      'ConnectDeviceSerial',
      'ConnectDeviceParallel',
      'ConnectDeviceSerialParallel',
    ]) {
      expect(schema.$defs[def].properties.answer_on_bridge).toBeDefined()
    }
  })

  it('exposes call_state_url/call_state_events, the documented post-answer hook', () => {
    const single = schema.$defs.ConnectDeviceSingle.properties
    expect(single.call_state_url).toBeDefined()
    expect(single.call_state_events).toBeDefined()
    const events = JSON.stringify(single.call_state_events)
    for (const ev of ['created', 'ringing', 'answered', 'ended']) {
      expect(events).toContain(ev)
    }
  })

  it('the customer\'s target flow validates when transcription is started off call_state_url instead of confirm', () => {
    expect(
      errorsFor(
        doc(
          {
            connect: {
              answer_on_bridge: true,
              to: '/private/usa-line-pro',
              call_state_url: 'https://example.com/call-state',
              call_state_events: ['answered', 'ended'],
            },
          },
          { play: { url: 'say:Please leave a message' } },
          { record: {} }
        )
      )
    ).toEqual([])
  })
})
