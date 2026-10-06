# Discrepancies

No live behavior was observed in this run, so this file lists only differences between sources (documentation versus documentation, documentation versus the published SDK, and customer assumptions versus documentation). Live observations will add rows when the harness runs against a Space.

| # | Topic | Side 1 | Side 2 |
|---|---|---|---|
| 1 | Parallel destination cap | Customer reports a 20-destination limit for `connect.parallel` | No limit appears in the SWML connect page or the SWML JSON schema (no `maxItems`). `evidence/docs/swml_facts.json` item 1 |
| 2 | `connect.status_url` | Public connect page documents `status_url` (event `calling.call.connect`). `evidence/docs/swml/public_swml_connect.md` | The SWML JSON schema connect definitions list `call_state_url` but not `status_url`. `evidence/docs/swml/mcp_swml_schema_connect_record.md` |
| 3 | Signature header casing | SWML webhook security guide: `X-Signalwire-Signature`, `X-Signalwire-SHA256-Signature`. `evidence/docs/swml/public_swml_webhook_security.md` | SDK docs: `X-SignalWire-Signature`, `X-SignalWire-Sha256-Signature`. `evidence/docs/swml/sdk_webhook_signature_validation.md`. HTTP headers are case-insensitive; the validator reads them that way |
| 4 | `record` direction values | Public record_call page: `speak`, `listen`, `both` | SWML cheatsheet and reference: `speak`, `hear`, `both`. `evidence/docs/swml_facts.json` item 2 gaps |
| 5 | Guest token authentication | One doc: `POST /api/fabric/guests/tokens` with a SAT | Another doc: with the project API token. `evidence/docs/rest_facts.json` 2_fabric_subscribers |
| 6 | `vars.userVariables` in SWML fetch | Customer expectation and SWAIG examples show `vars.userVariables` | SWML document-fetch payload docs do not list `vars` on the initial fetch and do not mention `userVariables`. `evidence/docs/swml_facts.json` item 5 |
| 7 | REST recording callback location | SDK-level docs put `status_url` in `calling.record` params | The Calling REST API reference retrieved shows no verbatim curl for `calling.record`. `evidence/docs/rest_facts.json` 1_calling_rest_api gaps |
| 8 | Retry behavior | cXML documents status callback retries (3 attempts) and 2 s / 5 s timeouts | SWML documents only an approximate 5 s wait and a fallback URL; no retry counts. `evidence/docs/swml/public_swml_webhook_reliability.md` |
