"""Verify and stage the consolidated Tower recovery installation."""

import argparse
from binascii import crc_hqx
from copy import deepcopy
from datetime import datetime
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess

from build_scripts import HERE, EXPECTED_DONORS, R1, R3, common


PRE = HERE.parent
PREVIOUS = 'QP2_JOHNNY_LOAD_REPAIR'
EPOCH = 'QP2_TOWER_RECOVERY'
SCHEMA = 'PTFR_TOWER_RECOVERY_CORE_V1'
ARCHIVE = 'archive/pc/mod/zzzz_PTFR_Combined.archive'
XL = ARCHIVE + '.xl'
CHANGES = {ARCHIVE, XL, R1, R3}
BRUISE = r'towercontinued\recovery\bruise_clear.questphase'
PARENT = r'ep1\quest\ep1.quest'
TEMPLATE = PRE / 'johnny_load_crash_20261111_01/deploy_core.ps1'
TEMPLATE_SHA = '8C94862FC57931194D6892B2B485C8E155F1CAC1903D1323DE6BB2E5F1E9D7C5'
TEMPLATE_MANIFEST_SHA = 'A18B646B307FE336F4D34BDFD01676322E0368C40204AA1C0CE92BF36FB79DB0'
MANIFEST = HERE / 'core_manifest_01.json'
INSTALLER = HERE / 'deploy_core_02.ps1'
DEPLOYMENT = HERE / 'deployment_02'
JOURNAL = HERE / 'recovery/core_tower_recovery_02/journal.json'
FIXTURES = HERE / 'fixtures/deployment_02'
sha = common.digest
read = common.read_json
write = common.write_json


def load_graph_reader():
    path = PRE / 'phone_support_ph1/model.py'
    spec = importlib.util.spec_from_file_location('graph_reader', path)
    reader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reader)
    return reader


def verify_bruise_graph(archive_output, proof):
    reader = load_graph_reader()
    graph_path = archive_output / 'bruise_clear.questphase.json'
    scene_path = archive_output / 'q307_09_cutscene.scene.json'
    assert sha(graph_path) == proof['graph_json_sha256']
    assert sha(scene_path) == proof['source_scene_json_sha256']
    donor, = [entry for entry in reader.walk(read(scene_path))
              if entry.get('$type') == 'questCharacterManagerVisuals_SetBrokenNoseStage']
    assert donor['brokenNoseStage'] == 'CCBN_FinalScene'
    root = read(graph_path)['Data']['RootChunk']
    assert not root.get('phasePrefabs')
    graphs = reader.model(graph_path)
    assert set(graphs) == {'root'}
    graph = graphs['root']
    assert graph['edges'] == [
        (0, 'Out', 1, 'In'), (1, 'False', 2, 'In'), (1, 'True', 5, 'In'),
        (2, 'Out', 3, 'In'), (3, 'Out', 4, 'In'), (4, 'Out', 5, 'In'),
    ]
    assert [graph['nodes'][i]['$type'] for i in range(6)] == [
        'questInputNodeDefinition', 'questConditionNodeDefinition', 'questPauseConditionNodeDefinition',
        'questCharacterManagerNodeDefinition', 'questFactsDBManagerNodeDefinition', 'questOutputNodeDefinition',
    ]
    expected_facts = {
        'q307_done': 1, 'q307_finished': 1, 'q307_active': 0, 'q307_2079': 1,
        'q307_main_game_killed': 1, 'q307_ep1_killed': 1, 'q305_johnny_scene_active': 0,
        'PostTowerFreeRoamActive': 1, 'PTFRP0_DR13': 1, 'PTFRPA2_ControlReady': 1, 'PTFRPA2_Fault': 0,
        'PTFRRecovery_BruiseReady': 1, 'PTFRRecovery_BruiseApplied': 0,
    }
    atoms = list(reader.walk(graph['nodes'][2]['condition']))
    conditions = [x for x in atoms if x.get('$type') == 'questVarComparison_ConditionType']
    assert {x['factName']: x['value'] for x in conditions} == expected_facts
    assert len(conditions) == len(expected_facts) and all(x['comparisonType'] == 'Equal' for x in conditions)
    assert graph['nodes'][2]['condition']['operation'] == 'AND'
    receipt_check, = [x for x in reader.walk(graph['nodes'][1])
                      if x.get('$type') == 'questVarComparison_ConditionType']
    assert (receipt_check['factName'], receipt_check['value'], receipt_check['comparisonType']) == (
        'PTFRRecovery_BruiseApplied', 1, 'Equal')
    visual, = [x for x in reader.walk(graph['nodes'][3])
               if x.get('$type') == 'questCharacterManagerVisuals_SetBrokenNoseStage']
    assert {**donor, 'brokenNoseStage': 'CCBN_Disabled'} == visual
    writes = [x for x in reader.walk(graph['nodes']) if x.get('$type') == 'questSetVar_NodeType']
    assert len(writes) == 1
    assert (writes[0]['factName'], writes[0]['value'], writes[0]['setExactValue']) == ('PTFRRecovery_BruiseApplied', 1, 1)
    return {'stage_before': 'CCBN_FinalScene', 'stage_after': 'CCBN_Disabled', 'edges': graph['edges'],
            'guard': expected_facts, 'native_ack': writes[0]['factName']}


