"""Read back an authorized QR13 installation and record current authority.

Writes workspace reports/pointers only. No deployment, game API, build or save write.
"""
from pathlib import Path
import datetime, hashlib, json
from prepare import H, W, meta, read, sha, write


def main():
    out = H / 'deployment_01'
    assert not (out / 'verification.json').exists(), 'Fresh evidence only'
    mp = H / 'core_manifest_02.json'; m = read(mp)
    game, saves = Path(m['game_root']), Path(m['save_root'])
    b = read(H / 'baseline.json')
    prep = read(H / 'completion.json')
    checks = {}
    def ck(label, condition):
        checks[label] = bool(condition)
        assert condition, label

    receipts = {name: read(out / (name + '.json')) for name in ['preflight','install','verify','rollback_ready']}
    for name, status in [('preflight','PREFLIGHT_READY'), ('install','INSTALLED_VERIFIED'),
                         ('verify','VERIFIED_AFTER'), ('rollback_ready','ROLLBACK_READY')]:
        ck(name + '_receipt', receipts[name]['status'] == status)
    ck('installer_and_manifest_still_reviewed', sha(H / 'deploy_core.ps1') == '8DE067549901CD3AD6E41AE88F35DBAE4967DC6DEDAADADFF79CF6BB8E2A9A08'
       and sha(mp) == '6963CB2679BF3D0ABD9F34A662C437A185D0FBA10873913B6AEC7EC4F76299C0')
    ck('all_preparation_artifact_pins_unchanged', all(sha(r['path']) == r['sha256'] for r in prep['artifacts'].values()))
    ck('all51_core_hashes', all(sha(game / r['path']) == r['after'] for r in m['files']))
    ck('all26_dependencies_and_diagnostics', all(sha(game / r['path']) == r['sha256'] for r in m['required_files']))
    changed = [r for r in m['files'] if r['before'] != r['after']]
    ck('three_reviewed_replacements_only', len(changed) == 3)
    recovery = H / 'recovery/core_qr13_02_01'
    envelope = read(recovery / 'journal.json')
    ck('journal_integrity', hashlib.sha256(envelope['payload_json'].encode()).hexdigest().upper() == envelope['payload_sha256'])
    journal = json.loads(envelope['payload_json'])
    ck('journal_committed_correct_manifest', journal['state'] == 'INSTALLED_VERIFIED'
       and journal['manifest_sha256'] == sha(mp) and journal['operation'] == 'Install')
    ck('journal_write_set', set(journal['completed_paths']) == {r['path'] for r in changed})
    backup_rows = []
    for r in changed:
        for side, field in [('old','before'), ('new','after')]:
            p = recovery / side / r['path']
            ck('backup_' + side + '_' + r['path'], sha(p) == r[field])
            backup_rows.append({'side': side, 'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size})
    old_protection = journal['protection_before']; new_protection = journal['protection_after']
    for section in ['saves','unmanaged']:
        ck('installer_' + section + '_unchanged', old_protection[section]['tree_sha256'] == new_protection[section]['tree_sha256'])
    ck('installer_dependencies_unchanged', old_protection['dependencies'] == new_protection['dependencies'])
    current_meta = meta(game)
    metadata_changes = sorted(k for k in set(current_meta) | set(b['game_metadata']) if current_meta.get(k) != b['game_metadata'].get(k))
    ck('full_game_metadata_only_three_replacements', set(metadata_changes) == {r['path'] for r in changed})
    current_saves = meta(saves)
    ck('all_save_metadata_unchanged', current_saves == b['save_metadata'])
    ck('all310_save_hashes_unchanged', all(sha(p) == s for p,s in b['save_sha256'].items()))
    ck('fresh_preflight_save_hashes_unchanged', all(sha(saves / r['path']) == r['sha256']
        for r in receipts['preflight']['protection']['saves']['files'] if r['kind'] == 'file'))
    managed = {r['path']: r for r in m['files']}
    for p, expected in m['compile_inputs'].items():
        relative = Path(p).relative_to(game).as_posix()
        if relative in managed:
            expected = managed[relative]['after']
        ck('compile_input_' + relative, sha(p) == expected)
    ck('QR13_evidence_and_candidate_metadata_unchanged', meta(H.parent / 'quest_restoration_qr13') == b['QR13_metadata'])
    ck('staged_package_and_ZIP_unchanged', all(sha(Path(m['package_root']) / r['path']) == r['after'] for r in m['files']) and sha(m['zip']) == m['zip_sha256'])
    ck('original_historical_source_proofs_unchanged', all(sha(r['path']) == r['sha256'] for r in m['proofs']))
    verification = {'status': 'PASS_QR13_INSTALLED_AND_PRESERVED', 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'checks': checks, 'core_epoch': 'QR13:02', 'manifest': str(mp), 'manifest_sha256': sha(mp),
        'managed_paths': 51, 'protected_dependencies': 26, 'save_files': len(b['save_sha256']),
        'changed': changed, 'game_metadata_changes': metadata_changes, 'backup_payloads': backup_rows,
        'diagnostics': 'QR10D01/D00E unchanged', 'compiled_cache_deployed': False,
        'game_launches': 0, 'save_or_fact_writes': 0, 'rollback_executed': False,
        'limits': ['Installed byte verification is not new-behavior gameplay or saved-owner proof.',
            'Nonmanaged game assets use complete metadata plus26 exact dependency pins; no claim of hashing every game asset.',
            'File rollback cannot undo QR13 execution in saves; save downgrade compatibility is unproved.']}
    write(out / 'verification.json', verification)
    installed = {'schema': 'PTFR_QR14_CURRENT_INSTALLED_V1', 'core_epoch': 'QR13:02', 'installed_utc': journal['updated_utc'],
        'authorization': 'User replied proceed after an explicit request for QR13 deployment approval.',
        'game_root': str(game), 'save_root': str(saves), 'core_source_epoch': str(H.parent / 'quest_restoration_qr13/source_epoch_02.json'),
        'core_source_epoch_sha256': sha(H.parent / 'quest_restoration_qr13/source_epoch_02.json'),
        'transaction_manifest': str(mp), 'transaction_manifest_sha256': sha(mp),
        'core_files': [{'path': r['path'], 'sha256': r['after'], 'bytes': r['after_bytes']} for r in m['files']],
        'required_files': m['required_files'], 'diagnostic_code_profile': 'QR10D01 candidate02 / D00E config unchanged',
        'archive_payloads': 1577, 'archive_sha256': managed['archive/pc/mod/zzzz_PTFR_Combined.archive']['after'],
        'recovery_root': str(recovery), 'verification': str(out / 'verification.json'), 'verification_sha256': sha(out / 'verification.json'),
        'receipt_files': {name: {'path': str(out / (name + '.json')), 'sha256': sha(out / (name + '.json'))} for name in receipts},
        'gameplay_qualification': 'No new Ronald/Brendan fixture READY; preserve accepted QR9-QR12 observations. No new runtime behavior tested.'}
    write(out / 'installed_manifest_01.json', installed)

    report = f'''# QR13:02 installed — QR14 authorized deployment

**INSTALLED_VERIFIED / VERIFIED_AFTER / ROLLBACK_READY.** The user's subsequent “proceed” authorized deployment after preparation. The game and REDlaunchers were closed naturally; none was launched or controlled.

Exactly three existing files changed: the combined archive, HistorySnapshotHS1 and SideJobsS23. All51 Core paths match QR13:02;48 other Core files, both validated diagnostic files,26 pinned dependencies and all{len(b['save_sha256'])} save files remain preserved. Full game metadata differs only at the three approved leaves. Offline compiled cache was not installed. No save/fact edits, quest execution, rebuild, release or publication occurred.

Archive SHA256: `{installed['archive_sha256']}`.
Installed manifest: [installed_manifest_01.json](installed_manifest_01.json).
Independent readback/preservation: [verification.json](verification.json), {len(checks)} checks.

Receipts: [fresh preflight](preflight.json), [install](install.json), [verify](verify.json), [rollback readiness](rollback_ready.json). Backups contain exact old/new bytes for all three replacements in `../recovery/core_qr13_02_01/`; the journal is committed. No rollback was executed. Preserve the recovery tree; file rollback is not save rollback.

The installed code contains prospective Ronald native consent/contact enrollment and the narrow earned peaceful final-Theo Brendan continuation. Source/package reviews and the fresh148-source integration compile remain accepted for their exact inputs. This deployment verifies files, not gameplay, actual saved owners or prefab refresh. Opaque machine-spot placement and prior unsupported histories remain unchanged limitations.

**Next:** the user may launch normally and continue ordinary gameplay. No CET command or repeated successful test is needed. No new quest test is qualified on the known fixtures; do not manufacture eligibility or repeat Bullets/Jinguji, Zane, Wilson, Cynthia, D00E or the two load checks. Report a genuine naturally available new Ronald offer or genuinely earned supported Brendan finale if encountered; qualify before a targeted capture.
'''
    (out / 'REPORT.md').write_text(report, encoding='utf-8')
    (out / 'HANDOFF.md').write_text('''# QR14 deployment continuation

QR13:02 Core is installed with explicit subsequent user approval. QR10D01/D00E diagnostics are unchanged. Read installed_manifest_01.json, verification.json and REPORT.md here; these supersede the preparation-only state in the parent immutable REPORT/HANDOFF/readiness/completion. Parent readiness remains READY_NOT_INSTALLED as a historical preparation proof required by the pinned installer; do not edit it to update installed status.

Fresh Preflight, Install, Verify and ValidateRollback passed. Exactly archive +HistorySnapshotHS1 +SideJobsS23 changed; all51 installed Core hashes,26 dependencies,310 save files and six old/new backup payloads verified. Full game metadata has only those three changes; no cache/build/game launch/save/fact or diagnostic changes occurred. Canonical current installed composite is installed_manifest_01.json, replacing old D00E whole-install hash assumptions (its QR8 pins are historical).

Rollback is prepared, not executed. Use the reviewed parent deploy_core.ps1 with its exact manifest02/receipt and game closed after separate rollback authority. Do not run older Core installers or diagnostic rollback manifests blindly; old diagnostics manifests pin QR8 and need a current compatible plan. File rollback cannot undo QR13 private saved state/rewards; no downgrade-save guarantee.

No new gameplay fixture READY. Preserve the user's prior successful tests and completed Skippy; no repeats. Known Brendan M23/M24 fallback/private-issued histories remain ineligible; Ronald disabled subscription alone does not prove unoffered/contact/owner state. Ordinary human gameplay may reveal genuine eligibility; qualify then issue a short manual S02/S06 card using unchanged validated sampler. Do not reset history/facts, replay an ending or invent owner introspection.

The148-source integration proof in parent verification/compile_01 corrected17 omitted runtime-registered LBD inputs; no rebuild/recompile is needed for unchanged bytes. QR13 resource reviews, opaque placement/saved-child refresh limits and remaining clock/combat/old-issued development blockers still apply. Next action is ordinary user-controlled play, not another audit or mandatory test.
''', encoding='utf-8')
    checkpoint = H / 'checkpoint.json'
    (out / 'checkpoint.before.json').write_bytes(checkpoint.read_bytes())
    state = W / 'docs/knowledge/current-state.md'
    (out / 'current-state.before.md').write_bytes(state.read_bytes())
    s = state.read_text(encoding='utf-8-sig')
    s = s.replace('Core installation updated 31 October 2026;', 'Core installation updated 3 November 2026;')
    s = s.replace('## Local installed successor: QR8:02 with QR10D01 diagnostics', '## Local installed successor: QR13:02 with QR10D01/D00E diagnostics')
    old = 'The sealed QR8:02 core is installed.'
    assert old in s
    s = s.replace(old, 'The sealed QR13:02 Core is installed through the user-authorized QR14 transaction. [Current installed manifest](../../prealpha/quest_restoration_qr14/deployment_01/installed_manifest_01.json), [deployment report](../../prealpha/quest_restoration_qr14/deployment_01/REPORT.md) and [preservation verification](../../prealpha/quest_restoration_qr14/deployment_01/verification.json) are authoritative. Exactly three Core leaves changed from QR8:02; all51 installed hashes,26 dependencies and310 save files verified, with rollback ready. No gameplay was launched or new behavior certified.')
    replacements = {
        '| Core source/package | `prealpha/quest_restoration_qr8/candidate_01/`; source epoch `source_epoch_02.json`, 1,577 archive payloads |': '| Core source/package | `prealpha/quest_restoration_qr13/candidate_01/`; source epoch `source_epoch_02.json` (QR13:02), 1,577 archive payloads |',
        '| Exact component manifests | Core: `prealpha/quest_restoration_qr9/worker_a/core_manifest_02.json`;': '| Exact component manifests | Current installed composite: `prealpha/quest_restoration_qr14/deployment_01/installed_manifest_01.json`; Core transaction: `prealpha/quest_restoration_qr14/core_manifest_02.json`;',
        '| Authorized deployment and installed assessment | [Deployment report](../../prealpha/quest_restoration_qr9/deployment_01/REPORT.md), [independent verification](../../prealpha/quest_restoration_qr9/deployment_01/verification.json) |': '| Authorized deployment and installed assessment | [QR14 deployment report](../../prealpha/quest_restoration_qr14/deployment_01/REPORT.md), [readback and preservation](../../prealpha/quest_restoration_qr14/deployment_01/verification.json) |',
        '| Install/verify/rollback-readiness receipts | `prealpha/quest_restoration_qr9/worker_a/deployment_01/` |': '| Install/verify/rollback-readiness receipts | `prealpha/quest_restoration_qr14/deployment_01/` — INSTALLED_VERIFIED / VERIFIED_AFTER / ROLLBACK_READY |',
        '| Archive SHA256 | `2AB35CC95931CD3C7BB2FB3A4C8B52746DE7847D42AE1DD3503A90A965FD2039` |': '| Archive SHA256 | `97D3C65BB72F4BA4F3BCB6AECDE9ABA105315D0340918F42590363F9F90A32BF` |',
        '| Core recovery | `prealpha/quest_restoration_qr9/worker_a/recovery/core_qr8_02_01/` |': '| Core recovery | `prealpha/quest_restoration_qr14/recovery/core_qr13_02_01/` — QR13→QR8 three-file recovery; earlier QR8 recovery remains historical |',
        'Current diagnostic rollback must use the QR11 receipt to restore B04 only.': 'Historical diagnostic rollback receipts pin the former QR8 Core; review a compatible current plan before any diagnostic rollback under QR13. The latest Core file rollback uses QR14 and restores only its three QR8 predecessors. Neither is authorized by a readiness receipt alone.'
    }
    for a, v in replacements.items():
        assert a in s, a
        s = s.replace(a, v)
    anchor = '\n## QR9 human quest assessment'
    assert anchor in s
    s = s.replace(anchor, '\n**Current installation supersession — 3 November:** the preparation-only QR13/QR14 paragraphs below remain dated evidence. QR13:02 is now installed; the latest [deployment handoff](../../prealpha/quest_restoration_qr14/deployment_01/HANDOFF.md) and mutable QR14 checkpoint select this state. Old QR11/D00E manifests describe their unchanged diagnostic bytes but contain obsolete QR8 whole-install pins; use the new installed composite for current verification. No new quest fixture is qualified and accepted gameplay tests are not repeated.\n' + anchor)
    state.write_text(s, encoding='utf-8')
    artifacts = {name: {'path': str(out / name), 'sha256': sha(out / name)} for name in
        ['preflight.json','install.json','verify.json','rollback_ready.json','verification.json','installed_manifest_01.json','REPORT.md','HANDOFF.md','checkpoint.before.json','current-state.before.md']}
    completion = {'status': 'QR13_02_INSTALLED_VERIFIED_ROLLBACK_READY', 'artifacts': artifacts,
        'installed': 'QR13:02 Core + unchanged QR10D01/D00E', 'preparation_completion_sha256': sha(H / 'completion.json'),
        'current_state': {'path': str(state), 'sha256': sha(state)}, 'changed_core_files': 3,
        'save_files_preserved': len(b['save_sha256']), 'game_launches': 0, 'save_or_fact_writes': 0,
        'rollback_executed': False, 'next': 'Ordinary human gameplay only; no immediate special test. Qualify genuine new behavior fixtures before capture.'}
    write(out / 'completion.json', completion)
    checkpoint.write_text(json.dumps({'state': completion['status'], 'completion': str(out / 'completion.json'),
        'completion_sha256': sha(out / 'completion.json'), 'installed': completion['installed'],
        'handoff': str(out / 'HANDOFF.md'), 'next': completion['next']}, indent=2) + '\n', encoding='utf-8')
    print({'status': completion['status'], 'checks': len(checks), 'save_files_preserved': len(b['save_sha256']),
        'game_metadata_changes': metadata_changes, 'report': str(out / 'REPORT.md')})


if __name__ == '__main__':
    main()
