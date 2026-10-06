---
source: "MCP tool mcp__SignalWire_Knowledge__get_swml(doc='schema') (SWML JSON schema, SWMLObject.json, $defs)"
fetched_at: "2026-10-06T15:21:41Z"
note: "Extracted $defs for connect device variants, ConnectHeaders, ConnectSwitch, RecordCall, StopRecordCall, Record. grep for 'maxItems' over the full schema returned 0 matches (no documented cap on parallel destination count)."
---

## ConnectDeviceSingle

```json
{
 "type": "object",
 "properties": {
  "from": {
   "type": "string",
   "examples": [
    "+15551234567"
   ],
   "description": "The caller ID to use when dialing the number."
  },
  "headers": {
   "type": "array",
   "items": {
    "$ref": "#/$defs/ConnectHeaders"
   },
   "description": "Custom SIP headers to add to INVITE. It Has no effect on calls to phone numbers."
  },
  "codecs": {
   "type": "string",
   "examples": [
    "PCMU,PCMA,OPUS"
   ],
   "description": "Comma-separated string of codecs to offer.\nIt has no effect on calls to phone numbers.\nBased on SignalWire settings."
  },
  "webrtc_media": {
   "anyOf": [
    {
     "type": "boolean"
    },
    {
     "$ref": "#/$defs/SWMLVar"
    }
   ],
   "default": false,
   "examples": [
    true
   ],
   "description": "If true, WebRTC media is offered to the SIP endpoint.\nIt has no effect on calls to phone numbers.\nDefault is `false`."
  },
  "session_timeout": {
   "anyOf": [
    {
     "type": "integer"
    },
    {
     "$ref": "#/$defs/SWMLVar"
    }
   ],
   "default": 0,
   "examples": [
    1800
   ],
   "minimum": 1,
   "description": "Time, in seconds, to set the SIP `Session-Expires` header in INVITE.\nMust be a positive, non-zero number.\nIt has no effect on calls to phone numbers.\nBased on SignalWire settings."
  },
  "ringback": {
   "type": "array",
   "items": {
    "type": "string"
   },
   "examples": [
    [
     "https://example.com/ringback.mp3"
    ]
   ],
   "description": "Array of URIs to play as ringback tone. If not specified, plays audio from the provider."
  },
  "result": {
   "anyOf": [
    {
     "$ref": "#/$defs/ConnectSwitch"
    },
    {
     "type": "array",
     "items": {
      "$ref": "#/$defs/CondParams"
     },
     "description": "Execute a sequence of instructions depending on the value of a JavaScript condition.",
     "title": "cond"
    }
   ],
   "description": "Action to take based on the result of the call. This will run once the peer leg of the call has ended.\nWill use the switch method when the return_value is an object, and will use the cond method when the return_value is an array."
  },
  "timeout": {
   "anyOf": [
    {
     "type": "integer"
    },
    {
     "$ref": "#/$defs/SWMLVar"
    }
   ],
   "default": 60,
   "examples": [
    30
   ],
   "description": "Time, in seconds, to wait for the call to be answered.\nDefault is 60 seconds."
  },
  "max_duration": {
   "anyOf": [
    {
     "type": "integer"
    },
    {
     "$ref": "#/$defs/SWMLVar"
    }
   ],
   "default": 14400,
   "examples": [
    3600
   ],
   "description": "Maximum duration, in seconds, allowed for the call.\nDefault is `14400` seconds."
  },
  "answer_on_bridge": {
   "anyOf": [
    {
     "type": "boolean"
    },
    {
     "$ref": "#/$defs/SWMLVar"
    }
   ],
   "default": false,
   "examples": [
    true
   ],
   "description": "Delay answer until the B-leg answers.\nDefault is `false`."
  },
  "confirm": {
   "anyOf": [
    {
     "type": "string"
    },
    {
     "type": "array",
     "items": {
      "$ref": "#/$defs/ValidConfirmMethods"
     }
    }
   ],
   "examples": [
    "https://example.com/confirm.swml"
   ],
   "description": "Confirmation to execute when the call is connected. Can be either:\n- A URL (string) that returns a SWML document\n- An array of SWML methods to execute inline"
  },
  "confirm_timeout": {
   "anyOf": [
    {
     "type": "integer"
    },
    {
     "$ref": "#/$defs/SWMLVar"
    }
   ],
   "examples": [
    30
   ],
   "description": "The amount of time, in seconds, to wait for the `confirm` URL to return a response"
  },
  "username": {
   "type": "string",
   "examples": [
    "sipuser"
   ],
   "description": "SIP username to use for authentication when dialing a SIP URI. Has no effect on calls to phone numbers."
  },
  "password": {
   "type": "string",
   "examples": [
    "sippassword"
   ],
   "description": "SIP password to use for authentication when dialing a SIP URI. Has no effect on calls to phone numbers."
  },
  "encryption": {
   "anyOf": [
    {
     "type": "string",
     "const": "mandatory"
    },
    {
     "type": "string",
     "const": "optional"
    },
    {
     "type": "string",
     "const": "forbidden"
    }
   ],
   "default": "optional",
   "examples": [
    "optional"
   ],
   "description": "Encryption setting to use. **Possible values:** `mandatory`, `optional`, `forbidden`"
  },
  "call_state_url": {
   "type": "string",
   "format": "uri",
   "examples": [
    "https://example.com/call-status"
   ],
   "description": "Webhook URL to send call status change notifications to. Authentication can also be set in the URL in the format of `username:password@url`."
  },
  "transfer_after_bridge": {
   "anyOf": [
    {
     "type": "string"
    },
    {
     "$ref": "#/$defs/SWMLVar"
    }
   ],
   "examples": [
    "https://example.com/after-bridge.swml"
   ],
   "description": "SWML to execute after the bridge completes. This defines what should happen after the call is connected and the bridge ends.\nCan be either:\n- A URL (http or https) that returns a SWML document\n- An inline SWML document (as a JSON string)\n\n**Note:** This parameter is REQUIRED when connecting to a queue (when `to` starts with \"queue:\")"
  },
  "call_state_events": {
   "type": "array",
   "items": {
    "$ref": "#/$defs/CallStatus"
   },
   "default": [
    "ended"
   ],
   "description": "An array of call state event names to be notified about.\nAllowed event names are:\n    - `created`\n    - `ringing`\n    - `answered`\n    - `ended`"
  },
  "to": {
   "type": "string",
   "examples": [
    "+15559876543"
   ],
   "description": "Destination to dial. Can be:\n- Phone number in E.164 format (e.g., \"+15552345678\")\n- SIP URI (e.g., \"sip:alice@example.com\")\n- Call Fabric Resource address (e.g., \"/public/test_room\")\n- Queue (e.g., \"queue:support\")"
  }
 },
 "required": [
  "to"
 ],
 "unevaluatedProperties": {
  "not": {}
 },
 "title": "ConnectDeviceSingle object"
}
```

