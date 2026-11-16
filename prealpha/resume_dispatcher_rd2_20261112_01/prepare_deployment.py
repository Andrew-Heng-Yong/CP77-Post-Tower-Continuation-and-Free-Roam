"""Package and bind the qualified candidate without writing to the game."""
import hashlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from capture import HERE, ROOT, BASELINE, BASELINE_SHA, baseline, plain, read, sha, write
from prepare import ARCHIVE, HS1, S22, once

BASE = ROOT / 'prealpha/tower_presentation_tp3_20261112_01'
EPOCH = 'RD2_THE_GIG_REWARD_RESUME'
BEFORE = 'TP3_BOUNDED_PRESENTATION_HANDOFF'
SCHEMA = 'PTFR_RD2_THE_GIG_REWARD_RESUME_CORE_V1'
CHANGES = {ARCHIVE, HS1, S22}
PACKAGE = HERE / 'candidate_01/package'
MANIFEST = HERE / 'core_manifest_01.json'
INSTALLER = HERE / 'deploy_core.ps1'
DEPLOYMENT = HERE / 'deployment_01'
PS = Path(r'C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')

def exclusive(path, source):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(source)

def main():
    assert all(not p.exists() for p in (MANIFEST, INSTALLER, DEPLOYMENT, HERE/'fixtures', HERE/'recovery', HERE/'deploy.py'))
    previous, game = baseline()
    manifest_path = PACKAGE.parent / 'manifest.json'
    assessment_path = HERE / 'assessment.json'
    compiler_path = HERE / 'compile_01/result.json'
    assessment = read(assessment_path)
    candidate = read(manifest_path)
    compiled = read(compiler_path)
    assert candidate['baseline_manifest_sha256'] == BASELINE_SHA
    assert candidate['qualification'] == assessment['status'] == 'PASS_BOUNDED_OFFLINE'
    assert assessment['contract_sha256'] == sha(HERE / 'contract.json')
    assert compiled['status'] == 'PASS' and compiled['source_count'] == 148
    for p, h in compiled['input_pins'].items():
        assert sha(game / p) == h
    for p, h in compiled['staged_hashes'].items():
        assert sha(PACKAGE / p if (PACKAGE / p).is_file() else game / p) == h
    after = {r['path']:r['sha256'] for r in candidate['files']}
    assert {p.relative_to(PACKAGE).as_posix() for p in PACKAGE.rglob('*') if p.is_file()} == set(after)
    files = []
    for r in previous['core_files']:
        p = PACKAGE / r['path']
        plain(p)
        assert sha(p) == after[r['path']]
        files.append({'path':r['path'], 'before':r['sha256'], 'before_bytes':r['bytes'],
                      'after':after[r['path']], 'after_bytes':p.stat().st_size})
    assert len(files) == 51 and {r['path'] for r in files if r['before'] != r['after']} == CHANGES
    for folder in (DEPLOYMENT, HERE/'fixtures', HERE/'recovery'):
        folder.mkdir()
    zipfile = DEPLOYMENT / 'RD2_candidate_01.zip'
    with ZipFile(zipfile, 'x', ZIP_DEFLATED, compresslevel=6) as z:
        for r in files:
            z.write(PACKAGE / r['path'], r['path'])
    with ZipFile(zipfile) as z:
        assert len(z.namelist()) == 51 and set(z.namelist()) == set(after) and z.testzip() is None
        assert all(hashlib.sha256(z.read(r['path'])).hexdigest().upper() == r['after'] for r in files)
    zip_proof = DEPLOYMENT / 'zip_readback.json'
    write(zip_proof, {'status':'PASS','files':51,'sha256':sha(zipfile)})
    proofs = [BASELINE, manifest_path, assessment_path, compiler_path, zip_proof, HERE/'contract.json', HERE/'archive_01/readback.json']
    write(MANIFEST, {
        'schema':SCHEMA, 'component':'Core', 'source_epoch':EPOCH, 'predecessor_epoch':BEFORE,
        'scope':'Three-file candidate for The Gig at the earned Cassius tattoo objective.',
        'game_root':str(game), 'save_root':previous['save_root'], 'package_root':str(PACKAGE),
        'process_names':read(BASE/'core_manifest_01.json')['process_names'],
        'files':files, 'changing_paths':sorted(CHANGES), 'required_files':previous['required_files'],
        'protected_saves':[], 'working_save_files':[], 'zip':str(zipfile), 'zip_sha256':sha(zipfile),
        'proofs':[{'path':str(p),'sha256':sha(p)} for p in proofs],
        'compile_inputs':{str(game/p):h for p,h in compiled['input_pins'].items()}
    })
    template = BASE / 'deploy_core.ps1'
    assert sha(template) == '491B078B11DF4EBAF06BFC30340FF45667D72AFF1A355A45D23CC37C7B48FF7D'
    source = template.read_text(encoding='utf-8-sig')
    wanted = next(line for line in source.splitlines() if line.startswith('$wanted=@('))
    for old, new in (
        ('# Replace exactly the TP3 setup-cover script after installation authorization.',
         '# Replace the three qualified RD2 files after installation authorization.'),
        (sha(BASE/'core_manifest_01.json'), sha(MANIFEST)),
        ('PTFR_TP3_BOUNDED_PRESENTATION_HANDOFF_CORE_V1', SCHEMA),
        ("$manifest.source_epoch -cne 'TP3_BOUNDED_PRESENTATION_HANDOFF'",f"$manifest.source_epoch -cne '{EPOCH}'"),
        ("$manifest.predecessor_epoch -cne 'TP2_RETAINED_PRESENTATION_REPAIR'",f"$manifest.predecessor_epoch -cne '{BEFORE}'"),
        ('recovery/core_presentation_tp3_01','recovery/core_resume_rd2_01'),
        (wanted, '$wanted=@('+','.join("'"+p+"'" for p in sorted(CHANGES))+')'),
        ('$changes.Count -ne 1','$changes.Count -ne 3'),
        ('Core51/one-script TP3 presentation scope drift','Core51/three-file RD2 scope drift')
    ):
        source = once(source, old, new)
    exclusive(INSTALLER, source)
    # Use the previous multi-replacement fixture runner with this baseline and
    # new archive-source pointer. All real commands retain their existing guards.
    runner = ROOT / 'prealpha/tower_presentation_tp2_20261112_01/deploy.py'
    assert sha(runner) == '923C478A62F6D36EB1C3746B5A1D048328B9B681C73B020FC0366707E54C41C9'
    source = runner.read_text(encoding='utf-8')
    for old, new in (
        ('TP2 fixture runner','RD2 fixture runner'),
        ('recovery/core_presentation_tp2_01','recovery/core_resume_rd2_01'),
        ("'compile_03/result.json'","'compile_01/result.json'"),
        ("'archive_source': previous['archive_source']","'archive_source': str(HERE/'archive_01/archive_source')"),
        ("'unchanged_core_paths': 49","'unchanged_core_paths': 48"),
        ("'PENDING_TP2_FRESH_TOWER_ARMS_AND_FAST_TRAVEL_TEST'","'PENDING_THE_GIG_EARNED_REWARD_PLAYTEST'")
    ):
        source = once(source, old, new)
    exclusive(HERE/'deploy.py',source)
    print('Prepared the 51-path local package and three-file transaction.')

if __name__ == '__main__':
    main()
