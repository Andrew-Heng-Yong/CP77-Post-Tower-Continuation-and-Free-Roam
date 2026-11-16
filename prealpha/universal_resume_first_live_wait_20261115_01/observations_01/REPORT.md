# Manual Save 31 qualifies as the first timer fixture

15 November 2026 at 10:43:13 Toronto time. The user's new normal manual save records `Over the Edge` and its El Capitan wait objective as Active. It has `q307_ready=1`, no recorded point of no return or Tower cleanup, and `mq049_started=1`. The save body is 4,652,669 bytes and matched SHA-256 `2E0F3C99AF3E98601CFC6363BBC068635D0C50ABB32F8E81B2A57B056B02F43D` before and after the read. [Saved-state check](../run_04/assessment.json)

The original Falco phase at `[0,2,82,4,9,3,64,12]` holds node 28 in slot 2333. Its node-instance key `5C744DEF0000001C` resolves to timer `1E88A`. The native clock in the save is 7,224,999 game seconds and the deadline is 7,311,387. That leaves **86,388 game seconds**, or 23 hours, 59 minutes and 48 seconds, of the authored 24-hour wait.

The main quest still has the original phase registrations for nodes 11 and 12. In Reyes's phase, node 23 still waits for `mq049_falco_done`, and node 18 still listens for the original Streetkid phone choice. The save contains five registrations across these three addresses and no additional private body registration. Both Reyes listeners belong in the handoff state. [Exact registrations](../run_04/assessment.json) · [Current provider proof](../run_sources_01/source_assessment.json)

**PASS for the pre-Tower save fixture.** The native registration and timer records establish the selected pending stage in the save. The actual cutoff, support ownership, handoff and post-Tower save and reload are pending.
