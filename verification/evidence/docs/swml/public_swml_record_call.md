---
source: "https://signalwire.com/docs/swml/reference/calling/record-call (record_call.mdx); https://signalwire.com/docs/platform/voice/record-calls"
retrieved_via: "mcp__SignalWire_Knowledge__search"
fetched_at: "2026-10-06T15:21:41Z"
note: "Verbatim chunk text as returned by the MCP vector search (signalwire_unified_v3 collection). Direct fetch of signalwire.com is blocked (403/EGRESS_BLOCKED)."
---

## record_call Properties

- `record_call.control_id` (string): Identifier for this recording, to use with [`stop_record_call`](/docs/swml/reference/calling/stop-record-call)
- `record_call.stereo` (boolean): Whether to record in stereo mode
- `record_call.format` (string): Format (`"wav"`, `"mp3"`, or `"mp4"`)
- `record_call.direction` (string): Direction of the audio to record: `"speak"` for what party says, `"listen"` for what party hears, `"both"` for what the party hears and says
- `record_call.terminators` (string): String of digits that will stop the recording when pressed. Default is empty (no terminators).
- `record_call.beep` (boolean): Whether to play a beep before recording
- `record_call.input_sensitivity` (number): [...] Allowed values from `0.0` to `100.0`.
- `record_call.initial_timeout` (number): How long, in seconds, to wait for speech to start?
- `record_call.end_silence_timeout` (number): How much silence, in seconds, will end the recording?
- `record_call.max_length` (number): Maximum length of the recording in seconds.
- `record_call.status_url` (string): HTTP or HTTPS URL to deliver record status events. Learn more about status callbacks.

## Variables

- **record_call_url:** (out) the URL of the newly started recording.
- **record_call_result:** (out) `success` | `failed`.
- **record_control_id:** (out) control ID of this recording.

## StatusCallbacks

A POST request will be sent to `status_url` with a JSON payload like the following:

- `event_type` (string): The type of event. Always `calling.call.record` for this method.
- `event_channel` (string): The channel for the event, includes the SWML session ID.
- `timestamp` (number): Unix timestamp (float) when the event was generated.
- `project_id` (string): The project ID associated with the call.
- `space_id` (string): The Space ID associated with the call.
- `params` (object): An object containing recording-specific parameters.
- `params.call_id` (string): The call ID.
- `params.node_id` (string): The node handling the call.
- `params.control_id` (string): The control ID for this record operation.
- `params.state` (string): The current recording state. **Valid values:** `recording`, `paused`, `finished`, `no_input`, `error`.
- `params.url` (string): URL of the recorded media on `files.signalwire.com`. Present from the `recording` state onward.
- `params.recording_id` (string): ID of the recording, matching the `id` returned by the Recordings API.
- `params.duration` (integer): Recording duration in seconds. Present when the recording ends.
- `params.size` (integer): Recording file size in bytes. Present when the recording ends.
- `params.start_time` (number): Unix timestamp (float) when the recording started. Present when the recording ends.
- `params.end_time` (number): Unix timestamp (float) when the recording ended. Present when the recording ends.
- `params.first_frame_time` (number): Unix timestamp (float) of the first recorded audio frame. Present when state is `finished`.
- `params.pause_behavior` (string): How paused recording handles audio. Only present when `state` is `paused`. **Valid values:** `silence`, `skip`.
- `params.segment_id` (string): The call segment the recording belongs to.
- `params.record` (object): The configuration the recording ran with.
- `record.audio.format` (string): Recording format. **Valid values:** `wav`, `mp3`, `mp4`.
- `record.audio.direction` (string): Direction of the audio recorded. **Valid values:** `speak`, `listen`, `both`.
- `record.audio.stereo` (boolean): Whether the recording was made in stereo mode.

## Platform guide: Receive recording status callbacks (record-calls)

You can set `status_url` on `record` or `record_call`, and SignalWire sends a POST request with a `calling.call.record` event as
the recording changes state. The `finished` event has `params.url`, `params.duration`, and
`params.size`. `params.recording_id` matches the `id` the Recordings API returns.

```json
{
  "event_type": "calling.call.record",
  "params": {
    "state": "finished",
    "record": { "audio": { "format": "wav", "direction": "speak", "stereo": false } },
    "url": "https://files.signalwire.com/<SPACE_ID>/<PROJECT_ID>/recordings/<RECORDING_ID>.wav",
    "recording_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "control_id": "main",
    "call_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "start_time": 1789651036.217461,
    "end_time": 1789651055.516839,
    "first_frame_time": 1789651036.219012,
    "size": 298284,
    "duration": 18
  }
}
```

## Stop recording the call via SWML (platform guide)

```yaml
version: 1.0.0
sections:
  main:
    - answer: {}
    - record_call:
        control_id: main
    - prompt:
        play: 'say:Tell us why you are calling, then press pound.'
        terminators: '#'
    - stop_record_call:
        control_id: main
    - play:
        url: 'say:Thanks. Connecting you now.'
```