def ep1_bindings(source):
    # Every literal EP1-root occurrence must be accounted for in the pinned
    # layout. A differently formatted binding or scope alias needs review.
    occurrences = list(re.finditer(r'ep1[\\/]+quest[\\/]+ep1\.quest\b', source, re.IGNORECASE))
    if not occurrences:
        return []
    phases = source.split('\nquest:', 1)[-1] if not source.startswith('quest:') else source
    matches = re.findall(
        r'(?m)^    - path: (\S+)\r?\n      parent: ep1\\quest\\ep1\.quest\r?\n'
        r'      input:\r?\n        node: \[1\]\r?\n        socket: Out\s*$', phases,
    )
    assert len(matches) == len(occurrences), 'Unsupported EP1 root binding format'
    return matches


def stage_xl(game, output, native_ids):
    old = (game / XL).read_bytes()
    newline = b'\r\n' if b'\r\n' in old else b'\n'
    entry = newline.join(x.encode() for x in (
        f'    - path: {BRUISE}', f'      parent: {PARENT}', '      input:',
        '        node: [1]', '        socket: Out', '',
    ))
    anchor = b'streaming:' + newline
    assert old.count(anchor) == 1 and entry not in old
    new = old.replace(anchor, entry + anchor, 1)
    assert new.replace(entry, b'') == old
    before = []
    after = []
    hashes = {}
    for root in ('archive/pc', 'red4ext/plugins'):
        for path in sorted((game / root).rglob('*.xl')):
            common.plain(path, game)
            hashes[path.relative_to(game).as_posix()] = sha(path)
            installed = path.read_text(encoding='utf-8-sig')
            before.extend(ep1_bindings(installed))
            after.extend(ep1_bindings(new.decode('utf-8-sig')) if path == game / XL else ep1_bindings(installed))
    assert after.count(BRUISE) == 1 and [p for p in after if p != BRUISE] == before
    generated = {path: crc_hqx((path + ':1').encode(), 65535) for path in after}
    assert len(generated) == len(after) == len(set(generated.values()))
    assert set(generated.values()).isdisjoint(native_ids)
    output.write_bytes(new)
    return {'generated_node_id': generated[BRUISE], 'xl_inputs': hashes, 'previous_phase_bindings': len(before)}