## ConnectDeviceParallel

```json
{
 "type": "object",
 "properties": {
  "from": {
   "type": "string",
   "examples": [
    "+15551234567"
   ],
   "description": "The caller ID to use when dialing the number."
  },
  "headers": {
   "type": "array",
   "items": {
    "$ref": "#/$defs/ConnectHeaders"
   },
   "description": "Custom SIP headers to add to INVITE. It Has no effect on calls to phone numbers."
  },
  "codecs": {
   "type": "string",
   "examples": [
    "PCMU,PCMA,OPUS"
   ],
   "description": "Comma-separated string of codecs to offer.\nIt has no effect on calls to phone numbers.\nBased on SignalWire settings."
  },
  "webrtc_media": {
   "anyOf": [
    {
     "type": "boolean"
    },
    {
     "$ref": "#/$defs/SWMLVar"
    }
   ],
   "default": false,
   "examples": [
    true
   ],
   "description": "If true, WebRTC media is offered to the SIP endpoint.\nIt has no effect on calls to phone numbers.\nDefault is `false`."
  },
  "session_timeout": {
   "anyOf": [
    {
     "type": "integer"
    },
    {
     "$ref": "#/$defs/SWMLVar"
    }
   ],
   "default": 0,
   "examples": [
    1800
   ],
   "minimum": 1,
   "description": "Time, in seconds, to set the SIP `Session-Expires` header in INVITE.\nMust be a positive, non-zero number.\nIt has no effect on calls to phone numbers.\nBased on SignalWire settings."
  },
  "ringback": {
   "type": "array",
   "items": {
    "type": "string"
   },
   "examples": [
    [
     "https://example.com/ringback.mp3"
    ]
   ],
   "description": "Array of URIs to play as ringback tone. If not specified, plays audio from the provider."
  },
  "result": {
   "anyOf": [
    {
     "$ref": "#/$defs/ConnectSwitch"
    },
    {
     "type": "array",
     "items": {
      "$ref": "#/$defs/CondParams"
     },
     "description": "Execute a sequence of instructions depending on the value of a JavaScript condition.",
     "title": "cond"
    }
   ],
   "description": "Action to take based on the result of the call. This will run once the peer leg of the call has ended.\nWill use the switch method when the return_value is an object, and will use the cond method when the return_value is an array."
  },
  "timeout": {
   "anyOf": [
    {
     "type": "integer"
    },
    {
     "$ref": "#/$defs/SWMLVar"
    }
   ],
   "default": 60,
   "examples": [
    30
   ],
   "description": "Time, in seconds, to wait for the call to be answered.\nDefault is 60 seconds."
  },
  "max_duration": {
   "anyOf": [
    {
     "type": "integer"
    },
    {
     "$ref": "#/$defs/SWMLVar"
    }
   ],
   "default": 14400,
   "examples": [
    3600
   ],
   "description": "Maximum duration, in seconds, allowed for the call.\nDefault is `14400` seconds."
  },
  "answer_on_bridge": {
   "anyOf": [
    {
     "type": "boolean"
    },
    {
     "$ref": "#/$defs/SWMLVar"
    }
   ],
   "default": false,
   "examples": [
    true
   ],
   "description": "Delay answer until the B-leg answers.\nDefault is `false`."
  },
  "confirm": {
   "anyOf": [
    {
     "type": "string"
    },
    {
     "type": "array",
     "items": {
      "$ref": "#/$defs/ValidConfirmMethods"
     }
    }
   ],
   "examples": [
    "https://example.com/confirm.swml"
   ],
   "description": "Confirmation to execute when the call is connected. Can be either:\n- A URL (string) that returns a SWML document\n- An array of SWML methods to execute inline"
  },
  "confirm_timeout": {
   "anyOf": [
    {
     "type": "integer"
    },
    {
     "$ref": "#/$defs/SWMLVar"
    }
   ],
   "examples": [
    30
   ],
   "description": "The amount of time, in seconds, to wait for the `confirm` URL to return a response"
  },
  "username": {
   "type": "string",
   "examples": [
    "sipuser"
   ],
   "description": "SIP username to use for authentication when dialing a SIP URI. Has no effect on calls to phone numbers."
  },
  "password": {
   "type": "string",
   "examples": [
    "sippassword"
   ],
   "description": "SIP password to use for authentication when dialing a SIP URI. Has no effect on calls to phone numbers."
  },
  "encryption": {
   "anyOf": [
    {
     "type": "string",
     "const": "mandatory"
    },
    {
     "type": "string",
     "const": "optional"
    },
    {
     "type": "string",
     "const": "forbidden"
    }
   ],
   "default": "optional",
   "examples": [
    "optional"
   ],
   "description": "Encryption setting to use. **Possible values:** `mandatory`, `optional`, `forbidden`"
  },
  "call_state_url": {
   "type": "string",
   "format": "uri",
   "examples": [
    "https://example.com/call-status"
   ],
   "description": "Webhook URL to send call status change notifications to. Authentication can also be set in the URL in the format of `username:password@url`."
  },
  "transfer_after_bridge": {
   "anyOf": [
    {
     "type": "string"
    },
    {
     "$ref": "#/$defs/SWMLVar"
    }
   ],
   "examples": [
    "https://example.com/after-bridge.swml"
   ],
   "description": "SWML to execute after the bridge completes. This defines what should happen after the call is connected and the bridge ends.\nCan be either:\n- A URL (http or https) that returns a SWML document\n- An inline SWML document (as a JSON string)\n\n**Note:** This parameter is REQUIRED when connecting to a queue (when `to` starts with \"queue:\")"
  },
  "call_state_events": {
   "type": "array",
   "items": {
    "$ref": "#/$defs/CallStatus"
   },
   "default": [
    "ended"
   ],
   "description": "An array of call state event names to be notified about.\nAllowed event names are:\n    - `created`\n    - `ringing`\n    - `answered`\n    - `ended`"
  },
  "parallel": {
   "type": "array",
   "items": {
    "$ref": "#/$defs/ConnectDeviceSingle"
   },
   "description": "Array of destinations to dial simultaneously."
  }
 },
 "required": [
  "parallel"
 ],
 "unevaluatedProperties": {
  "not": {}
 },
 "title": "ConnectDeviceParallel object"
}
```

