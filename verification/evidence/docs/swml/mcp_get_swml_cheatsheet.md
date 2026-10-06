---
source: "MCP tool mcp__SignalWire_Knowledge__get_swml(doc='cheatsheet')"
fetched_at: "2026-10-06T15:21:41Z"
---

## Play URL Schemes (verbatim)

| Scheme | Example | Description |
|--------|---------|-------------|
| `https://` | `https://cdn.example.com/audio.mp3` | Play audio file |
| `say:` | `say:Hello caller` | Text-to-speech |
| `silence:` | `silence:2.0` | Silence in seconds |
| `ring:` | `ring:us` or `ring:20.0:us` | Ring tone (optional duration) |

### play
```yaml
- play:
    urls: ["say:Hello", "https://example.com/audio.mp3"]
    volume: 10          # -40.0 to 40.0
    say_voice: Polly.Matthew
    say_language: en-US
    loop: 0             # 0 = loop forever
```

### connect
```yaml
- connect:
    to: "+15559876543"        # single destination
    from: "+15551230000"
    timeout: 30
    # OR serial: [{to: "..."}, {to: "..."}]
    # OR parallel: [{to: "..."}, {to: "..."}]
    # OR serial_parallel: [[{to: "..."}], [{to: "..."}]]
    result:
      case:
        connected: [hangup]
      default:
        - play: "say:No answer"
```
Output vars: `connect_result` (connected|failed), `connect_failed_reason`

### record
```yaml
- record:
    beep: true
    format: wav          # wav or mp3
    stereo: false
    direction: both      # speak, hear, both
    initial_timeout: 5.0
    end_silence_timeout: 3.0
    terminators: "#"
```
Output vars: `record_url`, `record_result`, `record_duration`

### record_call
```yaml
- record_call:
    format: wav
    stereo: true
    direction: both
    control_id: my_recording
```

### switch (on variable value)
```yaml
- switch:
    variable: prompt_value
    case:
      "1": [{ transfer: "https://example.com/a.swml" }]
      "2": [{ transfer: "https://example.com/b.swml" }]
    default:
      - play: "say:Invalid option"
```

### cond (conditional array)
```yaml
- cond:
    - - "vars.balance > 100"
      - - play: "say:Premium customer"
    - - "vars.balance > 0"
      - - play: "say:Standard customer"
    - - play: "say:No balance found"
```

### Subroutine Pattern
```yaml
version: 1.0.0
sections:
  main:
    - answer
    - execute:
        dest: play_greeting
        params:
          name: "caller"
        result:
          case:
            ok: [{ play: "say:Continuing..." }]
          default: [hangup]
    - hangup

  play_greeting:
    - play: "say:Welcome %{params.name}"
    - return: "ok"
```

Note: the cheatsheet lists `record.direction` values "speak, hear, both"; the public record_call page and schema use "speak", "listen", "both".
