---
source: api_spec_signalwire_rest.json :: SWML Webhook; api_fabric.json :: External SWML Handlers; SDK ref swml_scripts.create
retrieved_via: mcp__SignalWire_Knowledge__last_resort_search (collection signalwire_unified_v3)
fetched_at: 2026-10-06T15:23:11Z
note: 
---

# POST /api/fabric/resources/swml_webhooks "Create SWML webhook"
"Creates a resource that requests calling or messaging SWML from your server when the handler runs."
Request body: `name`; `used_for` ("Indicates whether this SWML Webhook handles inbound calls or inbound messages"); `primary_request_url` (string, required); `primary_request_method`; `fallback_request_url`; `fallback_request_method`; `status_callback_url`; `status_callback_method`.
Responses: 201, 401, 404, 422, 500

# api_fabric.json "External SWML Handlers": GET/POST /api/fabric/resources/external_swml_handlers, DELETE/GET/PATCH /:id
Fields: fallback_request_method (Required. One of: GET, POST), fallback_request_url, name (Maximum 50), primary_request_method (Required), primary_request_url (Required), script_type, status_callback_method (Required), status_callback_url, type. "Handled by `API::Fabric::Resources::SwmlWebhooksController`."

# SWML Script: SDK ref "Reference: `POST /api/fabric/resources/swml_scripts`" example `client.fabric.swml_scripts.create(name="my-item")`
# GET /api/fabric/resources/{id}/addresses (SDK list_addresses)
# api_fabric.json Alias Addresses: GET/POST /api/fabric/addresses/alias ... Fields: channels, codecs, context (Required), display_name (Required), name (Required, Maximum 256), resource_id (Required), type
# Dashboard validation: Fabric Addresses `channels`: "valid selections are audio, video, or messaging"
# GET /api/fabric/addresses "List Resource Addresses from a Client" (SAT auth)