## ConnectDeviceSerial

```json
{
 "type": "object",
 "properties": {
  "from": {
   "type": "string",
   "examples": [
    "+15551234567"
   ],
   "description": "The caller ID to use when dialing the number."
  },
  "headers": {
   "type": "array",
   "items": {
    "$ref": "#/$defs/ConnectHeaders"
   },
   "description": "Custom SIP headers to add to INVITE. It Has no effect on calls to phone numbers."
  },
  "codecs": {
   "type": "string",
   "examples": [
    "PCMU,PCMA,OPUS"
   ],
   "description": "Comma-separated string of codecs to offer.\nIt has no effect on calls to phone numbers.\nBased on SignalWire settings."
  },
  "webrtc_media": {
   "anyOf": [
    {
     "type": "boolean"
    },
    {
     "$ref": "#/$defs/SWMLVar"
    }
   ],
   "default": false,
   "examples": [
    true
   ],
   "description": "If true, WebRTC media is offered to the SIP endpoint.\nIt has no effect on calls to phone numbers.\nDefault is `false`."
  },
  "session_timeout": {
   "anyOf": [
    {
     "type": "integer"
    },
    {
     "$ref": "#/$defs/SWMLVar"
    }
   ],
   "default": 0,
   "examples": [
    1800
   ],
   "minimum": 1,
   "description": "Time, in seconds, to set the SIP `Session-Expires` header in INVITE.\nMust be a positive, non-zero number.\nIt has no effect on calls to phone numbers.\nBased on SignalWire settings."
  },
  "ringback": {
   "type": "array",
   "items": {
    "type": "string"
   },
   "examples": [
    [
     "https://example.com/ringback.mp3"
    ]
   ],
   "description": "Array of URIs to play as ringback tone. If not specified, plays audio from the provider."
  },
  "result": {
   "anyOf": [
    {
     "$ref": "#/$defs/ConnectSwitch"
    },
    {
     "type": "array",
     "items": {
      "$ref": "#/$defs/CondParams"
     },
     "description": "Execute a sequence of instructions depending on the value of a JavaScript condition.",
     "title": "cond"
    }
   ],
   "description": "Action to take based on the result of the call. This will run once the peer leg of the call has ended.\nWill use the switch method when the return_value is an object, and will use the cond method when the return_value is an array."
  },
  "timeout": {
   "anyOf": [
    {
     "type": "integer"
    },
    {
     "$ref": "#/$defs/SWMLVar"
    }
   ],
   "default": 60,
   "examples": [
    30
   ],
   "description": "Time, in seconds, to wait for the call to be answered.\nDefault is 60 seconds."
  },
  "max_duration": {
   "anyOf": [
    {
     "type": "integer"
    },
    {
     "$ref": "#/$defs/SWMLVar"
    }
   ],
   "default": 14400,
   "examples": [
    3600
   ],
   "description": "Maximum duration, in seconds, allowed for the call.\nDefault is `14400` seconds."
  },
  "answer_on_bridge": {
   "anyOf": [
    {
     "type": "boolean"
    },
    {
     "$ref": "#/$defs/SWMLVar"
    }
   ],
   "default": false,
   "examples": [
    true
   ],
   "description": "Delay answer until the B-leg answers.\nDefault is `false`."
  },
  "confirm": {
   "anyOf": [
    {
     "type": "string"
    },
    {
     "type": "array",
     "items": {
      "$ref": "#/$defs/ValidConfirmMethods"
     }
    }
   ],
   "examples": [
    "https://example.com/confirm.swml"
   ],
   "description": "Confirmation to execute when the call is connected. Can be either:\n- A URL (string) that returns a SWML document\n- An array of SWML methods to execute inline"
  },
  "confirm_timeout": {
   "anyOf": [
    {
     "type": "integer"
    },
    {
     "$ref": "#/$defs/SWMLVar"
    }
   ],
   "examples": [
    30
   ],
   "description": "The amount of time, in seconds, to wait for the `confirm` URL to return a response"
  },
  "username": {
   "type": "string",
   "examples": [
    "sipuser"
   ],
   "description": "SIP username to use for authentication when dialing a SIP URI. Has no effect on calls to phone numbers."
  },
  "password": {
   "type": "string",
   "examples": [
    "sippassword"
   ],
   "description": "SIP password to use for authentication when dialing a SIP URI. Has no effect on calls to phone numbers."
  },
  "encryption": {
   "anyOf": [
    {
     "type": "string",
     "const": "mandatory"
    },
    {
     "type": "string",
     "const": "optional"
    },
    {
     "type": "string",
     "const": "forbidden"
    }
   ],
   "default": "optional",
   "examples": [
    "optional"
   ],
   "description": "Encryption setting to use. **Possible values:** `mandatory`, `optional`, `forbidden`"
  },
  "call_state_url": {
   "type": "string",
   "format": "uri",
   "examples": [
    "https://example.com/call-status"
   ],
   "description": "Webhook URL to send call status change notifications to. Authentication can also be set in the URL in the format of `username:password@url`."
  },
  "transfer_after_bridge": {
   "anyOf": [
    {
     "type": "string"
    },
    {
     "$ref": "#/$defs/SWMLVar"
    }
   ],
   "examples": [
    "https://example.com/after-bridge.swml"
   ],
   "description": "SWML to execute after the bridge completes. This defines what should happen after the call is connected and the bridge ends.\nCan be either:\n- A URL (http or https) that returns a SWML document\n- An inline SWML document (as a JSON string)\n\n**Note:** This parameter is REQUIRED when connecting to a queue (when `to` starts with \"queue:\")"
  },
  "call_state_events": {
   "type": "array",
   "items": {
    "$ref": "#/$defs/CallStatus"
   },
   "default": [
    "ended"
   ],
   "description": "An array of call state event names to be notified about.\nAllowed event names are:\n    - `created`\n    - `ringing`\n    - `answered`\n    - `ended`"
  },
  "serial": {
   "type": "array",
   "items": {
    "$ref": "#/$defs/ConnectDeviceSingle"
   }
  }
 },
 "required": [
  "serial"
 ],
 "unevaluatedProperties": {
  "not": {}
 },
 "title": "ConnectDeviceSerial object"
}
```

