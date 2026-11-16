# Verified Step 2 coverage successor

The selected dialogue index is [index_05/dialogue.sqlite3](index_05/dialogue.sqlite3). Its [manifest](index_05/database_manifest.json), [source verification](index_05/verification.json) and [command checks](index_05/cli_verification.json) identify the exact result. The previous index and unsuccessful preparation candidates remain preserved.

**Post-index installed delta:** JP1 now changes three private scenes in KOLD MIRAGE and Sweet Dreams. This database remains the verified pre-JP1 source snapshot. Use the [JP1 installed manifest](../johnny_dialogue_pilot_jp1/deployment_01/installed_manifest_01.json), [decision/readback report](../johnny_dialogue_pilot_jp1/REPORT.md) and candidate_03 sources for those scenes. `CURRENT_PTFR_PAYLOAD` remains capture provenance, not a statement that the indexed events still play in the installed pilot.

Current scope and work status: use the [Steps 1/2 audit](../johnny_dialogue_scope_audit_20261107_01/REPORT.md), [scope policy](../johnny_dialogue_scope_audit_20261107_01/scope_policy.json) and [active work ledger](../johnny_dialogue_scope_audit_20261107_01/active_work_ledger.json). They exclude q303 quest-owned occurrences and native q115 ending execution, protect the genuine Tower ending and close completed Step 2 tasks. Raw index counts and boundary queries include out-of-scope sources and historical task statuses. The database boundary table is not the active work queue.

Run these read-only commands from the repository root:

    & 'C:/Users/Ayong/.local/bin/python3.14.exe' -X utf8 -B prealpha/johnny_dialogue_index_20261107_02/search.py --speaker johnny --scope CURRENT_PTFR_PAYLOAD --limit 5

    & 'C:/Users/Ayong/.local/bin/python3.14.exe' -X utf8 -B prealpha/johnny_dialogue_index_20261107_02/search.py --speaker v --addressee johnny --scope CURRENT_PTFR_PAYLOAD --limit 5

    & 'C:/Users/Ayong/.local/bin/python3.14.exe' -X utf8 -B prealpha/johnny_dialogue_index_20261107_02/search.py --kind dispatch --speaker johnny --limit 5

    & 'C:/Users/Ayong/.local/bin/python3.14.exe' -X utf8 -B prealpha/johnny_dialogue_index_20261107_02/search.py --kind dispatch --actor PLAYER --scope CURRENT_PTFR_PAYLOAD --limit 5

    & 'C:/Users/Ayong/.local/bin/python3.14.exe' -X utf8 -B prealpha/johnny_dialogue_index_20261107_02/search.py --kind voice-tag --actor JOHNNY --limit 5

    & 'C:/Users/Ayong/.local/bin/python3.14.exe' -X utf8 -B prealpha/johnny_dialogue_index_20261107_02/search.py --kind sound --limit 5

    & 'C:/Users/Ayong/.local/bin/python3.14.exe' -X utf8 -B prealpha/johnny_dialogue_index_20261107_02/search.py --kind boundary --text SOURCE_SOCKET_INTERFACE_BOUNDARY --limit 5

Use a result's item_key with --context and optional --depth 0 through 5.

The kind option accepts dialogue, choice, cue, stored, conversation, script, dispatch, voice-tag, sound, metadata, boundary and all. Default searches return dialogue-event occurrences and choices. Stored lines have no retained playback event. Dispatch rows contain source call parameters and binding leads; their search text is not a spoken transcript. Player binding stays PLAYER_CONTEXT_REQUIRED until its voice context is established.

Source scopes such as CURRENT_PTFR_PAYLOAD and REFERENCE_CENSUS describe storage/capture provenance, not proven post-Tower execution. All 20 Johnny-reference dispatch results are raw source leads; six belong to excluded native q115 ending contexts. The remaining 14 still require caller qualification. Do not limit the project to private sources or globally exclude shared voiceset lines used by eligible callers.

Ordinary text searches use SQLite FTS5. Boundary text searches use a substring match over the hold details and category. Boundary filters accept text, scene and scope. AUXILIARY_SOURCE can be selected for voice tags, metadata and support evidence.

Dispatch context includes the exact caller node, graph conditions, entries, socket connections, prefab metadata and candidate voiceset entry links. A matched entry exposes structurally connected dialogue-event candidates with their source text and IDs. Binding, condition feasibility, provider selection and actual post-Tower execution still require review. Name matches without an actor binding remain separate entry leads.

Source context verifies the retained export hash. Sound context also shows its animation/actor ancestry. Boundary context retains decoding diagnostics and literal null socket endpoints without inventing an edge or transcript. The q303 decoding diagnostic is outside the required post-Tower work. Voice-tag context lists candidate scene providers; an empty list preserves a missing-provider boundary.

English dialogue uses exact-ID external subtitle variants, with explicitly labelled embedded English fallback candidates where necessary. Choices retain embedded locStore text. Male/female subtitle variants, both lipsync-name fields, gender masks and other embedded locales remain preserved. Debug drafts are labelled separately.

The [report](REPORT.md) records measured coverage and limits. The earlier handoff listed 41 additional English providers; identity qualification found 12 already indexed under resolved names, so this successor adds 29 and reuses those 12. Step 3 remains planning only. This task generated no review document or game patch.
