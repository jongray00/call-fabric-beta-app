---
source: "https://signalwire.com/docs/compatibility-api/guides/webhooks and https://signalwire.com/docs/compatibility-api/guides/common-webhook-errors (cXML / Compatibility API, NOT SWML)"
retrieved_via: "mcp__SignalWire_Knowledge__search"
fetched_at: "2026-10-06T15:21:41Z"
note: "Verbatim chunk text as returned by the MCP vector search (signalwire_unified_v3 collection). Direct fetch of signalwire.com is blocked (403/EGRESS_BLOCKED)."
---

## How to Verify Webhooks (Compatibility API)

```js
import { RestClient } from "@signalwire/compatibility-api";

app.post("/mywebhook", (req, res) => {
  const valid = RestClient.validateRequest(
    "<--Signing Key copied from your credentials page-->",
    req.headers["x-signalwire-signature"],
    "https://example.ngrok.io/mywebhook",
    req.body
  );
});
```

This method responds with a boolean value. You can continue your application's logic in the truth case and return unauthorized for the false case.

## Parameters (URL fragment timeouts, Compatibility API webhooks)

| Parameter | Valid values | Default | Notes |
|-----------|--------------|---------|-------|
| Open Timeout (`ot`) | 100 - 10000 (ms) | 2000 | The timeout in milliseconds SignalWire will wait to establish its TCP connection to your web server. |
| Read Timeout (`rt`) | 100 - 15000 (ms) | 5000 | [...] |
| Total Time (`tt`) | 100 - 15000 (ms) | 15000 | The total time allowed for all timeouts including retries. If not set, the maximum limit is enforced. |

## HTML retrieval error (error code 11200)

HTML Retrieval Errors happen when there is a failure to retrieve the contents of the URL in your webhook. This indicates that SignalWire tried to reach your URL but did not receive a response before the connection timed out. Our current timeouts are 2 seconds for Connect and 5 seconds for Read.

If it's an action type of webhook, SignalWire won't attempt a retry but will go to the fallback URL (on inbound calls, can specify an action URL and a fallback URL). If it's a status callback webhook, SignalWire will retry up to two more times — three attempts in total.

If all retries fail, the callback is not delivered and no further notification is made — treat status callbacks as advisory and reconcile state via the REST API for critical workflows.