## ConnectDeviceSerialParallel

```json
{
 "type": "object",
 "properties": {
  "from": {
   "type": "string",
   "examples": [
    "+15551234567"
   ],
   "description": "The caller ID to use when dialing the number."
  },
  "headers": {
   "type": "array",
   "items": {
    "$ref": "#/$defs/ConnectHeaders"
   },
   "description": "Custom SIP headers to add to INVITE. It Has no effect on calls to phone numbers."
  },
  "codecs": {
   "type": "string",
   "examples": [
    "PCMU,PCMA,OPUS"
   ],
   "description": "Comma-separated string of codecs to offer.\nIt has no effect on calls to phone numbers.\nBased on SignalWire settings."
  },
  "webrtc_media": {
   "anyOf": [
    {
     "type": "boolean"
    },
    {
     "$ref": "#/$defs/SWMLVar"
    }
   ],
   "default": false,
   "examples": [
    true
   ],
   "description": "If true, WebRTC media is offered to the SIP endpoint.\nIt has no effect on calls to phone numbers.\nDefault is `false`."
  },
  "session_timeout": {
   "anyOf": [
    {
     "type": "integer"
    },
    {
     "$ref": "#/$defs/SWMLVar"
    }
   ],
   "default": 0,
   "examples": [
    1800
   ],
   "minimum": 1,
   "description": "Time, in seconds, to set the SIP `Session-Expires` header in INVITE.\nMust be a positive, non-zero number.\nIt has no effect on calls to phone numbers.\nBased on SignalWire settings."
  },
  "ringback": {
   "type": "array",
   "items": {
    "type": "string"
   },
   "examples": [
    [
     "https://example.com/ringback.mp3"
    ]
   ],
   "description": "Array of URIs to play as ringback tone. If not specified, plays audio from the provider."
  },
  "result": {
   "anyOf": [
    {
     "$ref": "#/$defs/ConnectSwitch"
    },
    {
     "type": "array",
     "items": {
      "$ref": "#/$defs/CondParams"
     },
     "description": "Execute a sequence of instructions depending on the value of a JavaScript condition.",
     "title": "cond"
    }
   ],
   "description": "Action to take based on the result of the call. This will run once the peer leg of the call has ended.\nWill use the switch method when the return_value is an object, and will use the cond method when the return_value is an array."
  },
  "timeout": {
   "anyOf": [
    {
     "type": "integer"
    },
    {
     "$ref": "#/$defs/SWMLVar"
    }
   ],
   "default": 60,
   "examples": [
    30
   ],
   "description": "Time, in seconds, to wait for the call to be answered.\nDefault is 60 seconds."
  },
  "max_duration": {
   "anyOf": [
    {
     "type": "integer"
    },
    {
     "$ref": "#/$defs/SWMLVar"
    }
   ],
   "default": 14400,
   "examples": [
    3600
   ],
   "description": "Maximum duration, in seconds, allowed for the call.\nDefault is `14400` seconds."
  },
  "answer_on_bridge": {
   "anyOf": [
    {
     "type": "boolean"
    },
    {
     "$ref": "#/$defs/SWMLVar"
    }
   ],
   "default": false,
   "examples": [
    true
   ],
   "description": "Delay answer until the B-leg answers.\nDefault is `false`."
  },
  "confirm": {
   "anyOf": [
    {
     "type": "string"
    },
    {
     "type": "array",
     "items": {
      "$ref": "#/$defs/ValidConfirmMethods"
     }
    }
   ],
   "examples": [
    "https://example.com/confirm.swml"
   ],
   "description": "Confirmation to execute when the call is connected. Can be either:\n- A URL (string) that returns a SWML document\n- An array of SWML methods to execute inline"
  },
  "confirm_timeout": {
   "anyOf": [
    {
     "type": "integer"
    },
    {
     "$ref": "#/$defs/SWMLVar"
    }
   ],
   "examples": [
    30
   ],
   "description": "The amount of time, in seconds, to wait for the `confirm` URL to return a response"
  },
  "username": {
   "type": "string",
   "examples": [
    "sipuser"
   ],
   "description": "SIP username to use for authentication when dialing a SIP URI. Has no effect on calls to phone numbers."
  },
  "password": {
   "type": "string",
   "examples": [
    "sippassword"
   ],
   "description": "SIP password to use for authentication when dialing a SIP URI. Has no effect on calls to phone numbers."
  },
  "encryption": {
   "anyOf": [
    {
     "type": "string",
     "const": "mandatory"
    },
    {
     "type": "string",
     "const": "optional"
    },
    {
     "type": "string",
     "const": "forbidden"
    }
   ],
   "default": "optional",
   "examples": [
    "optional"
   ],
   "description": "Encryption setting to use. **Possible values:** `mandatory`, `optional`, `forbidden`"
  },
  "call_state_url": {
   "type": "string",
   "format": "uri",
   "examples": [
    "https://example.com/call-status"
   ],
   "description": "Webhook URL to send call status change notifications to. Authentication can also be set in the URL in the format of `username:password@url`."
  },
  "transfer_after_bridge": {
   "anyOf": [
    {
     "type": "string"
    },
    {
     "$ref": "#/$defs/SWMLVar"
    }
   ],
   "examples": [
    "https://example.com/after-bridge.swml"
   ],
   "description": "SWML to execute after the bridge completes. This defines what should happen after the call is connected and the bridge ends.\nCan be either:\n- A URL (http or https) that returns a SWML document\n- An inline SWML document (as a JSON string)\n\n**Note:** This parameter is REQUIRED when connecting to a queue (when `to` starts with \"queue:\")"
  },
  "call_state_events": {
   "type": "array",
   "items": {
    "$ref": "#/$defs/CallStatus"
   },
   "default": [
    "ended"
   ],
   "description": "An array of call state event names to be notified about.\nAllowed event names are:\n    - `created`\n    - `ringing`\n    - `answered`\n    - `ended`"
  },
  "serial_parallel": {
   "type": "array",
   "items": {
    "type": "array",
    "items": {
     "$ref": "#/$defs/ConnectDeviceSingle"
    }
   },
   "description": "Array of arrays.\nInner arrays contain destinations to dial simultaneously.\nOuter array attempts each parallel group in order."
  }
 },
 "required": [
  "serial_parallel"
 ],
 "unevaluatedProperties": {
  "not": {}
 },
 "title": "ConnectDeviceSerialParallel object"
}
```

