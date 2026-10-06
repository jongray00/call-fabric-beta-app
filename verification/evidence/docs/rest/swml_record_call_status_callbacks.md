---
source: https://signalwire.com/docs/swml/reference/calling/record-call (docs:fern/products/swml/pages/reference/methods/calling/record_call.mdx)
retrieved_via: mcp__SignalWire_Knowledge__last_resort_search (collection signalwire_unified_v3)
fetched_at: 2026-10-06T15:22:36Z
note: StatusCallbacks section (record status payload, shared shape calling.call.record)
---

"A POST request will be sent to `status_url` with a JSON payload like the following:
- `event_type` (string): The type of event. Always `calling.call.record` for this method.
- `params.call_id`, `params.node_id`, `params.control_id`
- `params.state` (string): The current recording state. **Valid values:** `recording`, `paused`, `finished`, `no_input`, `error`.
- `params.url` (string): URL of the recorded media on `files.signalwire.com`. Present from the `recording` state onward.
- `params.recording_id` (string): ID of the recording, matching the `id` returned by the Recordings API.
- `params.duration` (integer): Recording duration in seconds. Present when the recording ends.
- `params.size` (integer) ...
- `params.pause_behavior` (string): How paused recording handles audio. Only present when `state` is `paused`. **Valid values:** `silence`, `skip`.
- `params.segment_id` (string): The call segment the recording belongs to.
- `record.audio.format` (string): Recording format. **Valid values:** `wav`, `mp3`, `mp4`.
- `record.audio.direction` (string): Direction of the audio recorded. **Valid values:** `speak`, `listen`, `both`.
- `record.audio.stereo` (boolean): Whether the recording was made in stereo mode."
