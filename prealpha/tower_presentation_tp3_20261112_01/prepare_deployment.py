"""Bind the one-script successor to a fresh transaction and local package."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib
from capture import HERE, ROOT, BASELINE, BASELINE_SHA, sha, read, write, plain
from prepare import COVER, one

BASE = ROOT / 'prealpha/tower_presentation_tp2_20261112_01'
EPOCH = 'TP3_BOUNDED_PRESENTATION_HANDOFF'
BEFORE = 'TP2_RETAINED_PRESENTATION_REPAIR'
SCHEMA = 'PTFR_TP3_BOUNDED_PRESENTATION_HANDOFF_CORE_V1'
CHANGES = {COVER}
ARCHIVE = 'archive/pc/mod/zzzz_PTFR_Combined.archive'
PACKAGE = HERE / 'candidate_01/package'
MANIFEST = HERE / 'core_manifest_01.json'
INSTALLER = HERE / 'deploy_core.ps1'
DEPLOYMENT = HERE / 'deployment_01'
PS = Path(r'C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')

def exclusive(path, text):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        f.write(text)

def qualify(game, compiled):
    before = (game / COVER).read_text(encoding='utf-8')
    after = (PACKAGE / COVER).read_text(encoding='utf-8')
    assert compiled['status'] == 'PASS' and compiled['source_count'] == 148
    assert compiled['staged_hashes'][COVER] == sha(PACKAGE / COVER)
    for marker in ('SetFact(', 'persistent let', 'SetBool(', 'ActivateTPPRepresentationEvent()',
                   'DeactivateTPPRepresentationEvent()', 'RestorePreviousVisualState(', 'inkHideLoadingScreenDelayedEvent()'):
        assert before.count(marker) == after.count(marker), marker
    assert before.split('public func TraceFastTravel(', 1)[1].split('  // TP2:', 1)[0] == (
        after.split('public func TraceFastTravel(', 1)[1].split('  // Native arrival', 1)[0])
    assert before.split('public class SetupTickLC1', 1)[1] == after.split('public class SetupTickLC1', 1)[1]
    assert 'this.FinishBodyReturnTP3();\n    if !this.Required()' in after
    assert 'this.presentationRepairAt = now + 4.0;' in after
    assert 'this.TryEndingLoadingCleanup();\n    this.presentationRepairActor = player;' in after
    return {
        'status': 'PASS_STATIC_SCOPE_AND_COMPILE',
        'baseline_manifest_sha256': BASELINE_SHA,
        'candidate_manifest_sha256': sha(PACKAGE.parent / 'manifest.json'),
        'compile_sha256': sha(HERE / 'compile_01/result.json'),
        'changed_paths': sorted(CHANGES),
        'observed': 'TP2 passed all mandatory checks and stayed covered at 11/12 before representation activation.',
        'scope': 'Bound the optional presentation wait, isolate loading cleanup, and return the actor before rechecking setup.',
        'gameplay': 'PENDING'
    }

def main():
    assert sha(BASELINE) == BASELINE_SHA
    assert all(not p.exists() for p in (MANIFEST, INSTALLER, DEPLOYMENT, HERE / 'fixtures', HERE / 'recovery', HERE / 'deploy.py'))
    baseline = read(BASELINE)
    game = Path(baseline['game_root'])
    compiled = read(HERE / 'compile_01/result.json')
    candidate_manifest = PACKAGE.parent / 'manifest.json'
    after = {r['path']: r['sha256'] for r in read(candidate_manifest)['files']}
    for row in baseline['core_files'] + baseline['required_files']:
        path = game / row['path']
        plain(path)
        assert sha(path) == row['sha256'], path
    for rel, pin in compiled['input_pins'].items():
        assert sha(game / rel) == pin, rel
    for rel, pin in compiled['staged_hashes'].items():
        assert sha(PACKAGE / rel if (PACKAGE / rel).is_file() else game / rel) == pin, rel
    assessment = HERE / 'assessment_01.json'
    write(assessment, qualify(game, compiled))

    files = []
    for row in baseline['core_files']:
        p = PACKAGE / row['path']
        plain(p)
        assert sha(p) == after[row['path']]
        files.append({'path': row['path'], 'before': row['sha256'], 'before_bytes': row['bytes'],
                      'after': after[row['path']], 'after_bytes': p.stat().st_size})
    assert len(files) == 51 and {r['path'] for r in files if r['before'] != r['after']} == CHANGES
    assert {p.relative_to(PACKAGE).as_posix() for p in PACKAGE.rglob('*') if p.is_file()} == set(after)
    for folder in (DEPLOYMENT, HERE / 'fixtures', HERE / 'recovery'):
        folder.mkdir()
    zipfile = DEPLOYMENT / 'TP3_candidate_01.zip'
    with ZipFile(zipfile, 'x', ZIP_DEFLATED, compresslevel=6) as z:
        for row in files:
            z.write(PACKAGE / row['path'], row['path'])
    with ZipFile(zipfile) as z:
        assert len(z.namelist()) == 51 and set(z.namelist()) == set(after) and z.testzip() is None
        assert all(hashlib.sha256(z.read(r['path'])).hexdigest().upper() == r['after'] for r in files)
    zip_proof = DEPLOYMENT / 'zip_readback.json'
    write(zip_proof, {'status': 'PASS', 'files': 51, 'sha256': sha(zipfile)})
    proofs = [BASELINE, candidate_manifest, assessment, HERE / 'compile_01/result.json', zip_proof]
    write(MANIFEST, {
        'schema': SCHEMA, 'component': 'Core', 'source_epoch': EPOCH, 'predecessor_epoch': BEFORE,
        'scope': 'One-script fix for the setup cover waiting indefinitely after the job checks passed.',
        'game_root': str(game), 'save_root': baseline['save_root'], 'package_root': str(PACKAGE),
        'process_names': read(BASE / 'core_manifest_01.json')['process_names'], 'files': files,
        'changing_paths': sorted(CHANGES), 'required_files': baseline['required_files'],
        'protected_saves': [], 'working_save_files': [], 'zip': str(zipfile), 'zip_sha256': sha(zipfile),
        'proofs': [{'path': str(p), 'sha256': sha(p)} for p in proofs],
        'compile_inputs': {str(game / p): h for p,h in compiled['input_pins'].items()}
    })

    template = BASE / 'deploy_core.ps1'
    assert sha(template) == '993E65E947EE025F8596B45586F2D465ADC4B7FB3113D447D0BF39EF46ACA65F'
    source = template.read_text(encoding='utf-8-sig')
    for old, new in (
        ('# Replace exactly the two TP2 scripts after separate installation authorization.',
         '# Replace exactly the TP3 setup-cover script after installation authorization.'),
        (sha(BASE / 'core_manifest_01.json'), sha(MANIFEST)),
        ('PTFR_TP2_RETAINED_PRESENTATION_REPAIR_CORE_V1', SCHEMA),
        ("$manifest.source_epoch -cne 'TP2_RETAINED_PRESENTATION_REPAIR'", f"$manifest.source_epoch -cne '{EPOCH}'"),
        ("$manifest.predecessor_epoch -cne 'TP1_FPP_HANDBACK_DIAGNOSTIC'", f"$manifest.predecessor_epoch -cne '{BEFORE}'"),
        ('recovery/core_presentation_tp2_01', 'recovery/core_presentation_tp3_01'),
        (f"'{COVER}','r6/scripts/PTFR_Consolidated/PTFR_RestrictionsR1.reds'", f"'{COVER}'"),
        ('$changes.Count -ne 2', '$changes.Count -ne 1'),
        ('Core51/two-script TP2 presentation scope drift', 'Core51/one-script TP3 presentation scope drift')
    ):
        source = one(source, old, new)
    exclusive(INSTALLER, source)

    runner = BASE / 'deploy.py'
    assert sha(runner) == '923C478A62F6D36EB1C3746B5A1D048328B9B681C73B020FC0366707E54C41C9'
    source = runner.read_text(encoding='utf-8')
    start = source.index("        'crash_second':")
    end = source.index("        'crash_stage':", start)
    source = source[:start] + source[end:]
    for old, new in (
        ('TP2 fixture runner', 'TP3 fixture runner'),
        ('recovery/core_presentation_tp2_01', 'recovery/core_presentation_tp3_01'),
        ("'compile_03/result.json'", "'compile_01/result.json'"),
        ("'unchanged_core_paths': 49", "'unchanged_core_paths': 50"),
        ("'PENDING_TP2_FRESH_TOWER_ARMS_AND_FAST_TRAVEL_TEST'", "'PENDING_TP3_FRESH_TOWER_PRESENTATION_TEST'")
    ):
        source = one(source, old, new)
    exclusive(HERE / 'deploy.py', source)
    print('Prepared one-script transaction and read back all 51 package files.')

if __name__ == '__main__':
    main()
