---
source: "MCP tool mcp__SignalWire_Knowledge__get_swml(doc='reference') (SignalWire_Knowledge server; internal SWML reference text; contains 'Expected on 9/4/2023' markers so may lag the public docs)"
fetched_at: "2026-10-06T15:21:41Z"
note: "Verbatim excerpts (line ranges from the 5066-line reference): Document fetching, transfer, execute, switch, cond, answer, hangup, play, record, record_call, stop_record_call, connect."
---

# SignalWire ML (SWML)

SignalWire ML (SWML) is the RELAY equivalent of LaML. The script native format is JSON, but can also be specified in YAML for human readability.

## Document fetching

1. Incoming call is routed to a call node
2. Call node sends RTC call_accept to Prime Rails.
3. Prime Rails replies with URL for SWML
4. SignalWire sends POST to webhook with body containing customer-defined script variables and the current call object:

```json
{
  "call": {
    "project_id": "project uuid",
    "space_id": "space_uuid",
    "call_id": "uuid",
    "state": "created",
    "type": "sip",
    "from": "sip:+15551231234@example.com",
    "to": "sip:+15553214321@example.com",
    "headers": [
      { "name": "X-Header-1", "value": "X-Header-1-Value" },
      { "name": "X-Header-2", "value": "X-Header-2-Value" }
    ]
  },
  "vars": {
    "customer_script_var_1": "customer_script_var_1_value",
    "customer_script_var_2": "customer_script_var_2_value"
  },
  "params": {
    "param_1": "param_1_value",
    "param_2": "param_2_value"
  }
}
```

5. Server replies with SignalWire ML Script with `application/json` or `application/yaml` or `text/x-yaml` content-type.

## Versioning

At the top level of a script will be a `version` field that is a string containing a semantic version for the document schema. Suggested use is MAJOR version reflects breaking changes where a script may not operate correctly without changes such as existing methods having new required parameters or renaming and refactoring.  The MINOR version can be used as new methods are introduced or new optional fields for existing methods, and PATCH version can be used to reflect only the most minor bug fixes which still have some impact on the schema.

## Document Execution

The document contains a `sections` field that is a mapping of named sections for execution. The `main` section is always executed first. There must always be a `main` section in the document. The `transfer` method is used to transfer the call execution to a new URL.

Each section is an Array of strings or objects. Strings can be used for methods that do not require parameters like `answer`, `hangup`, or `denoise`. Use objects to execute methods with parameters. Each string or object in the section's array is executed in order until the section is completed. If there are no more methods to execute, the call ends.

## Expression Evaluation with JavaScript

All text wrapped in `%{}` is evaluated as JavaScript or as a plain variable substitution.

### Variables and call parameters

All variables and call parameters are delivered in the POST body to the URL in `transfer` and `execute`. Use the `set` and `unset` methods to set or delete variables.

Variables are only set or unset as a side effect of SignalWire ML methods executed by the script. All variables can be referenced inside `%{}` JavaScript expressions in the `vars.` JavaScript object. Variables can not be permanently changed inside JavaScript expressions. 

All Call object parameters are referenceable inside JavaScript expressions. For example `%{call.from}` or `%{call.headers.X-Customer-ID}`. Call object parameters are read only.

## Script example

[...]
### transfer (dest)

Transfer execution of script to a new URL.

#### Parameters

- **dest:** Required `<URI>`
  - **`<label>`** - (DEPRECATED) section in document to jump to
  - **`relay:<relay application>`** - relay application to notify (NOT IMPLEMENTED)
  - **`https://<URL>`** - URL to fetch next document from. Sends HTTP POST
- **params:** Optional named parameters to send to section/URL/application. Default is not set.
- **meta:** Optional user data, ignored by SignalWire. Default is not set.

#### Variables

None

#### Examples

##### JSON, named parameter

```json
{ "transfer": { "dest": "https://example.com/next" } }
```

