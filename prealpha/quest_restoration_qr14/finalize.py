"""Finish bounded preparation records after real read-only Preflight and preservation."""
from pathlib import Path
from prepare import H, W, read, sha, write

def main():
    ready = read(H / 'readiness.json'); preflight = read(H / 'preflight_01.json')
    preservation = read(H / 'preservation.json'); assessment = read(H / 'fixture_assessment.json')
    review = read(H / 'review_01/review.json'); controls = read(review['fixture_result'])
    assert ready['status'] == 'READY_NOT_INSTALLED'
    assert preflight['status'] == 'PREFLIGHT_READY'
    assert preservation['status'] == 'PASS_PREPARATION_PRESERVATION'
    assert ready['installer_sha256'] == sha(H / 'deploy_core.ps1')
    assert assessment['ready'] == []
    report = f'''# QR14 — QR13 deployment preparation complete

**READY for separately authorized deployment; NOT installed.** Real read-only preflight passed. Installed Core remains QR8:02 with unchanged QR10D01/D00E diagnostics. No game, save/fact, diagnostic or staged package was modified. No game launch/CUA, publication or quest replay occurred.

## Concrete deployment

`deploy_core.ps1` / `core_manifest_02.json` validate51 stable Core paths and replace exactly3 existing leaves: combined archive, HistorySnapshotHS1 and SideJobsS23.48 other Core paths stay exact. The installer preserves both diagnostic files, the Atelier correction and unrelated mods; it creates verified old/new backups before any replacement and supports Preflight, Install, Verify, ValidateRollback, Rollback and interrupted-transaction Recover.

Final installer SHA256: `{ready['installer_sha256']}`.
Manifest02 SHA256: `{ready['manifest_sha256']}`.
The unchanged QR13 ZIP SHA256 remains `B2BDC04BE7CF202047C3E7CF85F9BB3BD8F0D77B9D98ACA7C1377F5E5AD52EB8`.

[Exact commands, backup paths and rollback](DEPLOYMENT.md); [current human plan](MANUAL_TEST_PLAN.md); [readiness binding](readiness.json).

## Important compile correction

Independent review found17 runtime-registered Lizzie's Braindances sources omitted by QR13's131-source offline compile. The actual installed runtime log lists148 sources. A fresh workspace integration compile staged all148, overlaid the exact46 candidate managed scripts, passed exit0/Compilation complete with no warning/error lines, and preserved all151 installed source/compiler/cache inputs. Output SHA256: `6185E254BDB1F98A4371A0DEDB76E09D2958EF6006ECA5D5E8C8EABDE83E6F0F`.

The installer now checks complete source inventory across the enclosing r6/scripts and red4ext/plugins trees, refusing added/deleted/renamed sources, linked sources and directory links. Existing non-source framework log links are retained without following them.26 dependencies are exact-pinned, including the17 LBD sources. This is a compile-evidence/guard correction; QR13 runtime source, archive, ZIP and historical reports remain immutable. Knowledge pointers explicitly supersede the earlier complete-input claim.

## Validation

| Gate | Result and limits |
|---|---|
| Final full integration compile |148 sources /151 input pins; candidate46 linkage independently verified. Offline only. |
| Engine02 transaction matrix |52 checks /98 PowerShell actions PASS: normal install, caught/hard install/rollback interruptions and recovery, unknown/corrupt/source/dependency/save refusal, locks/reparse targets and actual Core51 integration. |
| Final engine03 controls |{len(controls['checks'])} independent checks /{controls['command_count']} actions PASS, including populated inventories, benign log links, source/link/drift refusal, hard interruption and final actual Core51 install/verify/rollback. |
| Protocol preservation |Independent exact comparison establishes engine02→03 changes only source-inventory link classification. The98-action matrix was not misrepresented as running engine03. Both source revisions/results remain preserved. |
| Real preflight |PREFLIGHT_READY, game/REDlaunchers closed, exact before/package/proof/input hashes, fresh recovery path. Read-only; actual game replacement permission not exercised. |
| Preservation |77 protected installed pins,310 save-file hashes, all game/save metadata, QR13 provider baseline metadata and all QR13 original metadata unchanged. Candidate51 and ZIP unchanged. |

Receipts: [composed fixture coverage](fixture_summary.json), [independent final review](review_01/review.json), [compile](verification/compile_01/result.json), [preflight](preflight_01.json), [preservation](preservation.json).

Initial engines, rejected link classification, failed reviewer fixture-construction/count/message assertions and intermediate receipts are retained. Their coverage is bounded to the source executed; final approval uses the corrected final controls. No unresolved technical deployment blocker remains in this pinned preparation.

## Save qualification

Reused204 QR12 current/backup locations:196 bodies still bind;8 changed bodies remain UNKNOWN. No save was reparsed or loaded. No newly qualified Ronald first-consent fixture was found: QR12 did not capture native known/offer/topic-counter facts; disabled subscription alone cannot establish no previous offer/refusal, exact Inactive contact or support-owning child refresh. Metadata/raw journals/facts do not prove actual saved-owner liveness. Known Brendan ManualSave23/24 fallback history/private Issued/Entered state remains ineligible for the strict earned final-Theo route.

[Fixture evidence and exact missing prerequisites](fixture_assessment.json) / [CSV](fixture_inventory.csv). No immediate special gameplay test is issued. Previously accepted Jinguji/Bullets/Zane/Wilson/Cynthia/D00E/load results and user-completed Skippy are not repeated.

## Remaining boundaries and next action

User approval is still required to install this three-file Core successor; this turn authorized preparation only. No rebuild of unchanged quest resources is needed. After approval, run fresh Preflight, Install, Verify and ValidateRollback with the exact commands in DEPLOYMENT.md. Keep game/launchers closed naturally.

Static/fixture readiness does not prove new Ronald/Brendan gameplay, saved-child graph/prefab refresh, actual executing ownership or opaque native placement. File rollback is not save rollback; newer private state/rewards are not undone or proven old-version-compatible by restoring files. Replacements are individually atomic, not a globally atomic three-file transaction; fixtures cover process interruption, not power loss. Ordinary unmanaged game files are protected through write-set containment/full metadata, not a SHA census of every game asset.
'''
    (H / 'REPORT.md').write_text(report, encoding='utf-8')
    handoff = '''# QR14 continuation

Preparation COMPLETE; QR13:02 NOT installed. Read REPORT.md, readiness.json, DEPLOYMENT.md and MANUAL_TEST_PLAN.md. User's "proceed" authorized deployment preparation, not the later installation. Do not install without explicit subsequent authority; once given, do not ask redundant approval.

Canonical final installer is deploy_core.ps1, manifest core_manifest_02.json, selected by readiness.json. Source remains exact QR13 source_epoch_02/candidate_01; no resource/package rebuild was performed. Only archive +HistorySnapshotHS1 +SideJobsS23 may change. Other48 Core paths, QR10D01/D00E sampler, Atelier, dependencies and saves stay protected.

Important corrected evidence: QR13 offline131-source compile omitted17 actually registered LBD sources. QR14/verification/compile_01 passed148-source current integration,151 pins, exact candidate46 overlay. Compiled SHA6185E254BDB1F98A4371A0DEDB76E09D2958EF6006ECA5D5E8C8EABDE83E6F0F. Historical QR13 evidence is unchanged; knowledge guide/current-state now record the boundary and corrected proof. Do not revert to a five-root compiler dependency list.

Final engine03 rejects added/deleted/source-linked/directory-linked REDscript inventory across both enclosing trees. Benign non-source framework log links are retained without following. Engine02 matrix52/98 plus independent final engine03 controls55/23 and exact protocol equivalence form explicit composed coverage; do not claim the broad matrix ran engine03. Failed setup prototypes and old engines remain preserved. Final real preflight and preservation PASS; no runtime writes, game launch, CUA or save changes.

For authorized installation, use exact DEPLOYMENT.md commands from workspace with pinned PowerShell7: fresh Preflight, Install with deployment_01/install.json, Verify, ValidateRollback. Default recovery is QR14/recovery/core_qr13_02_01 (fresh); do not delete occupied evidence. Real preflight did not test write permission in Program Files. On interruption preserve journal and follow Recover semantics (Install→QR8, Rollback→QR13) only after reviewing state/closure. File rollback never restores saves; no old-code compatibility proof for QR13-executed new state.

No special live fixture is READY. fixture_assessment.json binds204 existing QR12 locations (196exact/8changed), does not reparse or infer absent facts0. Ronald known/offer/counter were not captured; current subscription0 is insufficient and no executing-owner API is invented. Known Brendan M23/M24 fallback/Inactive/private issued states are ineligible. Do not reset histories, repeat The Tower or generate artificial eligibility. Existing Jinguji/Bullets/Zane/Wilson/Cynthia/D00E and both load checks stay closed; user reported Skippy done.

Next: obtain/observe explicit deployment authorization or continue only independent authorized preparation. After verified installation, ordinary user gameplay may provide genuine new eligible evidence; qualify before issuing a short S02/S06 manual card. Preserve Ronald native refusal/news clocks, Brendan earned-only/fresh exclusion and remaining unsupported clock/combat/old-issued cases from QR13. No broad audit, extra agents, unchanged rebuild or repeated successful gameplay is needed.
'''
    (H / 'HANDOFF.md').write_text(handoff, encoding='utf-8')
    names = ['REPORT.md','HANDOFF.md','DEPLOYMENT.md','MANUAL_TEST_PLAN.md','readiness.json','core_manifest_02.json',
        'deploy_core.ps1','test_deployment.py','fixture_summary.json','run_02_results.json','review_01/review.json',
        'review_01/final_controls_04_result.json','verification/compile_01/result.json','preflight_01.json','preservation.json',
        'fixture_assessment.json','fixture_inventory.csv','engine_01_to_02.json','engine_02_to_03.json',
        'prepare.py','compile_integration.py','assess_fixtures.py','seal_ready.py','verify_preservation.py','finalize.py']
    artifacts = {n: {'path': str(H / n), 'sha256': sha(H / n)} for n in names}
    completion = {'status': 'QR14_PREPARATION_COMPLETE_READY_NOT_INSTALLED', 'artifacts': artifacts,
        'installed': 'QR8:02 + QR10D01/D00E', 'staged': 'QR13:02 unchanged', 'real_preflight': 'PREFLIGHT_READY',
        'managed_paths': 51, 'replacements': 3, 'integration_sources': 148, 'compile_input_pins': 151,
        'protected_installed_union': 77, 'save_files_preserved': 310, 'new_ready_gameplay_fixtures': 0,
        'installations': 0, 'game_launches': 0, 'CUA_calls': 0, 'save_or_fact_writes': 0,
        'knowledge_updates': [{'path': str(W / 'docs/knowledge' / n), 'sha256': sha(W / 'docs/knowledge' / n)} for n in ['current-state.md','redscript-toolchain.md']],
        'next': 'Explicit user deployment approval, then exact guarded Preflight/Install/Verify/ValidateRollback. No immediate special gameplay test.'}
    write(H / 'completion.json', completion)
    write(H / 'checkpoint.json', {'state': completion['status'], 'completion': str(H / 'completion.json'),
        'completion_sha256': sha(H / 'completion.json'), 'handoff': str(H / 'HANDOFF.md'),
        'installed': completion['installed'], 'staged': completion['staged'], 'next': completion['next']})
    print({'status': completion['status'], 'proofs': len(artifacts), 'next': completion['next']})

if __name__ == '__main__':
    main()
