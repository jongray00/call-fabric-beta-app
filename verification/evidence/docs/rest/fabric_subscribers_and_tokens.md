---
source: api_spec_signalwire_rest.json :: Subscribers + Subscriber Tokens; https://signalwire.com/docs/apis/authorization
retrieved_via: mcp__SignalWire_Knowledge__last_resort_search (collection signalwire_unified_v3)
fetched_at: 2026-10-06T15:23:11Z
note: Verbatim OpenAPI descriptions
---

# POST /api/fabric/resources/subscribers  "Create Subscriber"
Request body: `password` ("Defaults to a secure random password if not provided."), `email` (string, required), `first_name`, `last_name`, `display_name`, `job_title`, `timezone`, `country`, `company_name`.
Responses: 201, 401, 404, 422, 500. Scopes: Voice, Messaging, Fax, or Video.

# GET /api/fabric/resources/subscribers  "List Subscribers"  Responses: 200, 401, 404, 500
# GET /api/fabric/resources/subscribers/{id}/addresses (SDK ref listAddresses)

# DELETE /api/fabric/resources/subscribers/{id}  "Delete Subscriber"
"Deletes a persistent Subscriber resource by ID. Use it when the user identity should no longer exist in the project; temporary Guest and Invite Tokens expire independently and are not deleted through this operation."
Responses: 204, 401, 404, 500

# POST /api/fabric/subscribers/tokens  "Create Subscriber token"
"Creates a Subscriber Access Token (SAT) for a known Subscriber, identified by `reference`, and optionally updates that subscriber's profile. ... Tokens expire after two hours by default; bind one to a client with `fingerprint` and `sat:refresh` when that client should refresh its own access, or use Refresh Subscriber token from your backend."
Request body:
- `reference` (string, required): A string that uniquely identifies the subscriber. Often it's an email, but can be any other string.
- `expire_at` (integer): A unixtime ... at which the token should no longer be valid. Defaults to 'two hours from now'
- `application_id`: The ID of the application that the token is associated with.
- `password` (string): Set or update the subscriber's password. ...
- `fingerprint` (string): Binds the token to a specific device or browser session ... [truncated in index]
- `scope` (string): Grants the token's holder permission to refresh it directly from the ... [truncated in index]
- `first_name`, `last_name`, `display_name`, `job_title`, `time_zone`, `country`, `company_name`
- `region` (string): A routing override that controls which regional cluster the SDK connects to.
Responses: 200, 401, 404, 422, 500

# POST /api/fabric/subscribers/tokens/refresh  "Refresh Subscriber token"
"Exchanges a valid refresh token for a new Subscriber Access Token (SAT) and a new refresh token. ... The new access token is valid for 2 hours, and the new refresh token is valid for 2 hours and 5 minutes.
This operation consumes the `refresh_token` returned by Create Subscriber token."
Request body: `refresh_token` (required). Responses: 201, 401, 404, 422, 500

# POST /api/fabric/guests/tokens  "Create Subscriber guest token"
"Creates a temporary guest Subscriber token limited to the resource addresses in `allowed_addresses`. ... The token expires after two hours by default"
Request body: `allowed_addresses` (array, required): "List of up to 10 UUIDs representing the allowed Fabric addresses."; `expire_at`; `region`; `ch`.

# Authorization page (https://signalwire.com/docs/apis/authorization)
"**How to obtain:** Call the Create Subscriber Token endpoint using Basic Auth."
curl -X POST https://your-space.signalwire.com/api/fabric/subscribers/tokens -H 'Authorization: Basic <Base64(YourProjectID:YourAPIToken)>' -d '{"reference": "user@example.com", "expire_at": 1725513600}'
"Bearer tokens expire. Once they do, requests return `401 Unauthorized` and you'll need a fresh token."
Guest Token section: "They're created from an existing SAT ... Call the Create Guest Embed Token endpoint using a SAT." (example uses `Authorization: Bearer <subscriber_access_token>` against /api/fabric/guests/tokens; this conflicts with the API spec text "authenticate this request with a project API token")

# Browser SDK v4 refresh semantics (docs:fern/products/browser-sdk/.../EmbedTokenCredentialProvider/refresh.mdx)
"When not provided and the SAT includes a `sat:refresh` scope, the SDK automatically refreshes via Client Bound SAT (DPoP) without developer intervention."
"When not provided and no refresh scope is present, the SDK uses the initial credentials for the entire session lifetime."
