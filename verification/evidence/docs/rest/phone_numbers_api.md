---
source: api_spec_signalwire_rest.json :: Phone Numbers, Phone Number Addresses; SDK phone-binding docs (signalwire-java:rest/docs/phone-binding.md, signalwire-perl:rest/docs/phone-binding.md); SDK ref set_swml_webhook
retrieved_via: mcp__SignalWire_Knowledge__last_resort_search (collection signalwire_unified_v3)
fetched_at: 2026-10-06T15:23:11Z
note: 
---

# GET /api/relay/rest/phone_numbers/search "Search phone numbers"
Params: `areacode`; `number_type` ("local or toll-free numbers. Defaults to local."); `starts_with` / `contains` / `ends_with` ("A string of 3 to 7 digits", mutually exclusive); `max_results` ("Upper limit of 100. Defaults to 50."); `region` (ISO 3166-2 alpha-2, local only); `city` (with region). Scope: Numbers. Responses: 200, 401, 500

# POST /api/relay/rest/phone_numbers "Purchase phone number"
"Purchases one available phone number and adds it to the project." Request body: `number` (string, required): "The phone number in E164 format." Responses: 200, 400, 401, 422, 500

# DELETE /api/relay/rest/phone_numbers/{id} "Release phone number"
"Releases a project-owned phone number by ID ... deleting a handler resource or removing its E911 assignment does not release the number." Responses: 204, 401, 404, 422, 500
Compatibility DELETE IncomingPhoneNumbers: "Note: Numbers cannot be released within a cooldown period after purchase." (409 listed)

# Handler binding (SDK docs)
Java phone-binding table: "| `RELAY_SCRIPT` | `relay_script` | `call_relay_script_url` | `swml_webhook` |" ; "| `LAML_WEBHOOKS` | `laml_webhooks` | `call_request_url` | `cxml_webhook` |"; also ai_agent/call_ai_agent_id, call_flow/call_flow_id, relay_application/call_relay_application, relay_topic/call_relay_topic, video_room/call_video_room_id.
"**`calling_handler_resource_id`** (where present in responses) is **server-derived** and read-only. Don't try to set it on update; the server computes it from the handler you chose."
"**Naming note on `LAML_WEBHOOKS`:** ... it produces a **cXML** (Twilio-compat) handler ... For SWML, use `RELAY_SCRIPT`."
Wire form: `update(pnSid, {"call_handler": "relay_script", "call_relay_script_url": "https://example.com/swml"})`
Python set_swml_webhook: "The server auto-creates a `swml_webhook` Fabric resource keyed off this URL. This is a typed wrapper over `update` that sets `call_handler` to `relay_script` and populates `call_relay_script_url` for you."
Perl summary: "`swml_webhook` and `cxml_webhook` Fabric resources are auto-materialized. Don't manually create them."

# POST /api/fabric/phone_number_addresses "Link a resource to a phone number" (Beta)
Body: `phone_number_id` or `number`; `resource_id` (required); `handler_type` (required): `calling` or `messaging`.
422 codes: `missing_required_parameter`, `invalid_parameter`, `provided_id_is_unrecognized`, `invalid_resource_type`, `already_assigned`.
"<Warning title="Beta">This API is in beta and may change.</Warning>"