##### JSON, named parameter, with parameters

  ```json
{
   "transfer": {
      "dest": "https://example.com/next",
      "params": {
         "foo": "bar"
      }
   }
}
  ```

##### YAML, named parameter

```yaml
- transfer:
    dest: https://example.com/next
```

##### JSON, first parameter

```json
{ "transfer": "https://example.com/next" }
```

##### YAML, first parameter

```yaml
- transfer: https://example.com/next
```

---

### execute (dest)

Execute a section or URL as a subroutine and return back to current document.

#### Parameters

- **dest:** Required. It can be one of:
  - **`<label>`** - section in document to execute
  - **`https://<URL>`** - URL to fetch document to execute. Sends HTTP POST
- **params:** Optional named parameters to send to section/URL. Default is not set.
- **meta:** Optional user data, ignored by SignalWire. Default is not set. (CFB only: internal use; not costumer-facing)
- **result:** Optional. `switch` on `return_value` if `result` is an object (`{}`), or use as a `cond` if `result` is an array (`[]`)
- **on_return:** Optional. `Object` - a SWML document that takes over the call once the execute method is finished.

#### Variables

- **return_value:** (out) - Value returned by subroutine

#### Examples

##### JSON, named parameter

```json
{
   "execute": {
      "dest": "subroutine",
      "params": {
         "file": "https://example.com/foo.wav"
      }
   }
}
```

##### YAML, named parameter

```yaml
- execute:
    dest: subroutine
```

##### JSON, execute subroutine and optionally switch on return value
```json
{
  "label": "retry_menu",
  "execute": {
    "dest": "my_menu",
    "params": { "file": "https://example.com/foo.wav", "digits": "123" },
    "result": {
      "case": {
        "1": [
          { "execute": "https://example.com/sales.swml" }
        ],
        "2": [
          { "execute": "https://example.com/support.swml" }
        ],
        "3": [
          { "execute": "https://example.com/leave_a_message.swml" }
        ]
      },
      "default": [
        { "goto": { "label": "retry_menu", "max": 3 } }
      ]
    }
  }
}
```

##### JSON, execute subroutine and optionally branch on return value
```json
{
  "label": "retry_menu",
  "execute": {
    "dest": "my_menu",
    "params": { "file": "https://example.com/foo.wav", "digits": "123" },
    "result": [
      { "when": "vars.return_value == '1'", "then": [ { "execute": "https://example.com/sales.swml" } ] },
      { "when": "vars.return_value == '2'", "then": [ { "execute": "https://example.com/support.swml" } ] },
      { "when": "vars.return_value == '3'", "then": [ { "execute": "https://example.com/leave_a_message.swml" } ] },
      { "else": [ { "goto": { "label": "retry_menu", "max": 3 } } ] }
    ]
  }
}
```

---

### return (value)
Return from `execute` or exit script.

#### Parameters
 * Optional JSON parameter(s) of any type will be saved to `return_value`

#### Variables
 * **return_value:**(out) `Optional return value`

#### Examples

##### JSON, return with value

```json
{ "return": "1" }
 ```

##### YAML, return with value

 ```yaml
- return: 1
```

##### JSON, return with multiple values

```json
{ "return": { "a": "1", "b": "2" } }
 ```

##### YAML, return with multiple values

 ```yaml
- return:
    a: 1
    b: 2
```

##### JSON, return with no value

```json
 "return"
 ```

##### YAML, return with no value

 ```yaml
- return
```


---

### request (url)
GET/POST/PUT/DELETE a URL.

#### Parameters
[...]
### switch (variable, case)

Branch based on variable value.

#### Parameters

- **variable:** Required variable name.
- **case:** Optional object of values mapped to array of methods to execute. Default is not set.
- **default:** Optional array of methods to execute if no cases match. Default is not set.

#### Variables

None

#### Examples

##### JSON

```json
{
  "switch": {
    "variable": "prompt_value",
    "case": {
      "1": [{ "goto": "sales" }]
    },
    "default": [{ "play": "https://example.com/no_match.wav" }]
  }
}
```

