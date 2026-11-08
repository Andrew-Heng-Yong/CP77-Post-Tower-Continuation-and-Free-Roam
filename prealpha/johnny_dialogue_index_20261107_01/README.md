# Dialogue index for post Tower review

The selected Step 2 successor and current search commands are in [johnny_dialogue_index_20261107_02](../johnny_dialogue_index_20261107_02/README.md). This directory preserves the original verified HH1 snapshot [index_02/dialogue.sqlite3](index_02/dialogue.sqlite3), its [manifest](index_02/database_manifest.json) and the historical commands below.

The [Step 1 completion follow-up](../johnny_dialogue_coverage_20261107_01/REPORT.md) identified additional English subtitle providers and voiceset dispatch sources. The [verified successor report](../johnny_dialogue_index_20261107_02/REPORT.md) records the completed extension and its limits, including the corrected subtitle-provider denominator. This directory's database and verification remain preserved. Step 3 has not started.

English was selected for searchable dialogue text. The index preserves both male and female lipsync-name fields, player gender masks, subtitle variants, embedded localization signatures and other embedded locales. Context output marks db_db entries as debug drafts.

Run these commands from the repository root. They query the local index. Context queries also read retained source exports and check their hashes.

    & 'C:/Users/Ayong/.local/bin/python3.14.exe' -X utf8 -B prealpha/johnny_dialogue_index_20261107_01/search.py --speaker johnny --scope CURRENT_PTFR_PAYLOAD --limit 5

    & 'C:/Users/Ayong/.local/bin/python3.14.exe' -X utf8 -B prealpha/johnny_dialogue_index_20261107_01/search.py --speaker v --addressee johnny --scope CURRENT_PTFR_PAYLOAD --limit 5

    & 'C:/Users/Ayong/.local/bin/python3.14.exe' -X utf8 -B prealpha/johnny_dialogue_index_20261107_01/search.py --speaker johnny --text know --scope CURRENT_PTFR_PAYLOAD --limit 5

Use the returned item_key with --context and an optional --depth from 0 to 5. Context includes the event payload and timing, actors, resolved animation-resource table entries, adjacent nodes, conditions, choices, socket stamps, scene metadata and localization candidates.

The --kind option accepts dialogue, choice, cue, stored, conversation, script or all. Default searches include dialogue events and choices. The stored kind exposes screenplay lines without retained event references. Use --actor JOHNNY with --kind cue to inspect presentation events associated with Johnny.

Each result gives its scene depot, provider archive, source hash, graph and node identity, text-source category and structural entry names. CURRENT_PTFR_PAYLOAD identifies private scenes in the current payload. REFERENCE_CENSUS identifies resources captured from the first reference pass. GLOBAL_CENSUS_UNCLASSIFIED retains the rest of the identified scene census for availability review. Those categories include stored and inactive branches.

Choice labels use embedded en_us localization variants. Spoken dialogue prefers external subtitle variants. An embedded English fallback is explicitly labelled as a candidate. Unresolved text retains its original identifiers and locale records. The [report](REPORT.md) records the measured scope and remaining limits.

The index is an offline source snapshot. Step 3 reviews route eligibility, indirect V reactions and proposed cuts using the indexed evidence. The task tools use preserved output names. A fresh capture or rebuild needs a reviewed successor workspace.
