# Step 2: reliable player history capture

The implementation is staged and offline-verified. **It is not installed or gameplay-qualified.** Start with [REPORT.md](REPORT.md), the exact selection in [checkpoint.json](checkpoint.json), and the remaining [test card](TEST_CARD.md). Step 1 is accepted as completed by the user; this task implements step 2 only.

Selected package: `candidate_04/package`, with 51 Core files and three replacements. The selected archive comes from `archive_02`; the exact 148-source compile is `compile_04`. Existing registration, installed names, HS1 saved fields and catalogue indices are preserved.

The source tools are engineering records, not one-command setup instructions. They refuse occupied outputs; some bind the selected candidate explicitly. Do not rerun them to overwrite evidence or assume a higher numbered candidate is selected. Game-derived catalogues, save projections, compiled scripts, archive contents and candidates are local ignored evidence. A clean Git checkout cannot regenerate these without their pinned local inputs.

No tool in this task deploys, launches the game, modifies a save, resets a quest or imports another player's history. The installed predecessor remains `QP2_QUEST_HISTORY_AUTOLOAD` in [current-state](../../docs/knowledge/current-state.md).