##### YAML

```yaml
-switch:
  variable: prompt_value
  case:
    1:
    - goto: sales
  default:
  - play: "https://example.com/no_match.wav
```

---

### cond (when, then, else)
Branch based on JavaScript condition

#### Parameters
Array of objects:
 * **when:** Required JavaScript condition to test
 * **then:** Required array of methods to execute on true condition

or

 * **else:** Required array of methods to execute on no matching condition.

#### Variables

None

#### Examples

##### JSON

```json
{
  "cond": [
      {
        "when": "vars.foo < 2",
        "then": [
          "hangup"
        ]
      },
      {
        "when": "call.to == '+15551231234'",
        "then": [
          { "execute": "help" }
        ],
      },
      {
        "when": "/hello/.test(vars.foo)",
        "then": [
          { "execute": "match" }
        ]
      },
      {
        "else": [
          { "execute": "match" }
        ]
      }
    ]
}
```

##### YAML

```yaml
- cond:
  - when: "vars.foo > 3"
    then:
    - hangup
  - when: "vars.foo < 2"
    then:
    - hangup
  - when: "call.to == '+15551231234'"
    then:
    - execute: help
  - when: "/hello/.test(vars.foo)"
    then:
    - execute: match
  - else:
    - goto: retry
```

---

### if (condition, then, else)

Conditional execution with if/then/else structure.

#### Parameters

- **condition:** String, Required. JavaScript expression to evaluate.
- **then:** Array, Optional. Array of SWML methods to execute if condition is true.
- **else:** Array, Optional. Array of SWML methods to execute if condition is false.

#### Variables

None

#### Examples

##### JSON

```json
{
  "if": {
    "condition": "vars.foo > vars.bar",
    "then": [
      { "play": "say:Foo is greater than bar" }
    ],
    "else": [
      { "play": "say:Foo is not greater than bar" }
    ]
  }
}
```

##### YAML

```yaml
- if:
    condition: "vars.foo > vars.bar"
    then:
      - play: "say:Foo is greater than bar"
    else:
      - play: "say:Foo is not greater than bar"
```

---

### eval ({var=expression})

(DEPRECATED - use `set` instead)

Evaluate JavaScript expressions and store results in variables.

#### Parameters

Object where keys are variable names and values are JavaScript expressions to evaluate.

#### Variables

Sets the specified variables with the evaluated results.

#### Examples

##### JSON

```json
{
  "eval": {
    "foo": "vars.x > vars.y",
    "bar": "vars.count + 1",
    "result": "4 + 4"
  }
}
```

##### YAML

```yaml
- eval:
    foo: "vars.x > vars.y"
    bar: "vars.count + 1"
    result: "4 + 4"
```

---

### answer (max_duration)

Answer call and set optional maximum duration

#### Parameters

- **max_duration:** Optional maximum duration in seconds. Can not be less than 7 seconds. Default is 14400 seconds (4 hours).
- **codecs:** String, Optional. Comma-separated string of codecs to offer. Has no effect if a codec is not supported by the network. Default is picked by SignalWire. Valid codecs are: `PCMU,PCMA,G722,G729,AMR-WB,OPUS,VP8,H264`
- **fsvars:** Object, Optional. FreeSWITCH variables to set on the channel.
- **username:** String, Optional. Username for SIP requests that require authentication.
- **password:** String, Optional. Password for SIP requests that require authentication.

#### Variables

None

#### Examples

##### JSON, no parameters

```json
"answer"
```

##### JSON, first parameter

```json
{ "answer": 60.0 }
```

##### JSON, named parameter

```json
{ "answer": { "max_duration": 60.0, "codecs": "PCMU,PCMA" } }
```

##### YAML, no parameters

```yaml
- answer
```

##### YAML, first parameter

```yaml
- answer: 60.0
```

##### YAML, named parameter

```yaml
- answer:
    max_duration: 60.0
```

---

