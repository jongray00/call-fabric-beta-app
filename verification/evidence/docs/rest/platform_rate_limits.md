---
source: https://signalwire.com/docs/platform/rate-limits (docs:fern/products/platform/pages/platform/core/rate-limits.mdx); locale_trust.json
retrieved_via: mcp__SignalWire_Knowledge__last_resort_search (collection signalwire_unified_v3)
fetched_at: 2026-10-06T15:23:46Z
note: 
---

## Voice
"View pricing and contact Support to increase calling throughput. Because faxes are sent via phone calls, the below rate limits apply to faxes as well."
| Calls | `1` call per second (CPS) |
| Backlog | `10,000` queued calls |

## Queue and backlog system
"When an application sends calls or messages to SignalWire at a rate exceeding the applicable rate limit, SignalWire **queues** these messages or calls in the order received. The **backlog** is the limit to the number of queued (pending) calls or messages. The Voice backlog and Messaging backlog are both `10,000` by default.
When the backlog for calls is full, SignalWire will stop adding additional calls to the Voice queue."
"If you would like to raise your Voice or Messaging backlog, fill out the Space Increase Request Form (https://forms.signalwire.me/Space-Increase-Request.html)."

## API
"Every HTTP request includes the user's current limit and remaining requests in its X-Header."
GET/DELETE: "Effectively unlimited"; POST/PUT/PATCH: "`13800` requests per `10` seconds"

## Phone number limits
"Requests for more than 1000 phone numbers require additional verification."

## locale_trust.json "Trust Call Backlog" (dashboard/UI strings)
"This number has exceeded the maximum allowed number of queued outbound calls. You can wait for some calls to send from your queue, or contact Support to increase your queue size if you require more."
"Your Space is currently in Trial and has reached its maximum allowed number of queued calls."

## pricing.json High Throughput Calling (US): "| 1 | $0 /month /each | | 2 to 20 | $15 /month /each | ... | 201 to 250 | $40 /month /each |" "Requires three month commitment. Set and billed independently for PSTN and SIP."