## ConnectHeaders

```json
{
 "type": "object",
 "properties": {
  "name": {
   "type": "string",
   "examples": [
    "X-Custom-Header"
   ],
   "description": "The name of the header."
  },
  "value": {
   "type": "string",
   "examples": [
    "custom-value"
   ],
   "description": "The value of the header."
  }
 },
 "required": [
  "name",
  "value"
 ],
 "unevaluatedProperties": {
  "not": {}
 },
 "title": "ConnectHeaders object"
}
```

## ConnectSwitch

```json
{
 "type": "object",
 "properties": {
  "variable": {
   "type": "string",
   "examples": [
    "connect_result"
   ],
   "description": "Name of the variable whose value needs to be compared. If not provided, it will check the `connect_result` variable."
  },
  "case": {
   "type": "object",
   "properties": {},
   "unevaluatedProperties": {
    "type": "array",
    "items": {
     "$ref": "#/$defs/SWMLMethod"
    }
   },
   "description": "Object of values mapped to array of instructions to execute"
  },
  "default": {
   "type": "array",
   "items": {
    "$ref": "#/$defs/SWMLMethod"
   },
   "description": "Array of instructions to execute if no cases match"
  }
 },
 "required": [
  "case"
 ],
 "unevaluatedProperties": {
  "not": {}
 },
 "title": "ConnectSwitch object"
}
```