### hangup (reason)

End the call with optional reason

#### Parameters

- **reason:** Optional hangup reason (hangup, busy, decline). Default is busy.

#### Variables

None

#### Examples

##### JSON, no parameters

```json
"hangup"
```

##### JSON, first parameter

```json
{ "hangup": "busy" }
```

##### JSON, named parameter

```json
{ "hangup": { "reason": "busy" } }
```

##### YAML, no parameters

```yaml
-hangup
```

##### YAML, first parameter

```yaml
-hangup: busy
```

##### YAML, named parameter

```yaml
 -hangup
    reason: busy
```

---

### pay
[...]
### play (urls)

Play file(s), ringtones, speech or silence

#### Parameters

- **`auto_answer` Optional - Boolean - If `true`, the call will automatically answer as the sound is playing. If `false`, you will start playing the audio during early media
- **`urls`** (or **`url`**): Required, URL or string array of URLs to play. Allowed URLs are:
  - **`http://`** - audio file to GET
  - **`https://`** - audio file to GET
  - **`ring:<duration>:<country code>`** - ring tone to play. For example: `ring:us` to play single ring or `ring:20.0:us` to play ring for 20 seconds.
  - **`say:<text to speak>`** - Sentence to say
  - **`silence:<duration>`** - seconds of silence to play
- **`volume:`** Number, Optional \<-40.0 to 40.0\> optional gain to apply to URLs. Default 0.
- **`loop:`** Number, Optional number of times to play the file(s). Default 1. 0 will loop until the call ends or the play is stopped.
- **say_voice:** Optional voice to use for text to speech. Default is Polly.Salli.
- **say_language:** optional language to use for text to speech. Default is en-US.
- **say_gender:** optional gender to use for text to speech. Default is female.
- **status_url:** String, Optional. http or https URL to deliver RELAY play status events

#### Variables

- **`say_voice:`** (in) - optional voice to use for `say:` URLs
- **`say_language:`** (in) - optional language to use for `say:` URLs
- **`say_gender:`** (in) - optional gender to use for `say:` URLs

#### Examples

##### JSON, play single URL

```json
{ "play": "https://example.com/file.mp3" }
```

##### YAML, play single URL

```yaml
-play: https://example.com/file.mp3
```

##### JSON, play multiple URLs

```json
{
  "play": [
    "https://example.com/file1.wav",
    "https://example.com/file2.wav",
    "say: this is something to say",
    "silence:3.0",
    "ring:10.0:us"
  ]
}
```

##### YAML, play multiple URLs

```yaml
- play:
    - https://example.com/file1.wav
    - https://example.com/file2.wav
    - say:this is something to say
    - silence:3.0
    - ring:10.0:us
```

##### JSON, play multiple URLs with volume adjustment

```json
{
  "play": {
    "volume": 30,
    "urls": [
      "https://example.com/file1.wav",
      "https://example.com/file2.wav",
      "say:this is something to say",
      "silence:3.0",
      "ring:10.0:us"
    ]
  }
}
```

##### YAML, play multiple URLs with volume adjustment

```yaml
- play:
    volume: 30
    urls:
      - https://example.com/file1.wav
      - https://example.com/file2.wav
      - say:this is something to say
      - silence:3.0
      - ring:10.0:us
```

---

### bind_digit
[...]
### record

Record call audio in foreground. This is recording for voicemails.

#### Parameters

- **stereo:** Boolean, Optional. Default false.
- **format:** String, Optional. wav or mp3. Default wav
- **direction:** String, Optional. Direction of audio to record. speak = what party says. hear = what party hears. Default = speak.
- **terminators:** String, Optional. Digits that stop recording. Default = #
- **beep:** Boolean, Optional. Play a beep before recording. Default = false
- **input_sensitivity:** Number (0.0 - 100.0), Optional. How sensitive the recording voice activity detector is to background noise. Large value is more sensitive. Default 44.0
- **initial_timeout:** Number, Optional. How long to wait for speech to start in seconds. Default 4.0.
- **end_silence_timeout:** Number, optional. How much silence in seconds to end recording. Default 5.0.
- **max_length:** Number, Optional. Maximum length of the recording, in seconds. Default is 0 which means unlimited recording length.
- **status_url:** String, Optional. http or https URL to deliver RELAY recording status events


