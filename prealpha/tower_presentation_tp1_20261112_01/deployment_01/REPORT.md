# TP1 candidate 02 installed

The user explicitly answered “yes” to installing the staged candidate. **TP1_FPP_HANDBACK_DIAGNOSTIC**, candidate 02, is installed over RD1. The transaction completed at `2026-11-12T23:23:01.4601457Z` (18:23:01 Toronto). No game was launched and no saves were edited.

[Installed manifest](installed_manifest_01.json) SHA-256: `D1EFF6EA9B2A98FE1C92C90576D8DCA1BF9A6E371818C68E046966FC90F95A4E`. [Explicit authorization](authorization_01.json).

The two replaced paths are `r6/scripts/PTFR_Consolidated/PTFR_RestrictionsR1.reds` and `r6/scripts/PTFR_Consolidated/PTFR_LoadingCoverLC1.reds`. The other 49 Core paths, the 1,742-member archive, XL registrations, Machine Gun resume route and global-latest snapshot loader are unchanged.

The 148-source compilation and 18 deployment/recovery fixture actions remain bound to these exact inputs. A fresh authorized [preflight](preflight_02.json), [installation](install.json), [verification](verify.json) and [rollback readiness check](rollback_readiness.json) passed. All 51 Core paths and 26 dependencies match their expected hashes.

All **361 save files** retained exact names, sizes and hashes across installation. Required external dependencies retained exact hashes; other unmanaged game files retained names, sizes, timestamps and reparse metadata. That is not a claim that every unrelated file was content-hashed. Only the two authorized script paths were replaced. The predecessor and successor copies remain in `../recovery/core_presentation_tp1_01/`, with a committed receipt. File rollback does not undo saved gameplay.

The arms handback is a candidate repair awaiting visual confirmation. The fast-travel changes are diagnostics, not a confirmed blackout fix. Follow the [focused test card](../TEST_CARD.md): AutoSave-2, genuine Tower completion, inspect arms before any car/reload workaround, then one fast travel. Machine Gun's accepted fixture does not need repetition.
