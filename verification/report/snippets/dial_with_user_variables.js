// Browser SDK v4 dial with userVariables. Shape verified from the published types (sdk_facts.md Item 3).
// Live delivery location of userVariables in the webhook: not yet observed (see A5).
const call = await client.dial("/private/salesgod-outbound", {
  audio: true,
  video: false,
  userVariables: { to: "+15615550123", crm_call_id: "c-123" },
});
call.status$.subscribe((s) => console.log("status", s));