#### Variables

- **record_url:** (out) the URL of the newly created recording
- **record_result:** (out) success | failed

#### Examples

##### JSON, record then play it back

```json
{ "record": { "end_silence_timeout": 5.0 } },
{ "play": "%{record_url}" }
```

##### YAML, record then play it back

```yaml
- record:
    end_silence_timeout: 5.0
- play: "%{record_url}"
```

---

### record_call

Record call in the background.

#### Parameters

- **control_id:** String, Optional identifier for this recording to use with `stop_call_record`. Default is generated and saved to record_control_id variable.
- **stereo:** Boolean, Optional. Default false
- **format:** String, Optional. wav or mp3. Default wav
- **direction:** String, Optional. Direction of audio to record. speak = what party says. hear = what party hears. both = what party hears and says. Default = both.
- **terminators:** String, Optional. Digits that stop recording. Default is not set.
- **beep:** Boolean, Optional. Play a beep before recording. Default = false
- **input_sensitivity:** Number (0.0 - 100.0), Optional. How sensitive the recording voice activity detector is to background noise. Large value is more sensitive. Default 44.0
- **initial_timeout:** Number, Optional. How long to wait for speech to start in seconds. Default 0.
- **end_silence_timeout:** Number, Optional. How much silence in seconds to end recording. Default 0.
- **max_length**: Number, Optional. Maximum length of the recording, in seconds. Default is 0 which means unlimited recording length.
- **status_url:** String, Optional. http or https URL to deliver RELAY recording status events

#### Variables

- **record_call_url:** (out) the URL of the newly started recording
- **record_call_result:** (out) success | failed
- **record_control_id:** (out) control ID of this recording

#### Examples

##### JSON, start mp3 call recording

```json
{ "record_call": { "format": "mp3" } }
```

##### YAML, start mp3 call recording

```yaml
- record_call:
    format: mp3
```

---

### stop_record_call(control_id)

Stop an active background recording

#### Parameters

- **control_id:** String, Optional ID of the recording to stop. If not set, the last recording started will be stopped.

#### Variables

- **record_control_id:** (in) control ID of last recording started
- **stop_record_call_result:** (out) success | failed

#### Examples

##### JSON, stop last call recording

```json
"stop_record_call"
```

##### YAML, stop last call recording

```yaml
- stop_record_call
```

##### JSON, stop a specific call recording

```json
{ "stop_record_call": "my-recording-id" }
```

##### JSON, stop a specific call recording

```yaml
- stop_record_call: my-recording-id
```

---

### join_room (name)
[...]
### connect ()

Dial SIP URI or phone number

#### Destination

A destination is the object to dial with:

- **to:** String, Required. Phone number, SIP URI, queue, or stream to dial. Use `queue:queue_name` to connect to the first caller in a queue. Use `stream:wss://...` to connect to a bidirectional WebSocket stream.
- **from:** String, Optional. Caller ID number. Default is calling party caller ID number.
- **from_name:** String, Optional. Caller ID name for SIP calls. Has no effect on calls to phone numbers. Default is not set.
- **encryption:** String, Optional. Media encryption (SRTP). Possible values: `mandatory`, `optional`, `forbidden`. Has no effect on calls to phone numbers.
- **username:** String, Optional. Username for SIP authentication. Has no effect on calls to phone numbers. Default is not set.
- **password:** String, Optional. Password for SIP authentication. Has no effect on calls to phone numbers. Default is not set.
- **timeout:** Integer, Optional. Seconds. Maximum time to wait for destination to answer. Default is 60.
- **call_state_url:** String, Optional - webhook url (http(s)) to which send call state change notifications
- **call_state_events:** String, Optional - an array of call state event names to be notified about. Allowed event names: `created`, `ringing`, `answered`, `ended`. Defaults to `["ended"]`
- **confirm:** SWML URL or inline compact SWML script, Optional - script to execute on destination when answered. Parent and destination are bridged after script completes execution. If more than one destination is dialed in parallel, the destination that completes the script first wins and is bridged to the parent.
- **confirm_timeout:** Integer, Optional. The amount of seconds it takes for `confirm` to successfully execute. 
- **status_url:** String, Optional. http or https URL to deliver RELAY connect status events

