---
source: api_spec_signalwire_rest.json :: Recordings; api_spec_compatibility.json :: Recordings; api_laml.json; cXML Record page
retrieved_via: mcp__SignalWire_Knowledge__last_resort_search (collection signalwire_unified_v3)
fetched_at: 2026-10-06T15:23:46Z
note: 
---

# GET /api/relay/rest/recordings "List recordings" (Voice scope). Responses: 200, 401, 404, 422, 500
# GET /api/relay/rest/recordings/{id} "Get recording"
# DELETE /api/relay/rest/recordings/{id} "Delete recording": "Permanently deletes one voice call recording by ID." Responses: 204, 401, 404, 422, 500
# Compatibility: GET /api/laml/2010-04-01/Accounts/:project_id/Recordings (index), GET/DELETE .../Recordings/:id (api_laml.json: "Requires an API token with the `calling` scope.")
  List params: DateCreated, DateCreated<, DateCreated>, CallSid, ConferenceSid, Page, PageSize ("Default is 50, maximum is 1000."), PageToken
  DELETE /Accounts/{AccountSid}/Recordings/{Sid}: "returns no body on success. This removes the recording media without deleting its call or conference record."
# Compatibility POST /Accounts/{AccountSid}/Calls/{CallSid}/Recordings/{Sid} "Update a Recording": "Pauses, resumes, or stops a recording on an active call. When pausing, choose whether the elapsed interval becomes silence in the media or is skipped."
# Retention: cXML Record page (https://signalwire.com/docs/compatibility-api/cxml/reference/voice/record): "Recordings remain stored indefinitely. To delete a recording, use the appropriate API call from the Compatibility API."
# HIPAA page: "Manage recordings through the REST API — list them to audit access, and delete them once their retention period expires."