def verify_timeline(r3, donor_r3):
    def section(s, start, end):
        return s.split(start, 1)[1].split(end, 1)[0]

    for start, end in (
        ('class ProfileDefinition', 'class ProfileCatalogue'),
        ('private func UpgradeImplantProfile(', 'public func Poll('),
        ('private func RefundOne(', 'private func Total('),
    ):
        assert section(r3, start, end) == section(donor_r3, start, end), start
    old_fields = re.findall(r'private persistent let (\w+): (\w+)', donor_r3)
    new_fields = re.findall(r'private persistent let (\w+): (\w+)', r3)
    assert [field for field in new_fields if field in old_fields] == old_fields
    assert set(new_fields).difference(old_fields) == {
        ('recoveryClockStarted', 'Bool'), ('recoveryStartSeconds', 'Int32'), ('recoveryDays', 'Int32'),
    }
    assert re.findall(r'quests\.SetFact\(([^;]+)\);', r3) == ['n"PTFRRecovery_BruiseReady", 1']
    assert 'this.enabled && this.vitalsRequested && this.stage >= 3' in r3
    assert '(!this.vitalsRequested || (IsDefined(this.physical) && this.physical.VitalsReady()))' in r3
    assert 'this.pool, -excess, player, false, false' in r3
    assert 'if NotEquals(this.pool, gamedataStatPoolType.Health)' in r3
    for setting, value in {
        'DurationDays': '30', 'BruiseDays': '14', 'StartingHealth': '25.00', 'RecoveredHealth': '125.00',
        'StartingStamina': '25.00', 'RecoveredStamina': '75.00',
    }.items():
        assert re.search(r'func ' + setting + r'\(\) -> \w+ \{ return ' + re.escape(value) + r'; \}', r3)
    assert 'let days = (nowSeconds - startSeconds) / 86400;' in r3
    assert 'return days > savedDays ? days : savedDays;' in r3
    assert 'func Curve(progress: Float) -> Float { return progress; }' in r3
    # Reference timeline checks exercise the pinned formula and boundary
    # values. Native GameTime and StatPool execution require an in-game run.
    anchor = 740000
    elapsed = lambda now, saved: max(saved, (now - anchor) // 86400)
    samples = [(0, 0, 0), (14 * 86400 - 1, 0, 13), (14 * 86400, 0, 14),
               (17 * 86400, 14, 17), (3 * 86400, 17, 17), (31 * 86400, 17, 31)]
    for offset, saved, expected in samples:
        assert elapsed(anchor + offset, saved) == expected
    milestones = {}
    for day in (0, 13, 14, 15, 30, 31):
        progress = min(day, 30) / 30
        milestones[day] = {
            'health': round(25 + 100 * progress, 4), 'stamina': round(25 + 50 * progress, 4),
            'bruise_eligible': day >= 14,
        }
    assert milestones[0]['health'] == milestones[0]['stamina'] == 25
    assert milestones[30] == milestones[31] == {'health': 125, 'stamina': 75, 'bruise_eligible': True}
    return {'timeline_cases': samples, 'milestones': milestones, 'runtime': 'UNVERIFIED'}


ARCHIVE_GUARD = """function CheckArchiveInputs {
 if($fixture -and $manifest.archive_inputs.Count -eq 0 -and $manifest.xl_inputs.Count -eq 0){return}
 $archives=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
 $xls=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
 foreach($relative in @('archive/pc','red4ext/plugins')){
  $root=Safe $game $relative;$tree=TreeSnapshot $root
  foreach($entry in $tree.files){
   $ext=[IO.Path]::GetExtension($entry.path)
   if($entry.kind -eq 'REPARSE_NOT_FOLLOWED' -and (($entry.attributes -band [long][IO.FileAttributes]::Directory) -or $ext -in @('.archive','.xl'))){throw ('Linked archive input refused: '+$entry.path)}
   if($entry.kind -ne 'file'){continue}
   if($ext -ieq '.archive'){[void]$archives.Add($relative+'/'+$entry.path)}
   if($ext -ieq '.xl'){[void]$xls.Add($relative+'/'+$entry.path)}
  }
 }
 if(!$archives.SetEquals([string[]]@($manifest.archive_inputs|ForEach-Object path)) -or !$xls.SetEquals([string[]]@($manifest.xl_inputs.Keys))){throw 'Archive/XL inventory changed since readback'}
 # Each path already matched the enumerated in-root inventory. Allow normal
 # mod filenames here without expanding the managed write-path grammar.
 foreach($row in $manifest.archive_inputs){
  $f=Get-Item -LiteralPath (Beneath $game (Join-Path $game $row.path))
  if($f.Length -ne $row.bytes -or $f.LastWriteTimeUtc.Ticks -ne $row.mtime_utc_ticks){throw ('Archive changed after provider audit: '+$row.path)}
 }
 foreach($relative in $manifest.xl_inputs.Keys){CheckFile (Beneath $game (Join-Path $game $relative)) $manifest.xl_inputs[$relative]}
}
"""


def stage(attempt, archive_attempt):
    assert not MANIFEST.exists() and not INSTALLER.exists()
    assert sha(common.BASELINE) == common.BASELINE_HASH
    assert sha(TEMPLATE) == TEMPLATE_SHA and sha(TEMPLATE.parent / 'core_manifest_01.json') == TEMPLATE_MANIFEST_SHA
    baseline = read(common.BASELINE)
    assert baseline['core_epoch'] == PREVIOUS
    game = Path(baseline['game_root'])
    candidate = HERE / f'candidate_{attempt:02}'
    package = candidate / 'package'
    compile_file = HERE / f'compile_{attempt:02}/result.json'
    archive_output = HERE / f'archive_{archive_attempt:02}'
    archive_file = archive_output / 'zzzz_PTFR_Combined.archive'
    archive_report = archive_output / 'archive_readback.json'
    compiled, script_proof, archive_proof = read(compile_file), read(candidate / 'verification.json'), read(archive_report)
    assert compiled['status'] == script_proof['compile'] == archive_proof['status'] == 'PASS'
    assert archive_proof['members'] == baseline['archive_payloads'] + 1 and archive_proof['added_depot'] == BRUISE
    assert sha(archive_file) == archive_proof['after_archive_sha256']
    assert sha(game / 'r6/logs/redscript_rCURRENT.log') == compiled['registry_sha256']
    assert sha(candidate / 'overlay' / R1) == EXPECTED_DONORS[R1]
    for rel in (R1, R3):
        assert sha(candidate / 'overlay' / rel) == compiled['staged_hashes'][rel] == script_proof['script_hashes'][rel]
    assert not package.exists()
    for row in baseline['core_files'] + baseline['required_files']:
        path = game / row['path']
        common.plain(path, game)
        assert sha(path) == row['sha256'] and path.stat().st_size == row['bytes'], path

    graph_check = verify_bruise_graph(archive_output, archive_proof)
    donor_r3 = Path(script_proof['donor']) / 'overlay' / R3
    assert sha(donor_r3) == EXPECTED_DONORS[R3]
    timeline_check = verify_timeline((candidate / 'overlay' / R3).read_text(encoding='utf-8'),
                                     donor_r3.read_text(encoding='utf-8'))
    (package / XL).parent.mkdir(parents=True)
    xl_check = stage_xl(game, package / XL, set(archive_proof['native_root_ids']))
    files = []
    for row in baseline['core_files']:
        rel = row['path']
        destination = package / rel
        if rel != XL:
            if rel == ARCHIVE:
                source = archive_file
            elif rel in (R1, R3):
                source = candidate / 'overlay' / rel
            else:
                source = game / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            assert sha(destination) == sha(source), rel
        files.append({'path': rel, 'before': row['sha256'], 'before_bytes': row['bytes'],
                      'after': sha(destination), 'after_bytes': destination.stat().st_size})
    assert len(files) == 51 and {row['path'] for row in files if row['before'] != row['after']} == CHANGES
    semantics = HERE / 'scope_review.json'
    write(semantics, {'status': 'VERIFIED_OFFLINE', 'changed_paths': sorted(CHANGES), 'core_paths': len(files),
                      'bruise': graph_check, 'archive_xl': xl_check, 'recovery': timeline_check})
    proofs = [common.BASELINE, compile_file, candidate / 'verification.json', candidate / 'recovery.patch', archive_report, semantics]
    manifest = {
        'schema': SCHEMA, 'component': 'Core', 'source_epoch': EPOCH, 'predecessor_epoch': PREVIOUS,
        'scope': 'Post-Tower cyberware treatment, 30-day vitals recovery and day-14 bruise reset.',
        'game_root': str(game), 'save_root': baseline['save_root'], 'package_root': str(package),
        'process_names': read(TEMPLATE.parent / 'core_manifest_01.json')['process_names'],
        'files': files, 'changing_paths': sorted(CHANGES), 'required_files': baseline['required_files'],
        'protected_saves': [], 'working_save_files': [],
        'proofs': [{'path': str(path), 'sha256': sha(path)} for path in proofs],
        'compile_inputs': {str(game / rel): digest for rel, digest in compiled['input_pins'].items()},
        'archive_inputs': archive_proof['archive_inputs'], 'xl_inputs': xl_check['xl_inputs'],
        'zip': '', 'zip_sha256': None,
    }
    write(MANIFEST, manifest)
    return manifest


def write_installer():
    assert not INSTALLER.exists() and sha(TEMPLATE) == TEMPLATE_SHA
    script = TEMPLATE.read_text(encoding='utf-8-sig')
    for old, new in (
        ('# The Johnny presentation REDscript is the only game write for this load repair.',
         '# The combined archive, its registration and the two restriction scripts are the only game writes.'),
        (TEMPLATE_MANIFEST_SHA, sha(MANIFEST)),
        ('PTFR_JOHNNY_LOAD_REPAIR_CORE_V1', SCHEMA),
        ("$manifest.source_epoch -cne 'QP2_JOHNNY_LOAD_REPAIR'", f"$manifest.source_epoch -cne '{EPOCH}'"),
        ("$manifest.predecessor_epoch -cne 'QP2_REED_CRASH_AND_JOHNNY_WORLD'", f"$manifest.predecessor_epoch -cne '{PREVIOUS}'"),
        ('recovery/core_johnny_load_01', 'recovery/core_tower_recovery_02'),
        ("Safe $worker 'readiness.json'", "Safe $worker 'readiness_02.json'"),
        ("$wanted=@('r6/scripts/PTFR_Consolidated/PTFR_JohnnyVoiceJV1.reds')",
         '$wanted=@(' + ','.join(f"'{path}'" for path in sorted(CHANGES)) + ')'),
        ('$changes.Count -ne 1', '$changes.Count -ne 4'),
        ('Core51/one-file Johnny presentation scope drift', 'Core51/Tower recovery scope drift'),
        ('function CheckPackage {\n CheckCompileInventory', ARCHIVE_GUARD + 'function CheckPackage {\n CheckCompileInventory\n CheckArchiveInputs'),
    ):
        script = common.one(script, old, new)
    with INSTALLER.open('x', encoding='utf-8', newline='\n') as out:
        out.write(script)


def run_fixtures(manifest):
    assert not FIXTURES.exists()
    powershell = shutil.which('pwsh')
    assert powershell
    cases = {
        'exact_rollback': [('Preflight', 'PREFLIGHT_READY'), ('Install', 'INSTALLED_VERIFIED'),
                           ('Verify', 'VERIFIED_AFTER'), ('ValidateRollback', 'ROLLBACK_READY'),
                           ('Rollback', 'ROLLED_BACK_VERIFIED'), ('Verify', 'VERIFIED_BEFORE', '-ExpectedState', 'Before')],
        'interrupted_pair': [('Install', 72, '-FailurePoint', 'CrashAfterSecondReplace'),
                             ('Recover', 'RECOVERED_BEFORE'), ('Verify', 'VERIFIED_BEFORE', '-ExpectedState', 'Before')],
        'before_receipt': [('Install', 72, '-FailurePoint', 'CrashBeforeReceipt'),
                           ('Recover', 'RECOVERED_BEFORE'), ('Verify', 'VERIFIED_BEFORE', '-ExpectedState', 'Before')],
        'game_running': [('Install', 1, '-FixtureProcesses', 'Cyberpunk2077')],
    }
    actions = []
    for case, operations in cases.items():
        root = FIXTURES / case
        game, saves, package = (root / p for p in ('game', 'saves', 'package'))
        data = deepcopy(manifest)
        data.update(game_root=str(game), save_root=str(saves), package_root=str(package),
                    proofs=[], compile_inputs={}, archive_inputs=[], xl_inputs={})
        exact = case == 'exact_rollback'
        for row in data['files']:
            path = row['path']
            before = (game / path)
            after = (package / path)
            before.parent.mkdir(parents=True, exist_ok=True)
            after.parent.mkdir(parents=True, exist_ok=True)
            if exact:
                shutil.copyfile(Path(manifest['game_root']) / path, before)
                shutil.copyfile(Path(manifest['package_root']) / path, after)
                assert (sha(before), sha(after)) == (row['before'], row['after'])
            else:
                before.write_text('old ' + path, encoding='utf-8')
                after.write_text(('new ' if path in CHANGES else 'old ') + path, encoding='utf-8')
                row.update(before=sha(before), before_bytes=before.stat().st_size,
                           after=sha(after), after_bytes=after.stat().st_size)
        for row in data['required_files']:
            path = game / row['path']
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(row['path'], encoding='utf-8')
            row.update(sha256=sha(path), bytes=path.stat().st_size)
        save = saves / 'FixtureSave/sav.dat'
        save.parent.mkdir(parents=True)
        save.write_bytes(b'preserve this save')
        external = game / 'ExternalMod/keep.dat'
        external.parent.mkdir()
        external.write_bytes(b'preserve this external file')
        if exact:
            extra = game / 'archive/pc/mod/!_Fixture.archive'
            extra.write_bytes(b'preserve the archive with a punctuation prefix')
            registry = extra.with_suffix('.archive.xl')
            registry.write_bytes(b'# preserve this ArchiveXL file')
            data['archive_inputs'] = [
                {'path': path.relative_to(game).as_posix(), 'bytes': path.stat().st_size,
                 'mtime_utc_ticks': path.stat().st_mtime_ns // 100 + 621355968000000000}
                for path in (extra, game / ARCHIVE, game / 'archive/pc/mod/LizziesBDs.archive')
            ]
            data['xl_inputs'] = {p.relative_to(game).as_posix(): sha(p) for p in (registry, game / XL)}
        fixture_manifest = root / 'manifest.json'
        write(fixture_manifest, data)
        for action, expected, *flags in operations:
            result = subprocess.run(
                [powershell, '-NoProfile', '-File', str(INSTALLER), '-Action', action,
                 '-FixtureRoot', str(root), '-FixtureManifest', str(fixture_manifest),
                 '-FixtureManifestSHA', sha(fixture_manifest), *flags],
                capture_output=True, encoding='utf-8', errors='replace', timeout=60,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if isinstance(expected, int):
                assert result.returncode == expected, (case, action, result.stdout, result.stderr)
                status = None
            else:
                assert result.returncode == 0, (case, action, result.stdout, result.stderr)
                status = json.loads(result.stdout)['status']
                assert status == expected, (case, action, status)
            actions.append({'fixture': case, 'action': action, 'status': status, 'returncode': result.returncode})
        assert all(sha(game / row['path']) == row['before'] for row in data['files'])
        assert all(sha(game / row['path']) == row['sha256'] for row in data['required_files'])
        assert save.read_bytes() == b'preserve this save'
        assert external.read_bytes() == b'preserve this external file'
        if case == 'game_running':
            assert not (root / 'recovery').exists()
    return actions


def record(attempt, archive_attempt):
    manifest = read(MANIFEST)
    receipt = read(JOURNAL)
    journal_text = receipt['payload_json']
    assert sha256(journal_text.encode()).hexdigest().upper() == receipt['payload_sha256']
    journal = json.loads(journal_text)
    assert journal['manifest_sha256'] == sha(MANIFEST) and journal['state'] == 'INSTALLED_VERIFIED'
    assert set(journal['completed_paths']) == CHANGES
    assert read(DEPLOYMENT / 'verify.json')['status'] == 'VERIFIED_AFTER'
    assert read(DEPLOYMENT / 'rollback_readiness.json')['status'] == 'ROLLBACK_READY'
    before, after = journal['protection_before'], journal['protection_after']
    assert before['saves']['tree_sha256'] == after['saves']['tree_sha256']
    assert before['unmanaged']['tree_sha256'] == after['unmanaged']['tree_sha256']
    assert before['dependencies'] == after['dependencies']
    assert journal['save_writes'] == journal['game_launches'] == 0
    game = Path(manifest['game_root'])
    files = [{'path': row['path'], 'bytes': row['after_bytes'], 'sha256': row['after']} for row in manifest['files']]
    assert all(sha(game / row['path']) == row['sha256'] for row in files + manifest['required_files'])
    compile_file = HERE / f'compile_{attempt:02}/result.json'
    archive_output = HERE / f'archive_{archive_attempt:02}'
    archive = read(archive_output / 'archive_readback.json')
    out = DEPLOYMENT / 'installed_manifest_01.json'
    assert not out.exists()
    write(out, {
        'schema': 1, 'recorded_date': datetime.fromisoformat(journal['updated_utc']).astimezone().date().isoformat(),
        'core_epoch': EPOCH,
        'predecessor_epoch': PREVIOUS, 'authorization': 'User requested joint installation after implementing recovery.',
        'archive_payloads': archive['members'], 'archive_sha256': archive['after_archive_sha256'],
        'core_files': files, 'required_files': manifest['required_files'],
        'game_root': manifest['game_root'], 'save_root': manifest['save_root'],
        'source_candidate': str(Path(manifest['package_root']).parent),
        'archive_source': str(archive_output / 'archive_source'),
        'predecessor_manifest': str(common.BASELINE), 'predecessor_manifest_sha256': common.BASELINE_HASH,
        'core_transaction': str(MANIFEST), 'core_transaction_sha256': sha(MANIFEST),
        'installed_receipt': str(JOURNAL), 'installed_receipt_sha256': sha(JOURNAL),
        'post_install_verification': str(DEPLOYMENT / 'verify.json'),
        'rollback_readiness': str(DEPLOYMENT / 'rollback_readiness.json'),
        'compile_result': str(compile_file), 'compile_sources': read(compile_file)['source_count'],
        'changed_paths': sorted(CHANGES), 'unchanged_core_paths': len(files) - len(CHANGES),
        'save_files_preserved': sum(x['kind'] == 'file' for x in after['saves']['files']),
        'save_tree_sha256': after['saves']['tree_sha256'], 'gameplay': 'UNVERIFIED',
    })
    print(f"Recorded the verified installation and {read(out)['save_files_preserved']} preserved save files.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'record'))
    parser.add_argument('--scripts', type=int, default=1)
    parser.add_argument('--archive', type=int, default=1)
    args = parser.parse_args()
    if args.action == 'record':
        record(args.scripts, args.archive)
        return
    if MANIFEST.exists():
        assert sha(MANIFEST) == read(HERE / 'readiness.json')['manifest_sha256']
        manifest = read(MANIFEST)
    else:
        manifest = stage(args.scripts, args.archive)
    write_installer()
    actions = run_fixtures(manifest)
    fixtures = HERE / 'fixture_results_02.json'
    scope = HERE / 'scope_review.json'
    write(fixtures, {'status': 'PASS', 'manifest_sha256': sha(MANIFEST),
                     'installer_sha256': sha(INSTALLER), 'actions': actions})
    write(HERE / 'readiness_02.json', {
        'status': 'READY_NOT_INSTALLED', 'manifest_sha256': sha(MANIFEST), 'installer_sha256': sha(INSTALLER),
        'fixture_result': fixtures.name, 'fixture_result_sha256': sha(fixtures),
        'scope_review': scope.name, 'scope_review_sha256': sha(scope),
    })
    print(f'Verified four-file overlay and {len(actions)} transaction fixture actions.')


if __name__ == '__main__':
    main()