##### Stream-specific parameters (when using `stream:` prefix)

- **name:** String, Optional. Stream name identifier.
- **codec:** String, Optional. Audio codec. Default is PCMU. Supported: PCMU, PCMA, G722, L16. Codec can include rate/ptime modifiers (e.g., `PCMU@40i`, `L16@24000h@40i`).
- **status_url:** String, Optional. Webhook URL (https://) for stream status notifications.
- **status_url_method:** String, Optional. HTTP method for status webhook (GET or POST). Default is POST.
- **realtime:** Boolean, Optional. Enable realtime mode for bidirectional audio. Default is false.
- **authorization_bearer_token:** String, Optional. Bearer token sent as Authorization header in WebSocket handshake.
- **custom_parameters:** Object, Optional. Custom key-value pairs sent in WebSocket start message.

#### Parameters

- **from:** String, Optional. Caller ID number. Default is calling party caller ID number. Can be overwritten on each [destination](#destination).
- **from_name:** String, Optional. Caller ID name for SIP calls. Has no effect on calls to phone numbers. Default is not set. Can be overwritten on each [destination](#destination).
- **headers:** Object, Optional. Custom SIP headers to add to INVITE. Has no effect on calls to phone numbers. Default is not set.
- **codecs:** String, Optional. Comma-separated string of codecs to offer. Has no effect on calls to phone numbers. Default is picked by SignalWire.
- **webrtc_media:** Boolean, Optional. If true, WebRTC media is offered to the SIP endpoint. Has no effect on calls to phone numbers. Default is false.
- **encryption:** String, Optional. Media encryption (SRTP). Possible values: `mandatory`, `optional`, `forbidden`. Has no effect on calls to phone numbers. Can be overwritten on each [destination](#destination).
- **session_timeout:** Integer, Optional. Seconds. If >0, SIP `Session-Expires` header in INVITE is set to this value. Has no effect on calls to phone numbers. Default is picked by SignalWire.
- **timeout:** Integer, Optional. Seconds. Maximum time to wait for destination to answer. Default is 60.
- **call_state_url:** String, Optional - webhook url (http(s)) to which send call state change notifications for all legs (in case of parallel/serial). Can be overwritten on each [destination](#destination).
- **call_state_events:** String, Optional - an array of call state event names to be notified about. Allowed event names: `created`, `ringing`, `answered`, `ended`. Defaults to `["ended"]`. Can be overwritten on each [destination](#destination).
- - **confirm:** (Expected 9/4/2023) SWML URL or inline compact SWML script, Optional - script to execute on destination when answered. Parent and destination are bridged after script completes execution. If more than one destination is dialed in parallel, the destination that completes the script first wins and is bridged to the parent. Can be overwritten on each [destination](#destination)
- **ringback:** Array of `play` URIs to play as ringback tone. Default will play audio from the provider.
- **max_duration:** Integer, Optional. Maximum duration in seconds.
- **answer_on_bridge:** Delay answer until the b-leg answers. Default is false
- one of the following dial algorithms
  - **serial_parallel:** Array of arrays. Inner arrays contain [destinations](#destination) to dial simultaneously. Outer array attempts each parallel group in order.
  - **serial:** Array of [destinations](#destination) to dial in order.
  - **parallel:** Array of [destinations](#destination) to dial simultaneously.
  - **to:** Single destination to dial.
- **result:** Optional `switch` on `return_value` when object `{}` or `cond` when array `[]`

#### Variables

- **connect_result:** (out) connected | failed
- **connect_failed_reason:** (out) detailed reason for failure
- **return_value:** (out) `connect_result`

#### Allowed SWML methods in confirm (Expected 9/4/2023) 
The following subset of SWML methods are allowed in confirm:
  - cond
  - if
  - switch
  - set
  - unset
  - hangup
  - play
  - prompt
  - record
  - record_call
  - stop_record_call
  - tap
  - stop_tap
  - send_digits
  - send_sms
  - denoise
  - stop_denoise

#### Examples

##### JSON, Dial single phone number

```json
{ "connect": { "from": "+15553214321", "to": "+15551231234" } }
```

##### YAML, Dial single phone number

```yaml
- connect:
    to: "+15551231234"
```

##### JSON, Dial single phone number, go to voicemail on failure

```json
{ "connect": {
    "from": "+15553214321",
    "to": "+15551231234",
    "result": {
      "case": {
        "connected": [ "hangup" ]
      },
      "default": [
        { "execute": "voicemail" },
        "hangup"
      ]
    }
  }
}
```

##### YAML, Dial single phone number, go to voicemail on failure

```yaml
- connect:
    from: "+15553214321"
    to: "+15551231234"
    result:
      case:
        connected:
        - hangup
      default:
      - execute: "voicemail"
      - hangup
```


##### JSON, Dial numbers in parallel, one number with shorter timeout than default 60 seconds

```json
{
  "connect": {
    "parallel": [{ "to": "+15551231234", "timeout": 20 }, { "to": "+15553214321" }]
  }
}
```

##### YAML, Dial numbers in parallel, one number with shorter timeout than default 60 seconds

```yaml
-connect:
  parallel:
    - to: +15551231234
      timeout: 20
    - to: +15553214321
```

##### JSON, Dial SIP serially, with timeout of 20 seconds applied to all numbers

```json
{
  "connect": {
    "timeout": 20,
    "serial": [
      { "from": "sip:chris@example.com", "to": "sip:alice@example.com" },
      { "codecs": "PCMU", "to": "sip:bob@example.com" }
    ]
  }
}
```

##### YAML, Dial SIP serially, with timeout of 20 seconds applied to all numbers

```yaml
- connect:
    timeout: 20
    serial:
      - from: "sip:chris@example.com"
        to: "sip:alice@example.com"
      - to: "sip:bob@example.com"
        codecs: PCMU
```

##### JSON, Dial numbers in parallel. Called party must press one to accept the call.

```json
{
  "connect": {
    "timeout": 20,
    "confirm": [
      {
        "prompt": "say:Press one to accept this call."
      },
      {
        "cond": [
          { "when": "%{var.prompt_value != '1'}", "then": [ "hangup" ] },
          { "else": [ { "play": "say:Thank you" } ] }
        ]
      }
    ],
    "parallel": [{ "to": "+15551231234" }, { "to": "+15553214321" }]
  }
}
```

##### JSON, Connect to first caller in queue

```json
{ "connect": { "to": "queue:my_queue" } }
```

##### YAML, Connect to first caller in queue

```yaml
- connect:
    to: "queue:my_queue"
```

##### JSON, Connect to bidirectional WebSocket stream

```json
{
  "connect": {
    "to": "stream:wss://example.com/audio",
    "codec": "PCMU",
    "realtime": true,
    "authorization_bearer_token": "my-secret-token",
    "custom_parameters": {
      "user_id": "12345",
      "session_type": "voice"
    }
  }
}
```

##### YAML, Connect to bidirectional WebSocket stream

```yaml
- connect:
    to: "stream:wss://example.com/audio"
    codec: PCMU
    realtime: true
    authorization_bearer_token: "my-secret-token"
    custom_parameters:
      user_id: "12345"
      session_type: "voice"
```

---

### dial
