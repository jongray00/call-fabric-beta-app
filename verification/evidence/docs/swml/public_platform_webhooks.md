---
source: "https://signalwire.com/docs/platform/webhooks (docs:fern/products/platform/pages/platform/core/webhooks/index.mdx)"
retrieved_via: "mcp__SignalWire_Knowledge__search"
fetched_at: "2026-10-06T15:21:41Z"
note: "Verbatim chunk text as returned by the MCP vector search (signalwire_unified_v3 collection). Direct fetch of signalwire.com is blocked (403/EGRESS_BLOCKED)."
---

## Verify webhook signature

To verify webhooks that originated from SignalWire, SignalWire signs its requests with a digital HMAC security key. 
You can verify that the security key matches the key documented in your Dashboard's [API Credentials](https://my.signalwire.com?page=credentials) with the `validateRequest` method.

In the Dashboard, open **API Credentials**, find **Signing Key**, and select **Show** to reveal the key for the current project.

**Warning:** For production applications, it is extremely important to verify the webhook signature to ensure the requests are coming from SignalWire and not a malicious third party.

```js
import { validateRequest } from "@signalwire/js";

// prepare raw body for validation
app.use(express.json({
  verify: (req: any, _res, buf) => {
    req.rawBody = buf.toString();
  }
}));

app.post("/mywebhook", (req: any, res) => {
  const valid = validateRequest(
    "<SIGNING_KEY_FROM_Dashboard>",
    req.headers["x-signalwire-signature"] as string,
    "https://example.ngrok.io/mywebhook", //this should be the public-facing URL of your webhook handler
    req.rawBody
  );

  if (!valid) return res.status(401).send("Invalid signature");

  res.sendStatus(200);
});
```

## Status callbacks to keep track of events

| To track | Provide a callback URL on | States you'll receive |
| :--- | :--- | :--- |
| **Voice calls** | `call_state_url` on [`connect`](/docs/swml/reference/calling/connect) | `created`, `ringing`, `answered`, `ended` |
| **Messages** | `status_callback` on [`send_sms`](...), or `status_url` on [`reply`](...) | `queued`, `initiated`, `sent`, `delivered`, `undelivered`, `failed`, `read` |
| **Recordings** | `status_url` on [`record_call`](/docs/swml/reference/calling/record-call) | `recording`, `paused`, `finished`, `no_input`, `error` |

**Note:** For voice calls, `call_state_events` defaults to `['ended']` — set it explicitly to also receive `created`, `ringing`, and `answered`.

## Create a Resource for your webhook URL

In the SignalWire Dashboard, open the **My Resources** tab and click **+ Add**, then choose **SWML Script**.
Give the script a name, set **Handle Calls Using** to **External URL**, and enter your webhook URL in the **Primary Script URL** field. Click **Create** to save the Resource.
