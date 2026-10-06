# SWML

`inbound_ring_group.json`: parallel ring of Subscriber addresses with a voicemail branch on `connect_result`. Built from documented methods; not yet exercised live.

Outbound authorization SWML is generated per request by the backend: it reads the destination from userVariables, refuses any number not on the allow list, and returns a connect to that number. See snippets/outbound_authorization.py.
