# 12 November 2026, 18:25 Tower presentation test

The user reports that the arms stayed invisible and fast travel again left the world and menus black. They waited before closing the game. The installed TP1 candidate 02 compiled at launch. All 51 Core paths and 26 required dependencies match its installed manifest. Times below are Toronto local time. [Exact observation and log hashes](session.json) · [Installed manifest](../../deployment_01/installed_manifest_01.json)

| Time | Logged observation |
| --- | --- |
| 18:28:58 | Native `q307_done` and `q307_finished` reached 1. |
| 18:30:14–17 | The first-person handback event was queued. Stock hand attachment refresh was requested, then confirmed as continuation reached Ready. |
| 18:30:20 | The capture saw `Items.HolsteredFists` and stock fists, with the RightArm item attached and no pending spawn. |
| 18:31:27 | Fast travel started from Little China dataterm 05 to the stadium. |
| 18:31:32 | V was at the stadium. The map/menu flag cleared. The mod's setup popup was absent and the sampled loading layer had zero controllers at both travel captures. The HUD root reported visible after travel. |
| 18:31:52 | A game fact was still updating, 25 seconds after travel started. |
| 18:32:31–35 | RED4ext logged normal shutdown. No crash report from this session was present in the local queue. |

The arm repair failed its visual test. The handback log confirms queuing, and the attachment log confirms the item in the slot. Neither reports the native event's final rendering state. The mesh probe enumerates only components castable to `MeshComponent`; its zero matches on the RightArm item do not establish that the visible body or arm geometry is absent.

The trip moved V, but the trace never recorded `native-finished` before shutdown, about 64 seconds after departure. All three travel flags were false in the two samples. Those are point samples, and the callback trace has post-Tower admission guards. The native loading or presentation handoff is the next point to trace. The captures leave unobserved fade and render paths open. It does not demonstrate that the sampled loading layer was absent throughout the trip or that any other installed mod caused the blackout. The matching native script shows that travel requests teleportation before the native UI start notification, and the loading-finished listener schedules the post-travel autosave. [Prior source review](../../REPORT.md)

This review wrote only workspace evidence and the current-state pointer. The original candidate and its installation records remain pinned.