## RecordCall

```json
{
 "type": "object",
 "properties": {
  "record_call": {
   "type": "object",
   "properties": {
    "control_id": {
     "type": "string",
     "examples": [
      "recording_001"
     ],
     "description": "Identifier for this recording, to use with `stop_call_record`."
    },
    "stereo": {
     "anyOf": [
      {
       "type": "boolean"
      },
      {
       "$ref": "#/$defs/SWMLVar"
      }
     ],
     "default": false,
     "examples": [
      true
     ],
     "description": "If `true`, record in stereo.\nDefault is `false`."
    },
    "format": {
     "anyOf": [
      {
       "type": "string",
       "const": "wav"
      },
      {
       "type": "string",
       "const": "mp3"
      },
      {
       "type": "string",
       "const": "mp4"
      }
     ],
     "default": "wav",
     "examples": [
      "mp3"
     ],
     "description": "The format to record in. It can be `wav`, `mp3`, or `mp4`.\nDefault is `\"wav\"`."
    },
    "direction": {
     "anyOf": [
      {
       "type": "string",
       "const": "speak"
      },
      {
       "type": "string",
       "const": "listen"
      },
      {
       "type": "string",
       "const": "both"
      }
     ],
     "default": "both",
     "examples": [
      "both"
     ],
     "description": "Direction of the audio to record: \"speak\" for what party says, \"listen\" for what party hears, \"both\" for what the party hears and says.\nDefault is `\"both\"`."
    },
    "terminators": {
     "type": "string",
     "default": "",
     "examples": [
      "#*"
     ],
     "description": "String of digits that will stop the recording when pressed. Default is `\"\"` (empty)."
    },
    "beep": {
     "anyOf": [
      {
       "type": "boolean"
      },
      {
       "$ref": "#/$defs/SWMLVar"
      }
     ],
     "default": false,
     "examples": [
      true
     ],
     "description": "Play a beep before recording.\nDefault is `false`."
    },
    "input_sensitivity": {
     "anyOf": [
      {
       "type": "number"
      },
      {
       "$ref": "#/$defs/SWMLVar"
      }
     ],
     "default": 44,
     "examples": [
      44
     ],
     "description": "How sensitive the recording voice activity detector is to background noise.\nA larger value is more sensitive. Allowed values from 0.0 to 100.0.\nDefault is `44.0`."
    },
    "initial_timeout": {
     "anyOf": [
      {
       "type": "number"
      },
      {
       "$ref": "#/$defs/SWMLVar"
      }
     ],
     "default": 0,
     "examples": [
      0
     ],
     "description": "Time in seconds to wait for the start of speech.\nDefault is `0.0` seconds."
    },
    "end_silence_timeout": {
     "anyOf": [
      {
       "type": "number"
      },
      {
       "$ref": "#/$defs/SWMLVar"
      }
     ],
     "default": 0,
     "examples": [
      0
     ],
     "description": "Time in seconds to wait in silence before ending the recording.\nDefault is `0.0` seconds."
    },
    "max_length": {
     "anyOf": [
      {
       "type": "number"
      },
      {
       "$ref": "#/$defs/SWMLVar"
      }
     ],
     "examples": [
      300
     ],
     "description": "Maximum length of the recording in seconds."
    },
    "status_url": {
     "type": "string",
     "format": "uri",
     "examples": [
      "https://example.com/record-call-status"
     ],
     "description": "http or https URL to deliver record_call status events"
    }
   },
   "unevaluatedProperties": {
    "not": {}
   },
   "description": "Record call in the background.\nUnlike the record method, the record_call method will start the recording and continue executing\nthe SWML script while allowing the recording to happen in the background.\nTo stop call recordings started with record_call, use the stop_record_call method.",
   "title": "record_call"
  }
 },
 "required": [
  "record_call"
 ],
 "unevaluatedProperties": {
  "not": {}
 },
 "title": "RecordCall object"
}
```

## StopRecordCall

```json
{
 "type": "object",
 "properties": {
  "stop_record_call": {
   "type": "object",
   "properties": {
    "control_id": {
     "type": "string",
     "examples": [
      "recording_001"
     ],
     "description": "Identifier for the recording to stop.\nIf not set, the last recording started will be stopped."
    }
   },
   "unevaluatedProperties": {
    "not": {}
   },
   "description": "Stop an active background recording.",
   "title": "stop_record_call"
  }
 },
 "required": [
  "stop_record_call"
 ],
 "unevaluatedProperties": {
  "not": {}
 },
 "title": "StopRecordCall object"
}
```

## Record

```json
{
 "type": "object",
 "properties": {
  "record": {
   "type": "object",
   "properties": {
    "stereo": {
     "anyOf": [
      {
       "type": "boolean"
      },
      {
       "$ref": "#/$defs/SWMLVar"
      }
     ],
     "default": false,
     "examples": [
      true
     ],
     "description": "If true, record in stereo.\nDefault is `false`."
    },
    "format": {
     "anyOf": [
      {
       "type": "string",
       "const": "wav"
      },
      {
       "type": "string",
       "const": "mp3"
      },
      {
       "type": "string",
       "const": "mp4"
      }
     ],
     "default": "wav",
     "examples": [
      "mp3"
     ],
     "description": "The format to record in. Can be `wav`, `mp3`, or `mp4`.\nDefault is `\"wav\"`."
    },
    "direction": {
     "anyOf": [
      {
       "type": "string",
       "const": "speak"
      },
      {
       "type": "string",
       "const": "listen"
      }
     ],
     "default": "speak",
     "examples": [
      "speak"
     ],
     "description": "Direction of the audio to record: \"speak\" for what party says, \"listen\" for what party hears.\nDefault is `\"speak\"`."
    },
    "terminators": {
     "type": "string",
     "default": "#",
     "examples": [
      "#"
     ],
     "description": "String of digits that will stop the recording when pressed. Default is `\"#\"`."
    },
    "beep": {
     "anyOf": [
      {
       "type": "boolean"
      },
      {
       "$ref": "#/$defs/SWMLVar"
      }
     ],
     "default": false,
     "examples": [
      true
     ],
     "description": "Play a beep before recording.\nDefault is `false`."
    },
    "input_sensitivity": {
     "anyOf": [
      {
       "type": "number"
      },
      {
       "$ref": "#/$defs/SWMLVar"
      }
     ],
     "default": 44,
     "examples": [
      44
     ],
     "description": "How sensitive the recording voice activity detector is to background noise.\nA larger value is more sensitive. Allowed values from 0.0 to 100.0.\nDefault is `44.0`."
    },
    "initial_timeout": {
     "anyOf": [
      {
       "type": "number"
      },
      {
       "$ref": "#/$defs/SWMLVar"
      }
     ],
     "default": 4,
     "examples": [
      4
     ],
     "description": "Time in seconds to wait for the start of speech.\nDefault is `4.0` seconds."
    },
    "end_silence_timeout": {
     "anyOf": [
      {
       "type": "number"
      },
      {
       "$ref": "#/$defs/SWMLVar"
      }
     ],
     "default": 5,
     "examples": [
      5
     ],
     "description": "Time in seconds to wait in silence before ending the recording.\nDefault is `5.0` seconds."
    },
    "max_length": {
     "anyOf": [
      {
       "type": "number"
      },
      {
       "$ref": "#/$defs/SWMLVar"
      }
     ],
     "examples": [
      60
     ],
     "description": "Maximum length of the recording in seconds."
    },
    "status_url": {
     "type": "string",
     "examples": [
      "https://example.com/recording-status"
     ],
     "description": "URL to send recording status events to."
    }
   },
   "unevaluatedProperties": {
    "not": {}
   },
   "description": "Record the call audio in the foreground, pausing further SWML execution until recording ends.\nUse this, for example, to record voicemails.\nTo record calls in the background in a non-blocking fashion, use the record_call method.",
   "title": "record"
  }
 },
 "required": [
  "record"
 ],
 "unevaluatedProperties": {
  "not": {}
 },
 "title": "Record object"
}
```

